from django.db import models

# Create your models here.
class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    testimony = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.role}'
