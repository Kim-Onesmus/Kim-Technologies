
from django.contrib import admin
from .models import Testimonial, Subscribe, ContactMessage, Partner


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "role",
        "rating",
        "is_published",
        "date_created",
    )
    list_filter = ("is_published", "rating", "date_created")
    search_fields = ("name", "organization", "role", "testimony")
    list_editable = ("is_published",)
    readonly_fields = ("date_created",)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "date_created")
    list_filter = ("is_active", "date_created")
    search_fields = ("email",)
    list_editable = ("is_active",)
    readonly_fields = ("date_created",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "subject",
        "status",
        "date_created",
    )
    list_filter = ("status", "date_created")
    search_fields = ("name", "email", "subject", "message")
    list_editable = ("status",)
    readonly_fields = ("date_created",)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "website",
        "is_active",
        "display_order",
        "date_created",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    list_editable = ("is_active", "display_order")
    readonly_fields = ("date_created",)
