from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Testimonial
import json

# Create your views here.
def Index(request):
    return render(request, 'app/index.html')


def submit_testimonial(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        role = request.POST.get('role')
        testimony = request.POST.get('testimony')
        image = request.FILES.get('image')

        testimonial = Testimonial.objects.create(name=name, role=role, testimony=testimony)
        if image:
            testimonial.image = image
        testimonial.save()
        messages.success(request, 'Testmonial submitted successfully!')
        return redirect('/')


def send_contact_email(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        # Validate required fields
        if not all([name, email, subject, message]):
            messages.error(request, 'All fields are required')
            return redirect('/')

        email_subject = f"Kim Technologies Contact: {subject}"
        email_message = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message: {message}
        """

        send_mail(
            email_subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )

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

        send_mail(
            user_subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.success(request, 'Message sent successfully! We will get back to you soon.')
        return redirect('/')

    else:
        messages.error(request, 'Method not allowed')
        return redirect('/')