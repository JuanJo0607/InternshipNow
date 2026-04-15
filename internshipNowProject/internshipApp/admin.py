from django.contrib import admin
from .models import User, StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication, InternshipOfferView

admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(CompanyProfile)

@admin.register(InternshipOffer)
class InternshipOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('title', 'description', 'requirements', 'desired_skills')

@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('student__user__username', 'offer__title')

@admin.register(InternshipOfferView)
class InternshipOfferViewAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('offer__title', 'student__user__username')