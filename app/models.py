
from django.db import models
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


import secrets

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_chat_code():
    return "KT-" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


class ChatSession(models.Model):
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    chat_code = models.CharField(          # NEW
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visitor_name = models.CharField(max_length=120, blank=True)
    visitor_email = models.EmailField(blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):       # NEW
        if not self.chat_code:
            for _ in range(10):
                code = generate_chat_code()
                if not ChatSession.objects.filter(chat_code=code).exists():
                    self.chat_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat {self.chat_code or self.public_id}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(
        ChatSession,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role} message in {self.session_id}"


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        AWAITING_CUSTOMER = "awaiting_customer", "Awaiting Customer"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    reference = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True,
    )
    session = models.ForeignKey(
        ChatSession,
        related_name="tickets",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    subject = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(
        max_length=80,
        default="General support",
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kim_support_tickets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    customer_ack_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = (
                f"KIM-{timezone.now():%y%m%d}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.subject}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        related_name="replies",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_internal_note = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply on {self.ticket.reference}"


class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    testimony = models.TextField()
    rating = models.PositiveIntegerField(default=0)
    image = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        null=True
    )
    is_published = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.name} - {self.role}"


class Subscribe(models.Model):
    email = models.EmailField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]
        verbose_name = "Email Subscriber"
        verbose_name_plural = "Email Subscribers"

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    other_service = models.CharField(
        max_length=255,
        blank=True
    )
    preferred_date = models.DateField(
        blank=True,
        null=True
    )
    preferred_time = models.TimeField(
        blank=True,
        null=True
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Partner(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(
        upload_to="partners/",
        blank=True,
        null=True
    )
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Partner"
        verbose_name_plural = "Partners"

    def __str__(self):
        return self.name
