from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


admin.site.unregister(get_user_model())


@admin.register(get_user_model())
class UserWithProfileAdmin(UserAdmin):
    inlines = [ProfileInline]
