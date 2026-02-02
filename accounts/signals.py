from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from utils.code_four import generer_code


@receiver(post_save, sender=User)
def update_profile_on_user_save(sender, instance, created, **kwargs):
    if not instance.groups.filter(name="revendeur").exists():
        return
    try:
        profile = instance.profile
    except Profile.DoesNotExist:
        return
    if profile.code_revendeur == "0000":
        profile.code_revendeur = generer_code()
        profile.save(update_fields=["code_revendeur"])


@receiver(m2m_changed, sender=User.groups.through)
def user_added_to_group(sender, instance, action, pk_set, **kwargs):
    if action != "post_add":
        return
    if not instance.groups.filter(name="revendeur").exists():
        return
    try:
        profile = instance.profile
    except Profile.DoesNotExist:
        return
    if profile.code_revendeur == "0000":
        profile.code_revendeur = generer_code()
        profile.save(update_fields=["code_revendeur"])
