from django.urls import path
from . import views
from app.sitemap import StaticSitemap
from django.views.generic.base import TemplateView
from django.contrib.sitemaps.views import sitemap

sitemaps = {
    'static': StaticSitemap,
}


urlpatterns = [
    path('', views.Index, name='index'),
    path('sitemap.xml', sitemap, {'sitemaps':sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="app/robots.txt", content_type="text/plain")),
    path('send-contact-email/', views.send_contact_email, name='send_contact_email'),
    path('submit_testimonial/', views.submit_testimonial, name='submit_testimonial'),
    path('subscribe/', views.SubScribe, name='subscribe'),
]