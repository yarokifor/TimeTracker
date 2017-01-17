from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Shift, Event

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'time')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'start_time', 'end_time')
    def start_time(self, obj):
        return obj.start.time if obj.start != None else None
    start_time.short_description = 'Start'

    def end_time(self, obj):
        return obj.end.time if obj.end != None else None
    end_time.short_description = 'End'
        
        

# Register your models here.
admin.site.register(Profile)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
