from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import DemoRequest, HeroSlide


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'slide_label', 'is_uploaded')
    fields = ('position', 'image', 'image_preview')
    readonly_fields = ('image_preview',)

    @admin.display(description='Picha')
    def thumbnail(self, obj):
        if not obj.has_image:
            return '—'
        return format_html(
            '<img src="{}" width="128" height="72" alt="" '
            'style="object-fit:cover;border-radius:8px;display:block">',
            reverse('marketing:hero_image', args=[obj.pk]),
        )

    @admin.display(description='Slaidi kwenye ukurasa wa mwanzo')
    def slide_label(self, obj):
        return obj.get_position_display()

    @admin.display(description='Imepakwa', boolean=True)
    def is_uploaded(self, obj):
        return obj.has_image

    @admin.display(description='Muonekano wa slaidi hii')
    def image_preview(self, obj):
        if not obj.pk or not obj.has_image:
            return format_html(
                '<p style="margin:0;color:#666">Hakuna picha bado. Slaidi hii itaonyesha '
                'mchoro wa kipengele hadi upakishe picha ya shule.</p>'
            )
        return format_html(
            '<img src="{}" alt="" style="max-width:560px;width:100%;border-radius:12px;display:block">'
            '<p style="margin:8px 0 0;color:#666">Hivi ndivyo picha inavyoonekana kwenye slaidi {}.</p>',
            reverse('marketing:hero_image', args=[obj.pk]),
            obj.get_position_display(),
        )


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'contact_name', 'phone', 'is_contacted', 'created_at')
    list_filter = ('is_contacted', 'created_at')
    search_fields = ('school_name', 'contact_name', 'phone', 'email')
