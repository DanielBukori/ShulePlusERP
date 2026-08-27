from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from shule_core.models import CustomUser
from .models import AuditLog


def _get_school(request):
    return getattr(request, 'school', None)


def headmaster_required(view_func):
    """Audit log ni siri kubwa - Headmaster PEKEE anaweza kuiona."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'HEADMASTER':
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu - Mkuu wa Shule pekee.")
        return view_func(request, *args, **kwargs)
    return wrapper


@headmaster_required
def audit_log_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    logs = AuditLog.objects.filter(school=school).select_related('actor')

    actor_id = request.GET.get('actor')
    action = request.GET.get('action')
    if actor_id:
        logs = logs.filter(actor_id=actor_id)
    if action:
        logs = logs.filter(action=action)

    logs = logs[:200]  # dumu ya haraka - ukurasa ujao tunaweza kuongeza pagination

    actors = CustomUser.objects.filter(school=school, audit_actions__isnull=False).distinct()

    context = {
        'school': school, 'logs': logs, 'actors': actors,
        'action_choices': AuditLog.ACTION_CHOICES,
        'selected_actor': actor_id, 'selected_action': action,
    }
    return render(request, 'audit/audit_log.html', context)
