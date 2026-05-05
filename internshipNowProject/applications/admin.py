from django.contrib import admin
from applications.models import InternshipApplication


@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('student__user__username', 'offer__title')
