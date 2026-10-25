
import threading

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
import json
import logging
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import (
    csrf_protect,
    ensure_csrf_cookie,
)
from django.views.decorators.http import require_GET, require_POST

from .models import ChatSession, ChatMessage, SupportTicket
from .services import ask_ai, send_ticket_emails

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000

from .models import Testimonial, Subscribe, ContactMessage, Partner


# ==========================================
# EMAIL HELPERS
# ==========================================

def send_email_background(subject, text_body, html_body, recipients, cc=None):
    """
    Send multipart HTML and plain-text email.
    This function runs in a background thread.
    """
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            cc=cc or [],
        )

        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

        print(f"Email sent successfully: {subject}")

    except Exception as error:
        print(f"Email sending error for '{subject}': {error}")


def queue_email(subject, template_name, context, recipients, cc=None):
    """
    Render email templates and queue the email for sending.
    Rendering occurs before starting the thread so template errors
    can be caught during the request.
    """
    try:
        html_body = render_to_string(template_name, context)

        # Build a basic text alternative from the rendered HTML.
        import re
        from html import unescape

        text_body = re.sub(r"<[^>]+>", " ", html_body)
        text_body = unescape(text_body)
        text_body = re.sub(r"\s+", " ", text_body).strip()

        thread = threading.Thread(
            target=send_email_background,
            args=(
                subject,
                text_body,
                html_body,
                recipients,
                cc,
            ),
            daemon=True,
        )
        thread.start()
        return True

    except Exception as error:
        print(f"Email preparation error for '{subject}': {error}")
        return False


def get_date_time_display(contact):
    date_display = (
        contact.preferred_date.strftime("%d %B %Y")
        if contact.preferred_date
        else "Not specified"
    )

    time_display = (
        contact.preferred_time.strftime("%I:%M %p")
        if contact.preferred_time
        else "Not specified"
    )

    return date_display, time_display


# ==========================================
# HOMEPAGE
# ==========================================

def Index(request):
    testimonials = Testimonial.objects.filter(is_published=True)
    partners = Partner.objects.filter(is_active=True)

    context = {
        "testmonials": testimonials,
        "testimonials": testimonials,
        "partners": partners,
    }

    return render(request, "app/index.html", context)


# ==========================================
# TESTIMONIAL SUBMISSION
# ==========================================

@require_POST
def submit_testimonial(request):
    name = request.POST.get("name", "").strip()
    role = request.POST.get("role", "").strip()
    organization = request.POST.get("organization", "").strip()
    testimony = request.POST.get("testimony", "").strip()
    image = request.FILES.get("image")

    try:
        rating = int(request.POST.get("rating", "0"))
    except (TypeError, ValueError):
        rating = 0

    if not all([name, role, organization, testimony]):
        messages.error(
            request,
            "Please complete all required testimonial fields."
        )
        return redirect("/#testimonials")

    if rating < 1 or rating > 5:
        messages.error(
            request,
            "Please select a rating between 1 and 5."
        )
        return redirect("/#testimonials")

    testimonial = Testimonial.objects.create(
        name=name,
        role=role,
        organization=organization,
        testimony=testimony,
        rating=rating,
        image=image,
        is_published=False,
    )

    email_sent_to_queue = queue_email(
        subject="New Testimonial Submitted for Review",
        template_name="app/emails/testimonial_notification.html",
        context={"testimonial": testimonial},
        recipients=[settings.DEFAULT_FROM_EMAIL],
        cc=[
            "ruth@kimtechnologiesgroup.org",
        ],
    )

    messages.success(
        request,
        "Thank you! Your testimonial has been submitted for review."
    )

    if not email_sent_to_queue:
        print(
            f"Testimonial #{testimonial.pk} saved, "
            "but its notification could not be prepared."
        )

    return redirect("/#testimonials")


# ==========================================
# CONTACT FORM
# ==========================================

