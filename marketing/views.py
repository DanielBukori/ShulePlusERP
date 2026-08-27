from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import DemoRequestForm


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

    context = {'form': form}
    return render(request, 'marketing/landing_page.html', context)
