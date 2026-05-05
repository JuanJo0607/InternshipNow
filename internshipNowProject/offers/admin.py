from django.contrib import admin
from offers.models import InternshipOffer, InternshipOfferView


@admin.register(InternshipOffer)
class InternshipOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('title', 'description', 'requirements', 'desired_skills')


@admin.register(InternshipOfferView)
class InternshipOfferViewAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('offer__title', 'student__user__username')
