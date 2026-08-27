from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    context = {'notifications': notifications}
    return render(request, 'notifications/notifications_list.html', context)


@login_required
def mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    next_url = request.GET.get('next', '/')
    return redirect(next_url)


@login_required
def mark_read_and_go_view(request, notification_id):
    """Mtu akibofya notification moja - inakuwa 'read' kisha inampeleka kwenye link yake."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link or '/')
