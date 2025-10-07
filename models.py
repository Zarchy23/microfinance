from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    national_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else self.national_id}"

class LoanApplication(models.Model):
    STATUS_CHOICES = [('submitted','Submitted'),('assessed','Assessed'),('approved','Approved'),('rejected','Rejected'),('paid','Paid')]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term_months = models.IntegerField()
    purpose = models.CharField(max_length=255)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    existing_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    def __str__(self):
        return f"Loan #{self.id} - {self.client}"

class RiskAssessment(models.Model):
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=7, decimal_places=2)
    grade = models.CharField(max_length=10)
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    assessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Risk {self.score} ({self.grade}) for {self.application}"

class Payment(models.Model):
    GATEWAY_CHOICES = [('ecocash','EcoCash'),('zipit','Zipit')]
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    reference = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.reference} via {self.gateway}"

class Notification(models.Model):
    # simple notification stored when a new loan is submitted
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notif for Loan {self.loan.id} - {'Read' if self.read else 'New'}"
