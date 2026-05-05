from django.urls import path
from accounts import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/upload-cv/', views.upload_cv, name='upload_cv'),
    path('company/profile/', views.company_profile, name='company_profile'),
]