@require_POST
def send_contact_email(request):
    name = request.POST.get("name", "").strip()
    customer_email = request.POST.get("email", "").strip().lower()
    subject = request.POST.get("subject", "").strip()
    other_service = request.POST.get("other_service", "").strip()
    preferred_date_raw = request.POST.get("preferred_date", "").strip()
    preferred_time_raw = request.POST.get("preferred_time", "").strip()
    message_text = request.POST.get("message", "").strip()

    if not all([name, customer_email, subject, message_text]):
        messages.error(
            request,
            "Please provide your name, email, service, and message."
        )
        return redirect("/#contact")

    try:
        validate_email(customer_email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return redirect("/#contact")

    if subject.lower() == "other":
        if not other_service:
            messages.error(
                request,
                "Please specify the service you are enquiring about."
            )
            return redirect("/#contact")

        service_name = f"Other: {other_service}"
    else:
        service_name = subject

    preferred_date = None
    preferred_time = None

    if preferred_date_raw:
        preferred_date = parse_date(preferred_date_raw)
        if preferred_date is None:
            messages.error(request, "Please enter a valid preferred date.")
            return redirect("/#contact")

    if preferred_time_raw:
        preferred_time = parse_time(preferred_time_raw)
        if preferred_time is None:
            messages.error(request, "Please enter a valid preferred time.")
            return redirect("/#contact")

    # Save the enquiry before attempting email delivery.
    contact = ContactMessage.objects.create(
        name=name,
        email=customer_email,
        subject=subject,
        other_service=other_service if subject.lower() == "other" else "",
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        message=message_text,
    )

    date_display, time_display = get_date_time_display(contact)

    email_context = {
        "contact": contact,
        "service_name": service_name,
        "preferred_date_display": date_display,
        "preferred_time_display": time_display,
    }

    admin_email_queued = queue_email(
        subject=f"New Website Inquiry #{contact.pk}: {service_name}",
        template_name="app/emails/contact_notification.html",
        context=email_context,
        recipients=[settings.DEFAULT_FROM_EMAIL],
        cc=[
            "ruth@kimtechnologiesgroup.org",
        ],
    )

    customer_email_queued = queue_email(
        subject=f"We've Received Your Inquiry - Reference #{contact.pk}",
        template_name="app/emails/contact_acknowledgement.html",
        context=email_context,
        recipients=[customer_email],
    )

    if admin_email_queued and customer_email_queued:
        messages.success(
            request,
            "Your message has been saved and submitted successfully. "
            "We will get back to you soon."
        )
    else:
        # The contact record has already been saved.
        messages.success(
            request,
            "Your message has been received and saved. "
            "Our team will follow up as soon as possible."
        )

    return redirect("/#contact")


# ==========================================
# NEWSLETTER SUBSCRIPTION
# ==========================================

@require_POST
def SubScribe(request):
    email = request.POST.get("email", "").strip().lower()

    if not email:
        messages.error(request, "Please enter your email address.")
        return redirect("/#newsletter")

    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return redirect("/#newsletter")

    subscriber, created = Subscribe.objects.get_or_create(
        email=email,
        defaults={"is_active": True},
    )

    if created:
        queue_email(
            subject="Welcome to Kim Technologies Updates",
            template_name="app/emails/newsletter_welcome.html",
            context={"subscriber": subscriber},
            recipients=[subscriber.email],
        )

        messages.success(
            request,
            "Thank you for subscribing to our newsletter!"
        )

    elif not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active"])

        queue_email(
            subject="Welcome Back to Kim Technologies Updates",
            template_name="app/emails/newsletter_welcome.html",
            context={"subscriber": subscriber},
            recipients=[subscriber.email],
        )

        messages.success(
            request,
            "Your newsletter subscription has been reactivated."
        )

    else:
        messages.info(
            request,
            "This email address is already subscribed to our newsletter."
        )

    return redirect("/#newsletter")


import json
import logging
import re
import uuid
from pathlib import Path

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import validate_email
from django.http import JsonResponse
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ChatSession, ChatMessage, SupportTicket
from .services import (
    CODE_REDIRECT,
    CONSENT_QUESTION,
    ask_ai,
    send_ticket_emails,
    summarize_support_conversation,
)

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx",
}


