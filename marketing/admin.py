from django.contrib import admin
from .models import DemoRequest, HeroSlide


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('position', 'image')
    fields = ('position', 'image')


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'contact_name', 'phone', 'is_contacted', 'created_at')
    list_filter = ('is_contacted', 'created_at')
    search_fields = ('school_name', 'contact_name', 'phone', 'email')