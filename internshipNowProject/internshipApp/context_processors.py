def notification_context(request):
    if request.user.is_authenticated:
        notifications = request.user.notifications.all()[:5]
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'unread_notification_count': unread_count,
        }
    return {}
