from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.http import JsonResponse
from notifications.models import Notification


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def delete_notification(request, notification_id):
    Notification.objects.filter(id=notification_id, user=request.user).delete()
    return JsonResponse({'status': 'ok'})
