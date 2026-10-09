import mimetypes

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .forms import DemoRequestForm
from .models import HeroSlide


def terms_of_service_view(request):
    return render(request, 'marketing/terms_of_service.html', {})


def privacy_policy_view(request):
    return render(request, 'marketing/privacy_policy.html', {})


def landing_page_view(request):
    """
    Hii ndiyo view ya path '/' - inabeba kazi mbili kutegemea request.school
    (imewekwa na TenantMiddleware kutoka subdomain):
      - request.school ni None (apex/www, mfano shulepluserp.co.tz) ->
        onyesha LANDING PAGE YA KAMPUNI (marketing).
      - request.school ipo (mfano sehisco.shulepluserp.co.tz) -> onyesha
        BRANDING PAGE YA SHULE HIYO (branding app), siyo marketing.
    """
    if request.school:
        from branding.views import school_home_view
        return school_home_view(request)

    if request.method == 'POST':
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asante! Tutakupigia simu ndani ya masaa 24 kupanga demo.")
            return redirect('marketing:landing_page')
    else:
        form = DemoRequestForm()

    slides_with_images = {
        slide.position: reverse('marketing:hero_image', args=[slide.pk])
        for slide in HeroSlide.objects.exclude(image='')
    }
    context = {
        'form': form,
        'hero_images': [slides_with_images.get(position, '') for position in range(1, 8)],
    }
    return render(request, 'marketing/landing_page.html', context)


def hero_image_view(request, slide_id):
    slide = get_object_or_404(HeroSlide, pk=slide_id)
    if not slide.image:
        raise Http404("Hero image not found.")
    content_type = mimetypes.guess_type(slide.image.name)[0] or 'application/octet-stream'
    return FileResponse(slide.image.open('rb'), content_type=content_type)
