from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

def upload_to_profile(instance, filename):
    extension = filename.split('.')[-1]
    return f"profile_pictures/{instance.email.replace('@', '_').replace(".", "_")}.{extension}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('patron', 'Patron'),
        ('librarian', 'Librarian'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patron')

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def default_profile_picture():
        return "toolhub/images/default.png"
    
    profile_picture = models.ImageField(
        upload_to=upload_to_profile,
        default= default_profile_picture,
        storage=settings.DEFAULT_FILE_STORAGE,
        null= True, 
        blank= True
        )
    
    # Deletes old profile picture before saving a new one.
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                if old_instance.profile_picture and old_instance.profile_picture.name != self.profile_picture.name:
                    if hasattr(old_instance.profile_picture, 'delete'):
                        old_instance.profile_picture.delete(save=False)
            except CustomUser.DoesNotExist:
                pass  # First-time save, no old image exists
        super().save(*args, **kwargs)
    
    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{self.profile_picture.name}"
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/profile_pictures/default.png"

class Item(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images/', blank=True, null=True)