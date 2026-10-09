from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect

from shule_core.models import AcademicResult, SubjectAssignment, Student
from .forms import (
    MarksFilterForm, EmergencyMarksFilterForm, StatsFilterForm, HomePackageForm,
    RAW_EXAM_TYPES_TERM_1, RAW_EXAM_TYPES_TERM_2, SERIES_EXAM_TYPES,
)
from .models import HomePackage
from audit.utils import log_action
from academic.grading import recompute_derived_results


def _get_school(request):
    return getattr(request, 'school', None)


def teacher_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'TEACHER':
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu - wewe si Mwalimu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def marks_entry_allowed(view_func):
    """
    Marks entry inaruhusu Teacher (somo lake tu, kwenye view yenyewe) NA
    Academic/Headmaster/Second Master (DHARURA - somo/darasa lolote).
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ('TEACHER', 'ACADEMIC', 'HEADMASTER', 'SECOND_MASTER'):
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def _score_to_grade(score, level):
    if level == 'A':
        if score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        elif score >= 40: return 'E'
        elif score >= 35: return 'S'
        else: return 'F'
    else:
        if score >= 75: return 'A'
        elif score >= 65: return 'B'
        elif score >= 45: return 'C'
        elif score >= 30: return 'D'
        else: return 'F'


@teacher_required
def teacher_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    assignments = SubjectAssignment.objects.filter(teacher=request.user).select_related(
        'subject', 'school_class', 'combination'
    )
    recent_packages = HomePackage.objects.filter(teacher=request.user)[:5]

    context = {'school': school, 'assignments': assignments, 'recent_packages': recent_packages}
    return render(request, 'teacher_portal/teacher_dashboard.html', context)


@marks_entry_allowed
def enter_marks_view(request):
    """
    Marks Entry ya SPREADSHEET - column zote za CA (Test1_A, Test2_A,
    Mid-Term Exam, Test1_B, Test2_B, Terminal/Annual Exam) kwa pamoja,
    pamoja na 'Matokeo Yaliyokokotolewa' (Mid-Term + Terminal/Annual)
    yanayoonekana papo hapo baada ya kuhifadhi.

    Teacher: somo/darasa lake tu (SubjectAssignment).
    Academic/Headmaster/Second Master: somo/darasa LOLOTE (DHARURA).
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    is_emergency = request.user.role in ('ACADEMIC', 'HEADMASTER', 'SECOND_MASTER')

    if is_emergency:
        filter_form = EmergencyMarksFilterForm(request.GET or None, school=school)
    else:
        filter_form = MarksFilterForm(request.GET or None, teacher=request.user)

    students = []
    subject = school_class = None
    exam_columns = []
    series_columns = []
    computed_type = None
    assignment = None  # inatumika tu kwa njia ya Teacher (siyo emergency)

    if filter_form.is_valid():
        if is_emergency:
            subject = filter_form.cleaned_data['subject']
            school_class = filter_form.cleaned_data['school_class']
            combination = filter_form.cleaned_data.get('combination')
        else:
            assignment = filter_form.cleaned_data['assignment']
            subject = assignment.subject
            school_class = assignment.school_class
            combination = assignment.combination

        term = filter_form.cleaned_data['term']
        academic_year = filter_form.cleaned_data['academic_year']

        exam_columns = RAW_EXAM_TYPES_TERM_1 if term == 'TERM_1' else RAW_EXAM_TYPES_TERM_2
        series_columns = SERIES_EXAM_TYPES
        computed_type = 'TERMINAL' if term == 'TERM_1' else 'ANNUAL'
        all_columns = exam_columns + series_columns

        student_qs = Student.objects.filter(school=school, school_class=school_class)
        if combination:
            student_qs = student_qs.filter(combination=combination)

        existing = AcademicResult.objects.filter(
            subject=subject, term=term, academic_year=academic_year, student__in=student_qs,
        )
        existing_map = {}
        for r in existing:
            existing_map.setdefault(r.student_id, {})[r.exam_type] = r.score

        for s in student_qs:
            row_scores = existing_map.get(s.id, {})
            students.append({
                'student': s,
                'score_list': [(code, row_scores.get(code, '')) for code, _ in exam_columns],
                'series_list': [(code, row_scores.get(code, '')) for code, _ in series_columns],
                'midterm': row_scores.get('MID_TERM', ''),
                'final': row_scores.get(computed_type, ''),
            })

        if request.method == 'POST':
            saved_count = 0
            touched_students = set()
            with transaction.atomic():
                for s in student_qs:
                    for code, _ in all_columns:
                        raw_score = request.POST.get(f'score_{s.id}_{code}', '').strip()
                        if raw_score == '':
                            continue
                        try:
                            score_val = float(raw_score)
                        except ValueError:
                            continue
                        AcademicResult.objects.update_or_create(
                            student=s, subject=subject, exam_type=code,
                            term=term, academic_year=academic_year,
                            defaults={
                                'school': school,
                                'school_class': school_class,
                                'combination': combination,
                                'score': score_val,
                                'recorded_by': request.user,
                            },
                        )
                        saved_count += 1
                        # Series haziathiri MID_TERM/TERMINAL/ANNUAL - recompute
                        # inahitajika tu kwa raw CA columns (exam_columns)
                        if code in dict(exam_columns):
                            touched_students.add(s.id)

                for s in student_qs:
                    if s.id in touched_students:
                        recompute_derived_results(
                            school, s, subject, term, academic_year, school_class,
                            combination=combination,
                        )

            messages.success(request, f"Marks {saved_count} zimehifadhiwa - {subject.name} ({school_class}).")
            log_action(
                request.user, school, 'MARKS_ENTERED',
                f"{'[DHARURA] ' if is_emergency else ''}Amejaza marks {saved_count} - {subject.name} "
                f"({school_class}, {term}, {academic_year})."
            )
            return redirect(f"{request.path}?{request.GET.urlencode()}")

    context = {
        'school': school, 'filter_form': filter_form, 'students': students,
        'subject': subject, 'school_class': school_class, 'exam_columns': exam_columns,
        'series_columns': series_columns, 'computed_type': computed_type, 'is_emergency': is_emergency,
    }
    return render(request, 'teacher_portal/enter_marks.html', context)


