from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models as dj_models
from django.db import transaction
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from shule_core.models import Student
from .forms import OffenseTypeForm, DisciplineIncidentForm, IncidentSpreadsheetFilterForm
from .models import OffenseType, DisciplineIncident, DisciplineAlert, get_student_discipline_score
from audit.utils import log_action


DISCIPLINE_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'DISCIPLINE']


def _get_school(request):
    return getattr(request, 'school', None)


def discipline_role_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in DISCIPLINE_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


from notifications.utils import notify


def _notify_discipline_alert(alert):
    """
    Inatuma bell + SMS kwa mzazi wa mwanafunzi mwenye alert, kumjulisha
    alama zimeshuka na anahitajika shuleni.
    """
    student = alert.student
    if student.parent:
        message = (
            f"ShulePlusERP: Taarifa ya nidhamu - alama za {student.first_name} "
            f"{student.last_name} zimeshuka hadi {alert.score_at_alert}/100. "
            f"Tafadhali wasiliana na shule haraka."
        )
        notify(student.parent, alert.school, message, link='/family/parent/dashboard/')


@discipline_role_required
def discipline_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    open_alerts = DisciplineAlert.objects.filter(school=school, is_resolved=False).select_related('student')
    recent_incidents = DisciplineIncident.objects.filter(school=school).select_related('student', 'offense_type')[:20]

    context = {
        'school': school,
        'open_alerts': open_alerts,
        'recent_incidents': recent_incidents,
    }
    return render(request, 'discipline/discipline_dashboard.html', context)


