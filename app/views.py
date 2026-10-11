
import threading

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_POST

from .models import Testimonial, Subscribe, ContactMessage, Partner


# ==========================================
# EMAIL HELPER
# ==========================================

def send_email_background(subject, body, recipient_list, cc_list=None):
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            cc=cc_list or [],
        )
        email.send(fail_silently=False)
        print(f"Email sent successfully: {subject}")

    except Exception as error:
        print(f"Email sending error: {error}")


def start_email_thread(subject, body, recipients, cc=None):
    thread = threading.Thread(
        target=send_email_background,
        args=(subject, body, recipients, cc),
        daemon=True,
    )
    thread.start()


# ==========================================
# HOMEPAGE
# ==========================================

def Index(request):
    testimonials = Testimonial.objects.filter(is_published=True)
    partners = Partner.objects.filter(is_active=True)

    context = {
        "testmonials": testimonials,  # Preserves your existing template variable
        "testimonials": testimonials,
        "partners": partners,
    }

    return render(request, "app/index.html", context)


# ==========================================
# SUBMIT TESTIMONIAL
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
        messages.error(request, "Please complete all required testimonial fields.")
        return redirect("/#testimonials")

    if rating < 1 or rating > 5:
        messages.error(request, "Please select a rating between 1 and 5.")
        return redirect("/#testimonials")

    testimonial = Testimonial(
        name=name,
        role=role,
        organization=organization,
        testimony=testimony,
        rating=rating,
        image=image,
        is_published=False,
    )
    testimonial.save()

    messages.success(
        request,
        "Thank you! Your testimonial has been submitted for review."
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

    # Basic validation
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

    # Date and time are optional. Validate them if supplied.
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

    # Save the contact enquiry to the database first.
    contact = ContactMessage.objects.create(
        name=name,
        email=customer_email,
        subject=subject,
        other_service=other_service if subject.lower() == "other" else "",
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        message=message_text,
    )

    date_display = preferred_date.strftime("%d %B %Y") if preferred_date else "Not specified"
    time_display = preferred_time.strftime("%I:%M %p") if preferred_time else "Not specified"

    # Notify Kim Technologies.
    admin_subject = f"Kim Technologies Contact: {service_name}"

    admin_message = f"""
New Contact Form Submission
===========================

Reference: #{contact.pk}
Name: {name}
Email: {customer_email}
Service: {service_name}

Preferred Date: {date_display}
Preferred Time: {time_display}

Message:
{message_text}

===========================
Kim Technologies Group
https://www.kimtechnologiesgroup.org/
"""

    # Send an acknowledgement to the customer.
    customer_subject = "Thank you for contacting Kim Technologies"

    customer_message = f"""
Dear {name},

Thank you for contacting Kim Technologies.

We have received your message and will get back to you as soon as possible.

Your submission details:

Reference: #{contact.pk}
Service: {service_name}
Preferred Date: {date_display}
Preferred Time: {time_display}

Message:
{message_text}

Best regards,
Kim Technologies Team
https://www.kimtechnologiesgroup.org/
"""

    # Send emails in background so the form does not wait for SMTP.
    start_email_thread(
        admin_subject,
        admin_message,
        [settings.DEFAULT_FROM_EMAIL],
        ["ruth@kimtechnologiesgroup.org"],
    )

    start_email_thread(
        customer_subject,
        customer_message,
        [customer_email],
    )

    messages.success(
        request,
        "Your message has been saved and submitted successfully. We will get back to you soon."
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
        messages.success(
            request,
            "Thank you for subscribing to the Kim Technologies newsletter!"
        )
    elif not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active"])
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