# ---------- helpers ----------

def _json_body(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _request_data(request):
    """Accept either JSON or multipart/form-data."""
    if request.content_type and request.content_type.startswith(
        "multipart/form-data"
    ):
        return request.POST
    return _json_body(request)


def _clean(value, limit=MAX_MESSAGE_LENGTH):
    return strip_tags(str(value or "")).strip()[:limit]


_CODE_PATTERN = re.compile(
    r"```|<!doctype|<html|<script|<\?php|^\s*(def |class |import |function |const |SELECT )",
    re.IGNORECASE | re.MULTILINE,
)


def _contains_code(text):
    """True if an AI reply looks like it contains source code."""
    return bool(_CODE_PATTERN.search(text or ""))


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _throttled(request, scope, limit, window=300):
    """Simple per-IP rate limit (uses Django's cache)."""
    key = f"kim-chat:{scope}:{_client_ip(request)}"
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        count = 1
    return count > limit


def _get_session(raw_id):
    """Return a ChatSession for a public_id, or None (never raises)."""
    raw_id = str(raw_id or "").strip()
    if not raw_id:
        return None
    try:
        return ChatSession.objects.get(public_id=raw_id)
    except (ChatSession.DoesNotExist, ValueError, ValidationError):
        return None


def _normalize_code(raw):
    code = re.sub(r"[^A-Za-z0-9]", "", str(raw or "")).upper()
    if code.startswith("KT"):
        code = code[2:]
    return f"KT-{code}" if code else ""


def _session_payload(session, **extra):
    if not session.chat_code:
        session.save()  # ChatSession.save() generates the chat code
    return {
        "session_id": str(session.public_id),
        "chat_code": session.chat_code,
        **extra,
    }


# ---------- views ----------

@require_GET
@ensure_csrf_cookie
def health(request):
    return JsonResponse({"ok": True, "service": "kim-support"})


@require_POST
@csrf_protect
def chat_start(request):
    data = _request_data(request)

    session = _get_session(data.get("session_id"))
    if session and not session.is_closed:
        return JsonResponse(_session_payload(session, created=False))

    if _throttled(request, "start", 20):
        return JsonResponse(
            {"error": "Too many requests. Please wait a moment."},
            status=429,
        )

    session = ChatSession.objects.create()
    return JsonResponse(_session_payload(session, created=True))


@require_POST
@csrf_protect
def chat_resume(request):
    """Reopen a previous chat using its customer-facing chat ID."""
    if _throttled(request, "resume", 10):
        return JsonResponse(
            {"error": "Too many attempts. Please try again in a few minutes."},
            status=429,
        )

    data = _request_data(request)

    # Accept the internal session_id (auto-restore) or a typed chat ID.
    session = _get_session(data.get("session_id"))
    if not session:
        code = _normalize_code(data.get("chat_code"))
        if not code:
            return JsonResponse(
                {"error": "Enter your chat ID, e.g. KT-7F3K9QXA."},
                status=400,
            )
        session = ChatSession.objects.filter(chat_code=code).first()

    if not session:
        return JsonResponse(
            {"error": "We couldn't find that chat ID. Check it and try again."},
            status=404,
        )

    history = (
        session.messages
        .filter(role__in=[ChatMessage.Role.USER, ChatMessage.Role.ASSISTANT])
        .order_by("-created_at")[:100]
    )
    messages = [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(list(history))
    ]

    return JsonResponse(
        _session_payload(session, closed=session.is_closed, messages=messages)
    )


@require_POST
@csrf_protect
def chat_message(request):
    if _throttled(request, "message", 40):
        return JsonResponse(
            {"error": "You're sending messages too fast. Please wait a moment."},
            status=429,
        )

    data = _request_data(request)

    message = _clean(data.get("message"))
    uploaded_file = request.FILES.get("file")

    if not message and not uploaded_file:
        return JsonResponse(
            {"error": "Type a message or attach a file."},
            status=400,
        )

    session = _get_session(data.get("session_id"))
    if not session:
        return JsonResponse(
            {"error": "Chat not found. Please start a new chat."},
            status=404,
        )

    if session.is_closed:
        return JsonResponse(
            {"error": "This chat is closed. Start a new chat to continue."},
            status=400,
        )

    attachment_note = ""

    if uploaded_file:
        suffix = Path(uploaded_file.name).suffix.lower()

        if suffix not in ALLOWED_EXTENSIONS:
            return JsonResponse(
                {"error": "This file type is not supported."},
                status=400,
            )

        if uploaded_file.size > MAX_UPLOAD_SIZE:
            return JsonResponse(
                {"error": "Attachments must be 5 MB or smaller."},
                status=400,
            )

        # Configure default_storage as PRIVATE for customer attachments.
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        storage_path = default_storage.save(
            f"support-chat-uploads/{safe_name}",
            uploaded_file,
        )

        attachment_note = (
            f"[Attachment uploaded: {Path(uploaded_file.name).name}; "
            f"stored as {storage_path}]"
        )

    saved_message = message
    if attachment_note:
        saved_message = (
            f"{message}\n\n{attachment_note}".strip()
            if message else attachment_note
        )

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=saved_message,
    )

    try:
        # The AI sees the text and attachment filename only, not file contents.
        answer = ask_ai(session, saved_message)
    except Exception:
        logger.exception("AI chat request failed")
        answer = (
            "[ESCALATE]\n"
            "I'm having trouble answering right now. "
            f"{CONSENT_QUESTION}"
        )

    # The chat shows plain text, so remove markdown bold/underline marks.
    answer = re.sub(r"\*\*|__", "", answer)

    # Safety net: the assistant must never send code to customers.
    if _contains_code(answer):
        answer = f"[ESCALATE]\n{CODE_REDIRECT}"

    escalate = answer.lstrip().startswith("[ESCALATE]")

    if escalate:
        answer = re.sub(r"^\s*\[ESCALATE\]\s*", "", answer).strip()
        if not answer:
            answer = CONSENT_QUESTION

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=answer,
    )

    return JsonResponse(_session_payload(session, answer=answer, escalate=escalate))


