from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
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
            with transaction.atomic():
                school = form.save(commit=False)
                school.is_approved = False
                school.save()
                CustomUser.objects.create_user(
                    username=form.cleaned_data['headmaster_username'],
                    password=form.cleaned_data['headmaster_password'],
                    phone=form.cleaned_data['headmaster_phone'],
                    email=form.cleaned_data['headmaster_email'],
                    role='HEADMASTER',
                    school=school,
                    is_active=False,
                    is_staff=False,
                    must_change_password=False,
                    school_registration_pending=True,
                )

            messages.success(
                request,
                "Ombi lako limepokelewa. Akaunti itafunguliwa baada ya ukaguzi na idhini ya admin."
            )
            return redirect('shule_core:registration_received')
    else:
        form = SchoolRegistrationForm()

    return render(request, 'shule_core/register_school.html', {'form': form})


def school_registration_received(request):
    return render(request, 'shule_core/registration_received.html')


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
