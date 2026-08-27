from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SchoolRegistrationForm
from .models import CustomUser


def register_school(request):
    """
    Ukurasa PEKEE wa 'shule_core' app - kusajili shule mpya kabisa kwenye
    mfumo. Kila kitu kingine (academic, store, discipline, n.k.) kina
    urls/views zake katika apps zake zenyewe - hii haigusi chochote pale.
    """
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()

            CustomUser.objects.create_user(
                username=form.cleaned_data['headmaster_username'],
                password=form.cleaned_data['headmaster_password'],
                phone=form.cleaned_data['headmaster_phone'],
                role='HEADMASTER',
                school=school,
                is_staff=True,
            )
            messages.success(request, f"Shule ya {school.name} imesajiliwa kikamilifu! Sasa ingia.")
            return redirect('accounts:login')
    else:
        form = SchoolRegistrationForm()

    return render(request, 'shule_core/register_school.html', {'form': form})


def health_check_view(request):
    """
    /health/ - endpoint rahisi ya kuchekki kama mfumo uko hai (database
    inafikika). UptimeRobot (bure) inaita hii kila dakika 5; ikishindwa
    mara mbili mfululizo, inakutumia SMS/email kiotomatiki.
    """
    from django.http import JsonResponse
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=503)
