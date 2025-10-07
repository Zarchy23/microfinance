from django.contrib import admin
from .models import Client, LoanApplication, RiskAssessment, Payment, Notification
admin.site.register(Client)
admin.site.register(LoanApplication)
admin.site.register(RiskAssessment)
admin.site.register(Payment)
admin.site.register(Notification)
