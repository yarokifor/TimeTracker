from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Shift, Event

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Register your models here.
admin.site.register(Profile)
admin.site.register(Shift)
admin.site.register(Event)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
