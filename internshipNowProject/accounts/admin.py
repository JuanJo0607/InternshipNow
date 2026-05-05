from django.contrib import admin
from accounts.models import User, StudentProfile, CompanyProfile

admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(CompanyProfile)
