from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404

from .forms import OffenseTypeForm, DisciplineIncidentForm
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
                if score < school.discipline_alert_threshold:
                    alert, created = DisciplineAlert.objects.get_or_create(
                        student=incident.student, academic_year=incident.academic_year,
                        defaults={'school': school, 'score_at_alert': score},
                    )
                    if created:
                        _notify_discipline_alert(alert)
                        alert_msg = (
                            f"⚠ ALERT: Alama za {incident.student} zimeshuka hadi {score} "
                            f"(chini ya kiwango cha {school.discipline_alert_threshold}). "
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
