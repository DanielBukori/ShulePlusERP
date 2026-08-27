from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden, HttpResponse

from shule_core.models import AcademicResult, Student, ConductReport
from academic.views import _build_broadsheet
from accountant.models import get_student_debt
from discipline.models import get_student_discipline_score, DisciplineAlert, DisciplineIncident
from store.models import StudentContribution
from teacher_portal.models import HomePackage


def _get_school(request):
    return getattr(request, 'school', None)


def parent_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'PARENT':
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'STUDENT':
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_latest_published_summary(student):
    """
    Inatafuta matokeo ya hivi karibuni yaliyochapishwa (is_published=True),
    kisha inatumia _build_broadsheet (kutoka academic app) kupata
    position/division/average halisi ya mwanafunzi huyu kwenye darasa lake.
    """
    latest = AcademicResult.objects.filter(
        student=student, is_published=True
    ).order_by('-academic_year', '-updated_at').first()

    if not latest or not student.school_class:
        return None

    groups = _build_broadsheet(
        student.school, student.school_class, latest.term, latest.exam_type, latest.academic_year
    )
    for group in groups:
        for row in group['rows']:
            if row['student'].id == student.id:
                return {
                    'term': latest.term, 'exam_type': latest.exam_type,
                    'academic_year': latest.academic_year,
                    'average': row['average'], 'position': row['position'],
                    'division': row['division'], 'total_students': group['total_students'],
                }
    return None


def _available_result_combos(student):
    """Orodha ya (term, exam_type, academic_year) zote zilizochapishwa kwa
    mwanafunzi huyu - kwa dropdown ya 'Ripoti za Nyuma'."""
    from django.db.models import Count
    return list(
        AcademicResult.objects.filter(student=student, is_published=True)
        .values('academic_year', 'term', 'exam_type')
        .annotate(n=Count('id'))
        .order_by('-academic_year', '-n')
    )


def _get_summary_for_combo(student, term, exam_type, academic_year):
    """Kama _get_latest_published_summary, ila kwa mchanganyiko MAALUM
    ulioteuliwa (siyo lazima ya 'sasa')."""
    if not student.school_class:
        return None

    groups = _build_broadsheet(student.school, student.school_class, term, exam_type, academic_year)
    for group in groups:
        for row in group['rows']:
            if row['student'].id == student.id:
                return {
                    'term': term, 'exam_type': exam_type, 'academic_year': academic_year,
                    'average': row['average'], 'position': row['position'],
                    'division': row['division'], 'total_students': group['total_students'],
                }
    return None


def _get_series_results(student):
    """
    Mitihani ya Maandalizi (Series 1-5) - taarifa ya MAENDELEO tu kwa
    wazazi, HAZIINGII kwenye Midterm/Terminal/Annual (angalia
    academic/grading.py - haziguswi popote pale kwa makusudi).
    """
    return AcademicResult.objects.filter(
        student=student, is_published=True, exam_type__startswith='SERIES_',
    ).select_related('subject').order_by('exam_type', 'subject__name')


def _build_student_summary(student):
    """Kila kitu kuhusu mwanafunzi mmoja - matokeo, ada, discipline, store."""
    results_summary = _get_latest_published_summary(student)
    debt = get_student_debt(student)

    academic_year = results_summary['academic_year'] if results_summary else 2026
    discipline_score = get_student_discipline_score(student, academic_year)
    open_alert = DisciplineAlert.objects.filter(student=student, is_resolved=False).first()

    pending_contributions = [
        c for c in StudentContribution.objects.filter(student=student).select_related('requirement')
        if not c.is_complete
    ]

    home_packages = HomePackage.objects.filter(
        school_class=student.school_class
    ).select_related('subject').order_by('-uploaded_at')[:10] if student.school_class else []

    conduct = None
    if results_summary:
        conduct = ConductReport.objects.filter(
            student=student, term=results_summary['term'], academic_year=results_summary['academic_year']
        ).first()
        if conduct and not conduct.has_any_data():
            conduct = None

    return {
        'student': student,
        'results_summary': results_summary,
        'debt': debt,
        'discipline_score': discipline_score,
        'discipline_alert': open_alert,
        'pending_contributions': pending_contributions,
        'home_packages': home_packages,
        'series_results': _get_series_results(student),
        'conduct': conduct,
    }


@parent_required
def parent_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    children = Student.objects.filter(school=school, parent=request.user).select_related('school_class')
    summaries = [_build_student_summary(child) for child in children]

    context = {'school': school, 'summaries': summaries}
    return render(request, 'family_portal/parent_dashboard.html', context)


@parent_required
def child_detail_view(request, student_id):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    student = get_object_or_404(Student, id=student_id, school=school, parent=request.user)
    summary = _build_student_summary(student)

    context = {'school': school, 'summary': summary}
    return render(request, 'family_portal/student_summary.html', context)


