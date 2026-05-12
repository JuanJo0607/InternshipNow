from django.urls import path
from analytics import views

urlpatterns = [
    path('company/<int:company_id>/metrics/dashboard/', views.company_metrics_page, name='company_metrics_page'),
    path('companies/<int:id>/metrics/', views.company_metrics_api, name='company_metrics_api'),
    path('api/profile-status/', views.profile_status, name='profile_status'),
    path('api/demanded-skills/', views.demanded_skills_api, name='demanded_skills_api'),
]
