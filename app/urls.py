from django.urls import path
from . import views
from app.sitemap import StaticSitemap
from django.views.generic.base import TemplateView
from django.contrib.sitemaps.views import sitemap

app_name = "app"

sitemaps = {
    'static': StaticSitemap,
}


urlpatterns = [
    path('', views.Index, name='index'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="app/robots.txt", content_type="text/plain")),
    path("submit-testimonial/", views.submit_testimonial, name="submit_testimonial"),
    path("send-contact-email/", views.send_contact_email, name="send_contact_email"),
    path("subscribe/", views.SubScribe, name="subscribe"),

    path("health/", views.health, name="health"),
    path("chat/start/", views.chat_start, name="chat_start"),
    path("chat/resume/", views.chat_resume, name="chat_resume"),   # NEW
    path("chat/message/", views.chat_message, name="chat_message"),
    path("tickets/create/", views.create_ticket, name="create_ticket"),
    path("tickets/<str:reference>/", views.ticket_status, name="ticket_status"),
]