@require_POST
@csrf_protect
def create_ticket(request):
    data = _request_data(request)

    email = _clean(data.get("email"), 254)

    if not email:
        return JsonResponse(
            {"error": "Enter your email address so our team can reply."},
            status=400,
        )

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {"error": "Enter a valid email address."},
            status=400,
        )

    session = _get_session(data.get("session_id"))
    if not session:
        return JsonResponse(
            {"error": "Your chat could not be found. Please start a new chat."},
            status=404,
        )

    # Build the ticket from the saved conversation, not client-supplied fields.
    subject, description = summarize_support_conversation(session)

    ticket = SupportTicket.objects.create(
        session=session,
        customer_name=session.visitor_name or "Website visitor",
        customer_email=email,
        subject=subject[:180],
        description=description[:20000],
        category="Website AI support",
        priority=SupportTicket.Priority.NORMAL,
    )

    session.visitor_email = email
    session.save(update_fields=["visitor_email", "updated_at"])

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.SYSTEM,
        content=f"Support ticket {ticket.reference} created.",
    )

    send_ticket_emails(ticket)

    return JsonResponse({
        "success": True,
        "ticket_reference": ticket.reference,
        "chat_code": session.chat_code,
        "message": (
            f"Done. Ticket {ticket.reference} sent. "
            "Our team will reply to your email."
        ),
    }, status=201)


@require_GET
def ticket_status(request, reference):
    return JsonResponse({
        "error": (
            "Public ticket lookup is not enabled. "
            "Reply to your ticket email for updates."
        )
    }, status=404)