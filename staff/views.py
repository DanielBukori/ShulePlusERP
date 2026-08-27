import secrets
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from shule_core.models import CustomUser, Staff, SubjectAssignment
from .forms import TeacherRegistrationForm, SubjectAssignmentForm
from audit.utils import log_action

MANAGER_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'ACADEMIC']

def _get_school(request):
    return getattr(request, 'school', None)

def staff_manager_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in MANAGER_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper

@staff_manager_required
def register_teacher_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, school=school)
        email = request.POST.get('email', '').strip()

        # --- 1. Email ni LAZIMA (kwa ajili ya 2FA magic link) ---
        if not email:
            messages.error(
                request,
                "Email ya mwalimu ni lazima - itatumika kutuma link ya kuingia (2FA)."
            )
            return redirect('staff:register_teacher')

        # --- 2. Email isiwe imeshatumika na mtumiaji mwingine ---
        if CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                f"Email '{email}' tayari inatumiwa na mtumiaji mwingine. "
                "Kila mtumiaji lazima awe na email yake ya kipekee."
            )
            return redirect('staff:register_teacher')

        if form.is_valid():
            with transaction.atomic():
                phone_digits = ''.join(ch for ch in form.cleaned_data['phone'] if ch.isdigit())
                username = f"{school.subdomain}{phone_digits}"
                temp_password = f"{secrets.randbelow(900000) + 100000}"  # PIN ya tarakimu 6

                user = CustomUser.objects.create_user(
                    username=username,
                    password=temp_password,
                    phone=phone_digits,
                    email=email,
                    role='TEACHER',
                    school=school,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    must_change_password=True,
                )
                staff = Staff.objects.create(
                    user=user,
                    school=school,
                    tsc_number=form.cleaned_data.get('tsc_number') or None,
                    qualification=form.cleaned_data.get('qualification'),
                    is_teaching_staff=True,
                    is_store_keeper=form.cleaned_data.get('is_store_keeper', False),
                )

            messages.success(
                request,
                f"Mwalimu {user.get_full_name()} amesajiliwa. Akaunti: {username} / {temp_password} "
                f"(mtumie sasa hivi). Sasa mpangie masomo/madarasa."
            )
            log_action(
                request.user, school, 'TEACHER_REGISTERED',
                f"Amesajili mwalimu {user.get_full_name()} ({username})."
            )
            return redirect('staff:manage_assignments', staff_id=staff.id)
    else:
        form = TeacherRegistrationForm(school=school)

    context = {'school': school, 'form': form}
    return render(request, 'staff/register_teacher.html', context)

@staff_manager_required
def manage_assignments_view(request, staff_id):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    staff = get_object_or_404(Staff, id=staff_id, school=school)

    if request.method == 'POST':
        form = SubjectAssignmentForm(request.POST, school=school)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.school = school
            assignment.teacher = staff.user
            assignment.save()
            messages.success(
                request,
                f"{staff.user.get_full_name()} amepangiwa {assignment.subject.name} - {assignment.school_class}."
            )
            return redirect('staff:manage_assignments', staff_id=staff.id)
    else:
        form = SubjectAssignmentForm(school=school)

    assignments = SubjectAssignment.objects.filter(school=school, teacher=staff.user).select_related(
        'subject', 'school_class', 'combination'
    )
    context = {'school': school, 'staff': staff, 'form': form, 'assignments': assignments}
    return render(request, 'staff/manage_assignments.html', context)

@staff_manager_required
def teacher_list_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    teachers = Staff.objects.filter(school=school, is_teaching_staff=True).select_related('user')
    context = {'school': school, 'teachers': teachers}
    return render(request, 'staff/teacher_list.html', context)

@staff_manager_required
def assign_class_teacher_view(request):
    """
    Kila SchoolClass inaweza kuwa na Mwalimu wa Darasa mmoja (class_teacher) –
    Ndiye pekee anayeruhusiwa kuandika mahudhurio ya darasa hilo.
    """
    from shule_core.models import SchoolClass

    School = _get_school(request)
    if not School:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    classes = SchoolClass.objects.filter(school=School).order_by('level', 'name')
    teachers = CustomUser.objects.filter(school=School, role='TEACHER')

    if request.method == 'POST':
        updated = 0
        for c in classes:
            teacher_id = request.POST.get(f'class_teacher_{c.id}', '').strip()
            new_teacher = teachers.filter(id=teacher_id).first() if teacher_id else None
            if c.class_teacher_id != (new_teacher.id if new_teacher else None):
                c.class_teacher = new_teacher
                c.save()
                updated += 1
        messages.success(request, f"Walimu wa Darasa wamesasishwa ({updated} zilizobadilika).")
        return redirect('staff:assign_class_teacher')

    context = {'school': School, 'classes': classes, 'teachers': teachers}
    return render(request, 'staff/assign_class_teacher.html', context)


