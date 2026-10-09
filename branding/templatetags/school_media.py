from django import template
from django.urls import reverse

from shule_core.models import School
from branding.models import (
    Facility,
    LeadershipMember,
    PostImage,
    SchoolProfile,
    Testimonial,
    BrandingPost,
)

register = template.Library()

ASSET_KINDS = {
    (School, 'logo'): 'school-logo',
    (SchoolProfile, 'cover_image'): 'profile-cover',
    (BrandingPost, 'image'): 'post-image',
    (PostImage, 'image'): 'gallery-image',
    (LeadershipMember, 'photo'): 'leadership-photo',
    (Facility, 'image'): 'facility-image',
    (Testimonial, 'photo'): 'testimonial-photo',
}


@register.simple_tag
def school_media_url(instance, field_name):
    kind = ASSET_KINDS.get((type(instance), field_name))
    if not kind or not getattr(instance, field_name):
        return ''

    school = instance if isinstance(instance, School) else (
        instance.post.school if isinstance(instance, PostImage) else instance.school
    )
    return reverse(
        'branding:school_asset',
        kwargs={
            'subdomain': school.subdomain,
            'kind': kind,
            'object_id': instance.pk,
        },
    )
