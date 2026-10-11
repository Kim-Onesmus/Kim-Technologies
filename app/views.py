
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
            # "ruth@kimtechnologiesgroup.org",
            "onesmus@kimtechnologiesgroup.org",
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
            # "ruth@kimtechnologiesgroup.org",
            "onesmus@kimtechnologiesgroup.org",
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
