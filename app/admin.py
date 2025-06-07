from django.contrib import admin
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'is_published', 'date_created')
    list_filter = ('is_published', 'date_created')
    search_fields = ('name', 'role', 'testimony')
    ordering = ('-date_created',)
    list_editable = ('is_published',)
    readonly_fields = ('date_created',)

    fieldsets = (
        ('Client Info', {
            'fields': ('name', 'role', 'image', 'organization', 'rating'),
        }),
        ('Testimony Details', {
            'fields': ('testimony', 'is_published'),
        }),
        ('System Info', {
            'fields': ('date_created',),
        }),
    )
