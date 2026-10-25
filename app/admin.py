
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


from django.contrib import admin

from .models import (
    ChatSession,
    ChatMessage,
    SupportTicket,
    TicketReply,
)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = (
        "role",
        "content",
        "created_at",
    )
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "visitor_name",
        "visitor_email",
        "created_at",
        "updated_at",
        "is_closed",
    )
    search_fields = (
        "public_id",
        "visitor_name",
        "visitor_email",
        "messages__content",
    )
    list_filter = ("is_closed", "created_at")
    inlines = [ChatMessageInline]
    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "subject",
        "customer_name",
        "customer_email",
        "priority",
        "status",
        "assigned_to",
        "created_at",
    )
    search_fields = (
        "reference",
        "subject",
        "customer_name",
        "customer_email",
        "description",
    )
    list_filter = (
        "status",
        "priority",
        "category",
        "created_at",
    )
    list_editable = (
        "status",
        "priority",
        "assigned_to",
    )
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "notification_sent_at",
        "customer_ack_sent_at",
    )
    inlines = [TicketReplyInline]


@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "author",
        "is_internal_note",
        "created_at",
    )
    search_fields = (
        "ticket__reference",
        "message",
    )
    list_filter = (
        "is_internal_note",
        "created_at",
    )