@teacher_required
def subject_stats_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    filter_form = StatsFilterForm(request.GET or None, teacher=request.user)
    stats = {}
    assignment = None

    if filter_form.is_valid():
        assignment = filter_form.cleaned_data['assignment']
        exam_type = filter_form.cleaned_data['exam_type']
        term = filter_form.cleaned_data['term']
        academic_year = filter_form.cleaned_data['academic_year']
        level = assignment.subject.level

        results = AcademicResult.objects.filter(
            subject=assignment.subject, exam_type=exam_type, term=term, academic_year=academic_year,
            school=school,
        )
        scores = [float(r.score) for r in results]

        if scores:
            grades = [_score_to_grade(s, level) for s in scores]
            pass_mark = 30 if level == 'O' else 40
            stats = {
                'total_students': len(scores),
                'average': round(sum(scores) / len(scores), 2),
                'highest': max(scores),
                'lowest': min(scores),
                'passed': sum(1 for s in scores if s >= pass_mark),
                'failed': sum(1 for s in scores if s < pass_mark),
                'grade_counts': {g: grades.count(g) for g in sorted(set(grades))},
            }

    context = {'school': school, 'filter_form': filter_form, 'stats': stats, 'assignment': assignment}
    return render(request, 'teacher_portal/subject_stats.html', context)


@teacher_required
def upload_home_package_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = HomePackageForm(request.POST, request.FILES, teacher=request.user)
        if form.is_valid():
            package = form.save(commit=False)
            package.school = school
            package.teacher = request.user
            package.save()
            messages.success(request, f"'{package.title}' imepakiwa kwa ajili ya {package.school_class}.")
            return redirect('teacher_portal:upload_home_package')
    else:
        form = HomePackageForm(teacher=request.user)

    my_packages = HomePackage.objects.filter(teacher=request.user)
    context = {'school': school, 'form': form, 'my_packages': my_packages}
    return render(request, 'teacher_portal/upload_home_package.html', context)


@login_required
def download_home_package_view(request, package_id):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia faili hili.")

    package = get_object_or_404(
        HomePackage.objects.select_related('school_class'),
        pk=package_id,
        school=school,
    )
    user = request.user
    allowed = user.school_id == school.pk and user.role in ('HEADMASTER', 'SECOND_MASTER', 'ACADEMIC')

    if user.role == 'TEACHER':
        allowed = allowed or package.teacher_id == user.pk
    elif user.role == 'STUDENT':
        allowed = Student.objects.filter(
            user=user,
            school=school,
            school_class=package.school_class,
        ).exists()
    elif user.role == 'PARENT':
        allowed = Student.objects.filter(
            parent=user,
            school=school,
            school_class=package.school_class,
        ).exists()

    if not allowed:
        return HttpResponseForbidden("Hauruhusiwi kufikia faili hili.")
    if not package.file:
        raise Http404("Faili la kazi hii halipo.")

    return FileResponse(
        package.file.open('rb'),
        as_attachment=True,
        filename=package.file.name.rsplit('/', 1)[-1],
    )
