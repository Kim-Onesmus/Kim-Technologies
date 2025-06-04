from django.urls import path
from . import views


urlpatterns = [
    path('', views.Index, name='index'),
    path('send-contact-email/', views.send_contact_email, name='send_contact_email'),
]