@student_required
def student_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    student = Student.objects.filter(school=school, user=request.user).first()
    if not student:
        return HttpResponseForbidden("Hakuna taarifa za mwanafunzi zilizounganishwa na akaunti hii.")

    summary = _build_student_summary(student)

    context = {'school': school, 'summary': summary}
    return render(request, 'family_portal/student_summary.html', context)


def _get_authorized_student(request, student_id):
    """
    Inarudisha Student TU kama request.user ana ruhusa ya kumuona:
    - PARENT: mtoto wake mwenyewe
    - STUDENT: yeye mwenyewe
    - Staff ya Academic (Headmaster/Second Master/Academic): mwanafunzi yeyote wa shule
    """
    school = _get_school(request)
    if not school:
        return None

    student = Student.objects.filter(id=student_id, school=school).first()
    if not student:
        return None

    if request.user.role == 'PARENT' and student.parent_id == request.user.id:
        return student
    if request.user.role == 'STUDENT' and student.user_id == request.user.id:
        return student
    if request.user.role in ('HEADMASTER', 'SECOND_MASTER', 'ACADEMIC'):
        return student
    return None


def _build_report_context(student, term=None, exam_type=None, academic_year=None):
    """
    Data ya ripoti - inatumika na PDF download NA HTML preview zote mbili.
    Kama term/exam_type/academic_year vimetolewa (mzazi ameteua kwenye
    dropdown ya 'Ripoti za Nyuma'), itumike hiyo - vinginevyo default ni
    ripoti ya HIVI KARIBUNI iliyochapishwa.
    """
    school = student.school
    available_combos = _available_result_combos(student)

    if term and exam_type and academic_year:
        results_summary = _get_summary_for_combo(student, term, exam_type, int(academic_year))
    else:
        results_summary = _get_latest_published_summary(student)

    subject_results = []
    if results_summary:
        subject_results = AcademicResult.objects.filter(
            student=student, is_published=True,
            exam_type=results_summary['exam_type'], term=results_summary['term'],
            academic_year=results_summary['academic_year'],
        ).select_related('subject')

    debt = get_student_debt(student)
    academic_year_val = results_summary['academic_year'] if results_summary else 2026
    report_term = results_summary['term'] if results_summary else 'TERM_1'

    discipline_score = get_student_discipline_score(student, academic_year_val)
    recent_incidents = DisciplineIncident.objects.filter(student=student, academic_year=academic_year_val)[:5]
    pending_contributions = [
        c for c in StudentContribution.objects.filter(student=student).select_related('requirement')
        if not c.is_complete
    ]

    # Tabia/Mwenendo - kwa term+mwaka ile ile ya matokeo yanayoonyeshwa.
    # Hiari kabisa - inaonekana tu kama Class Teacher amejaza kitu.
    conduct = ConductReport.objects.filter(
        student=student, term=report_term, academic_year=academic_year_val
    ).first()
    if conduct and not conduct.has_any_data():
        conduct = None

    return {
        'school': school, 'student': student, 'results_summary': results_summary,
        'subject_results': subject_results, 'debt': debt, 'discipline_score': discipline_score,
        'recent_incidents': recent_incidents, 'pending_contributions': pending_contributions,
        'academic_year': academic_year_val, 'series_results': _get_series_results(student),
        'conduct': conduct, 'available_combos': available_combos,
    }


def preview_consolidated_report_view(request, student_id):
    """HTML preview ya ripoti - Tailwind, kuona kabla ya kupakua PDF."""
    student = _get_authorized_student(request, student_id)
    if not student:
        return HttpResponseForbidden("Hauruhusiwi kufikia ripoti hii.")

    context = _build_report_context(
        student,
        term=request.GET.get('term'),
        exam_type=request.GET.get('exam_type'),
        academic_year=request.GET.get('academic_year'),
    )
    return render(request, 'family_portal/consolidated_report_preview.html', context)


def download_consolidated_report(request, student_id):
    """
    Ripoti moja ya PDF kwa mwanafunzi mmoja - matokeo (kwa somo),
    discipline, ada/madeni, na michango ya store - yenye watermark,
    logo, na sahihi.
    """
    import weasyprint

    student = _get_authorized_student(request, student_id)
    if not student:
        return HttpResponseForbidden("Hauruhusiwi kufikia ripoti hii.")

    context = _build_report_context(
        student,
        term=request.GET.get('term'),
        exam_type=request.GET.get('exam_type'),
        academic_year=request.GET.get('academic_year'),
    )
    academic_year = context['academic_year']

    html_string = render(request, 'family_portal/consolidated_report_pdf.html', context).content.decode('utf-8')

    pdf_file = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"ripoti_{student.reg_number}_{academic_year}.pdf".replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
