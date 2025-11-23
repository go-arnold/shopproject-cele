from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profiles'
    fk_name = 'user'
    readonly_fields = ('image_preview',)

    def image_preview(self, instance):
        if instance and instance.image:
            return mark_safe(f'<img src="{instance.image.url}" style="max-height:120px;"/>')
        return '(Pas d\'image)'
    image_preview.short_description = 'Photo de profil'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height:50px;"/>')
        return '(Pas d\'image)'
    image_preview.short_description = 'Photo'


# Remplacer l'admin User pour inclure l'inline Profile
try:
    admin.site.unregister(User)
except Exception:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        # n'afficher l'inline que si on édite un utilisateur existant
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


admin.site.register(Profile, ProfileAdmin)
