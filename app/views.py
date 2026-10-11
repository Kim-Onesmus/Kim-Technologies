from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Testimonial, Subscribe
from django.core.mail import EmailMessage
import threading
import json

# Create your views here.
def Index(request):
    testmonials = Testimonial.objects.filter(is_published=True)

    context = {
        'testmonials':testmonials
    }
    return render(request, 'app/index.html', context)


def submit_testimonial(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        role = request.POST.get('role')
        organization = request.POST.get('organization')
        testimony = request.POST.get('testimony')
        rating = request.POST.get('rating')
        image = request.FILES.get('image')

        testimonial = Testimonial.objects.create(
            name=name,
            organization=organization,
            role=role,
            testimony=testimony,
            rating=rating
        )
        if image:
            testimonial.image = image
        testimonial.save()
        messages.success(request, 'Testmonial submitted successfully!')
        return redirect('/')
    else:
        messages.error(request, 'An error occured, please try again!')
        return redirect('/')




def send_email_background(subject, message, recipient_list, cc_list=None):
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            cc=cc_list or [],
        )

        email.send(fail_silently=False)

        print(f"Email sent successfully: {subject}")

    except Exception as e:
        print(f"Email sending error: {e}")


def send_contact_email(request):
    if request.method == 'POST':

        # Get fields directly from the frontend
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        other_service = request.POST.get('other_service', '').strip()
        preferred_date = request.POST.get('preferred_date', '').strip()
        preferred_time = request.POST.get('preferred_time', '').strip()
        message = request.POST.get('message', '').strip()

        # If user selected "Other"
        if subject == 'Other' and other_service:
            subject = f"Other: {other_service}"

        # Validate frontend fields
        if not all([
            name,
            email,
            subject,
            preferred_date,
            preferred_time,
            message
        ]):
            messages.error(request, 'All fields are required')
            return redirect('/')

        # ==========================================
        # ADMIN EMAIL
        # ==========================================

        admin_subject = f"Kim Technologies Contact: {subject}"

        admin_message = f"""
New Contact Form Submission
===========================

Name: {name}
Email: {email}
Service: {subject}

Preferred Date: {preferred_date}
Preferred Time: {preferred_time}

Message:
{message}

===========================
Kim Technologies Group
https://www.kimtechnologiesgroup.org/
"""

        # ==========================================
        # CUSTOMER EMAIL
        # ==========================================

        user_subject = "Thank you for contacting Kim Technologies"

        user_message = f"""
Dear {name},

Thank you for contacting Kim Technologies.

We have received your message and will get back to you as soon as possible.

Your submission details:

Service: {subject}
Preferred Date: {preferred_date}
Preferred Time: {preferred_time}

Message:
{message}

Best regards,

Kim Technologies Team
https://www.kimtechnologiesgroup.org/
"""

        # ==========================================
        # SEND ADMIN EMAIL
        # To: DEFAULT_FROM_EMAIL
        # CC: Ruth
        # ==========================================

        threading.Thread(
            target=send_email_background,
            args=(
                admin_subject,
                admin_message,
                [settings.DEFAULT_FROM_EMAIL],
                ['ruth@kimtechnologiesgroup.org'],
            )
        ).start()

        # ==========================================
        # SEND CUSTOMER ACKNOWLEDGEMENT
        # ==========================================

        threading.Thread(
            target=send_email_background,
            args=(
                user_subject,
                user_message,
                [email],
            )
        ).start()

        messages.success(
            request,
            'Message sent successfully! We will get back to you soon.'
        )

        return redirect('/')

    messages.error(request, 'Method not allowed')
    return redirect('/')

    

def SubScribe(request):
    if request.method == 'POST':
        email = request.POST['email']

        if Subscribe.objects.filter(email=email).exists():
            messages.error(request, 'You already subscribed to Kim Technologies news letter')
            return redirect('/')
        else:
            sub_info = Subscribe.objects.create(
                email=email
            )
            sub_info.save()
            messages.success(request, 'Thank you for subscribing to our news letter')
            return redirect('/')
    else:
        messages.error(request, 'An error occured while subscribing to our news letter')
        return redirect('/')
