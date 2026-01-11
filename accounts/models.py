from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )
    def_address = models.CharField(
        max_length=60, null=True, blank=True,)
    def_country = models.CharField(
        max_length=60, null=True, blank=True,)
    def_quarter_town = models.CharField(
        max_length=60, null=True, blank=True,)

    deliv_address = models.CharField(
        max_length=60, null=True, blank=True,)
    deliv_country = models.CharField(
        max_length=60, null=True, blank=True,)
    deliv_quarter_town = models.CharField(
        max_length=60, null=True, blank=True,)
    image = models.ImageField(
        upload_to='profile_pics/', default='produits/avatar_kbwhgu.png')

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
