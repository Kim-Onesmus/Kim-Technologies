from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Testimonial, Subscribe
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


def send_email_background(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )


def send_contact_email(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not all([name, email, subject, message]):
            messages.error(request, 'All fields are required')
            return redirect('/')

        # Admin notification
        admin_subject = f"Kim Technologies Contact: {subject}"
        admin_message = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
        Message: {message}
        """

        # User acknowledgment
        user_subject = "Thank you for contacting Kim Technologies"
        user_message = f"""
        Dear {name},

        Thank you for contacting Kim Technologies. We have received your message and will get back to you as soon as possible.

        Your message details:
        Subject: {subject}
        Message: {message}

        Best regards,
        Kim Technologies Team
        """

        # Send emails in background threads
        threading.Thread(target=send_email_background, args=(admin_subject, admin_message, [settings.DEFAULT_FROM_EMAIL])).start()
        threading.Thread(target=send_email_background, args=(user_subject, user_message, [email])).start()

        messages.success(request, 'Message sent successfully! We will get back to you soon.')
        return redirect('/')

    else:
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