@discipline_role_required
def full_report_view(request):
    """
    Ripoti KAMILI ya nidhamu kwa mwaka mmoja - kila kosa la kila
    mwanafunzi likiwa na jina, kosa, alama zilizokatwa, na tarehe -
    yote mahali pamoja, yamepangwa kwa mwanafunzi mwenye alama za chini
    kabisa kwanza (wenye tatizo kubwa zaidi la nidhamu).
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    academic_year = int(request.GET.get('academic_year') or timezone.now().year)

    incidents = DisciplineIncident.objects.filter(
        school=school, academic_year=academic_year
    ).select_related('student', 'offense_type', 'student__school_class').order_by(
        'student__school_class__name', 'student__reg_number', '-date_occurred'
    )

    by_student = {}
    for inc in incidents:
        sid = inc.student_id
        by_student.setdefault(sid, {'student': inc.student, 'incidents': [], 'total_deducted': 0})
        by_student[sid]['incidents'].append(inc)
        by_student[sid]['total_deducted'] += inc.offense_type.points_deducted

    student_rows = []
    for sid, data in by_student.items():
        score = get_student_discipline_score(data['student'], academic_year)
        student_rows.append({
            'student': data['student'],
            'school_class': data['student'].school_class,
            'incidents': data['incidents'],
            'total_deducted': data['total_deducted'],
            'score': score,
        })
    student_rows.sort(key=lambda r: r['score'])

    context = {
        'school': school,
        'academic_year': academic_year,
        'student_rows': student_rows,
        'total_incidents': incidents.count(),
        'total_students_involved': len(student_rows),
    }
    return render(request, 'discipline/full_report.html', context)


@discipline_role_required
def add_offense_type_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = OffenseTypeForm(request.POST)
        if form.is_valid():
            offense = form.save(commit=False)
            offense.school = school
            offense.save()
            messages.success(request, f"Kosa '{offense.name}' limeongezwa kwenye orodha.")
            return redirect('discipline:add_offense_type')
    else:
        form = OffenseTypeForm()

    offense_types = OffenseType.objects.filter(school=school)
    context = {'school': school, 'form': form, 'offense_types': offense_types}
    return render(request, 'discipline/add_offense_type.html', context)


@discipline_role_required
def record_incident_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = DisciplineIncidentForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            with transaction.atomic():
                incident = form.save(commit=False)
                incident.school = school
                incident.recorded_by = request.user
                incident.save()

                score = get_student_discipline_score(incident.student, incident.academic_year)

                alert_msg = None
                if score < school.discipline_alert_score:
                    alert, created = DisciplineAlert.objects.get_or_create(
                        student=incident.student, academic_year=incident.academic_year,
                        defaults={'school': school, 'score_at_alert': score},
                    )
                    if created:
                        _notify_discipline_alert(alert)
                        alert_msg = (
                            f"⚠ ALERT: Alama za {incident.student} zimeshuka hadi {score} "
                            f"(chini ya kiwango cha {school.discipline_alert_score}). "
                            f"Bodi ikae / Mzazi aitwe."
                        )

            messages.success(request, f"Kosa la {incident.student} limerekodiwa. Alama za sasa: {score}.")
            log_action(
                request.user, school, 'DISCIPLINE_RECORDED',
                f"Amerekodi kosa la '{incident.offense_type.name}' kwa {incident.student} (-{incident.offense_type.points_deducted} pts)."
            )
            if alert_msg:
                messages.warning(request, alert_msg)
            return redirect('discipline:record_incident')
    else:
        form = DisciplineIncidentForm(school=school)

    context = {'school': school, 'form': form}
    return render(request, 'discipline/record_incident.html', context)


@discipline_role_required
def record_incident_spreadsheet_view(request):
    """
    Kurekodi makosa kwa WINGI - kama Marks Entry, LAKINI safu (columns)
    ni AINA ZA MAKOSA (siyo mtihani), na kiini ni TIKI/checkbox (siyo
    namba) - kwa sababu kosa ni tukio la nadra, siyo kitu ambacho kila
    mwanafunzi 'anahitajika' kuwa nacho.

    Chagua Darasa + Tarehe + Mwaka -> wanafunzi WOTE wa darasa
    wanaonekana, tiki tu wale walio na kosa siku hiyo, 'Hifadhi' moja
    inarekodi yote kwa pamoja. Tiki iliyopo tayari (kutoka ziara ya
    awali ya ukurasa huu huo huo) haiundwi mara mbili - get_or_create
    kwa (student, offense_type, date_occurred).

    Kwa makosa yanayohitaji ushahidi (picha/PDF) au maelezo marefu,
    tumia 'Rekodi Kosa (Moja kwa Moja)'.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    filter_form = IncidentSpreadsheetFilterForm(request.GET or None, school=school)
    students = []
    school_class = None
    date_occurred = None
    academic_year = None
    offense_types = OffenseType.objects.filter(school=school)

    if filter_form.is_valid():
        school_class = filter_form.cleaned_data['school_class']
        date_occurred = filter_form.cleaned_data['date_occurred']
        academic_year = filter_form.cleaned_data['academic_year']

        student_qs = Student.objects.filter(school=school, school_class=school_class)

        existing = DisciplineIncident.objects.filter(
            student__in=student_qs, date_occurred=date_occurred,
        ).values_list('student_id', 'offense_type_id')
        existing_set = set(existing)

        for s in student_qs:
            cells = [(ot.id, (s.id, ot.id) in existing_set) for ot in offense_types]
            students.append({'student': s, 'cells': cells})

        if request.method == 'POST':
            created_count = 0
            alert_msgs = []
            with transaction.atomic():
                for s in student_qs:
                    for ot in offense_types:
                        field_name = f'offense_{s.id}_{ot.id}'
                        if request.POST.get(field_name):
                            _, created = DisciplineIncident.objects.get_or_create(
                                student=s, offense_type=ot, date_occurred=date_occurred,
                                defaults={
                                    'school': school, 'academic_year': academic_year,
                                    'recorded_by': request.user,
                                },
                            )
                            if created:
                                created_count += 1
                                score = get_student_discipline_score(s, academic_year)
                                if score < school.discipline_alert_score:
                                    alert, alert_created = DisciplineAlert.objects.get_or_create(
                                        student=s, academic_year=academic_year,
                                        defaults={'school': school, 'score_at_alert': score},
                                    )
                                    if alert_created:
                                        _notify_discipline_alert(alert)
                                        alert_msgs.append(f"{s}: alama zimeshuka hadi {score}")

            messages.success(request, f"Makosa {created_count} yamerekodiwa - {school_class} ({date_occurred}).")
            log_action(
                request.user, school, 'DISCIPLINE_RECORDED',
                f"[Spreadsheet] Amerekodi makosa {created_count} - {school_class} ({date_occurred})."
            )
            for m in alert_msgs:
                messages.warning(request, f"⚠ ALERT: {m}")
            return redirect(f"{request.path}?{request.GET.urlencode()}")

    context = {
        'school': school, 'filter_form': filter_form, 'students': students,
        'school_class': school_class, 'date_occurred': date_occurred, 'academic_year': academic_year,
        'offense_types': offense_types,
    }
    return render(request, 'discipline/record_incident_spreadsheet.html', context)


@discipline_role_required
def view_evidence_view(request, incident_id):
    """Ushahidi wa kosa - Headmaster/Second Master/Discipline PEKEE, siyo mzazi/mwanafunzi."""
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    incident = get_object_or_404(DisciplineIncident, id=incident_id, school=school)

    if not incident.evidence_file:
        raise Http404("Hakuna ushahidi uliopakiwa kwa kosa hili.")

    filename = incident.evidence_file.name.split('/')[-1]
    return FileResponse(incident.evidence_file.open('rb'), filename=filename)
