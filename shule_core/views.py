from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .forms import SchoolRegistrationForm, SchoolSettingsForm
from .models import (
    CustomUser, SchoolClass, Subject, Student, Staff, SubjectAssignment,
    AcademicResult,
)

SETUP_ROLES = ('HEADMASTER', 'SECOND_MASTER', 'ACADEMIC')


def _school_for(request):
    school = getattr(request, 'school', None)
    if school:
        return school
    if request.user.is_authenticated:
        return request.user.school
    return None


@login_required
def school_settings_view(request):
    """Utambulisho wa shule (rangi, logo, sender ID, anwani) - headmaster tu."""
    school = _school_for(request)
    if not school or request.user.role not in ('HEADMASTER', 'SECOND_MASTER'):
        return HttpResponseForbidden('Hauruhusiwi kufikia ukurasa huu.')

    form = SchoolSettingsForm(request.POST or None, request.FILES or None, instance=school)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mipangilio ya shule yamesasishwa.')
        return redirect('shule_core:school_settings')

    return render(request, 'shule_core/school_settings.html', {
        'school': school,
        'form': form,
        'public_host': f'{school.subdomain}.{request.get_host().split(":")[0]}',
    })


@login_required
def onboarding_view(request):
    """
    Orodha ya hatua za kuanisha shule mpya. Kila hali ya 'imekamilika'
    inatokana na hesabu halisi za data ya shule hiyo - hakuna kuweka
    tiki mwenyewe, kwa hiyo orodha haitaonyesha hatua imekamilika bila
    data kweli iko kwenye database.
    """
    from accountant.models import FeeStructure

    school = _school_for(request)
    if not school or request.user.role not in SETUP_ROLES:
        return HttpResponseForbidden('Hauruhusiwi kufikia ukurasa huu.')

    from .class_setup import ensure_standard_classes
    ensure_standard_classes(school)

    counts = {
        'classes': SchoolClass.objects.filter(school=school).count(),
        'subjects': Subject.objects.filter(school=school).count(),
        'students': Student.objects.filter(school=school).count(),
        'teachers': Staff.objects.filter(school=school, is_teaching_staff=True).count(),
        'assignments': SubjectAssignment.objects.filter(school=school).count(),
        'fees': FeeStructure.objects.filter(school=school).count(),
        'results': AcademicResult.objects.filter(school=school).count(),
        'published': AcademicResult.objects.filter(school=school, is_published=True).count(),
    }

    profile = getattr(school, 'public_profile', None)
    brand_set = bool(school.logo) and bool(school.address) and school.primary_color != '#7E22CE'

    steps = [
        {
            'id': 'identity',
            'title': 'Utambulisho wa Shule',
            'detail': 'Weka logo, anwani na rangi yako kuu - mfumo mzima (menyu, chati, tovuti ya umma) utavaa rangi hiyo.',
            'done': brand_set,
            'metric': 'Logo, anwani na rangi',
            'url': 'shule_core:school_settings',
            'cta': 'Fungua Mipangilio',
        },
        {
            'id': 'subjects',
            'title': 'Masomo na Madarasa',
            'detail': 'Madarasa ya kawaida (kidato cha I–VI) tayari yapo. Ongeza masomo unayofundisha.',
            'done': counts['subjects'] > 0,
            'metric': f"Masomo {counts['subjects']} · Madarasa {counts['classes']}",
            'url': 'academic:school_setup',
            'cta': 'Ongeza Masomo',
        },
        {
            'id': 'students',
            'title': 'Sajili Wanafunzi',
            'detail': 'Pakia kiolezo cha Excel ili uwaingize wote kwa mara moja; akaunti za wazazi zinaundwa kiotomatiki.',
            'done': counts['students'] > 0,
            'metric': f"Wanafunzi {counts['students']}",
            'url': 'academic:bulk_register_students',
            'cta': 'Pakia Orodha',
        },
        {
            'id': 'teachers',
            'title': 'Sajili Walimu',
            'detail': 'Kila mwalimu hupata akaunti ya kuingia na OTP kwenye simu yake.',
            'done': counts['teachers'] > 0,
            'metric': f"Walimu {counts['teachers']}",
            'url': 'staff:register_teacher',
            'cta': 'Sajili Mwalimu',
        },
        {
            'id': 'assignments',
            'title': 'Gawa Masomo kwa Walimu',
            'detail': 'Bila ugawaji, walimu hawawezi kuingia kujaza alama za darasa lolote.',
            'done': counts['assignments'] > 0,
            'metric': f"Ugawaji {counts['assignments']}",
            'url': 'staff:teacher_list',
            'cta': 'Gawa Masomo',
        },
        {
            'id': 'fees',
            'title': 'Muundo wa Ada',
            'detail': 'Weka ada ya kila darasa kwa mwaka wa sasa kabla ya kuanza kupokea malipo.',
            'done': counts['fees'] > 0,
            'metric': f"Miundo {counts['fees']}",
            'url': 'accountant:set_fee_structure',
            'cta': 'Weka Ada',
        },
        {
            'id': 'marks',
            'title': 'Jaza Alama za Kwanza',
            'detail': 'Alama za CA na mtihani hujazwa na walimu; mkuu anaweza kuingia dharura.',
            'done': counts['results'] > 0,
            'metric': f"Rekodi {counts['results']}",
            'url': 'teacher_portal:enter_marks',
            'cta': 'Jaza Alama',
        },
        {
            'id': 'publish',
            'title': 'Chapisha Matokeo',
            'detail': 'Ukichapisha, wazazi na wanafunzi huanza kuona ripoti zao kwenye tovuti.',
            'done': counts['published'] > 0,
            'metric': f"Zilizochapishwa {counts['published']}",
            'url': 'academic:publish_results',
            'cta': 'Chapisha',
        },
        {
            'id': 'website',
            'title': 'Tovuti ya Umma ya Shule',
            'detail': 'Wasifu, mission/vision na picha ya juu - hii ndiyo mwanzo wa tovuti yako.',
            'done': bool(profile and profile.is_complete()),
            'metric': 'Wasifu wa umma',
            'url': 'branding:edit_profile',
            'cta': 'Hariri Wasifu',
        },
    ]

    done_count = sum(1 for s in steps if s['done'])
    progress = round(done_count * 100 / len(steps))

    return render(request, 'shule_core/onboarding.html', {
        'school': school,
        'steps': steps,
        'counts': counts,
        'done_count': done_count,
        'progress': progress,
        'total_steps': len(steps),
    })


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
                "Ombi lako limepokelewa. Akaunti itafunguliwa baada ya ukaguzi na idhini ya msimamizi."
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
