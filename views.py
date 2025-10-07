from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoanApplicationForm, RegisterForm, validate_national_id, validate_phone
from .models import LoanApplication, Client, RiskAssessment, Payment, Notification
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from decimal import Decimal
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
import csv, uuid

def home(request):
    recent = LoanApplication.objects.order_by('-submitted_at')[:6]
    total = LoanApplication.objects.count()
    approved = LoanApplication.objects.filter(status='approved').count()
    rejected = LoanApplication.objects.filter(status='rejected').count()
    assessed = LoanApplication.objects.filter(status='assessed').count()
    return render(request,'home.html',{'recent':recent,'stats':{'total':total,'approved':approved,'rejected':rejected,'assessed':assessed}})

def register(request):
    if request.method=='POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            national = form.cleaned_data['national_id']
            phone = form.cleaned_data.get('phone','')
            Client.objects.create(user=user,national_id=national,phone=phone)
            messages.success(request,'Account created. Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request,'register.html',{'form':form})

def user_login(request):
    if request.method=='POST':
        uname = request.POST.get('username'); pwd=request.POST.get('password')
        user = authenticate(request, username=uname, password=pwd)
        if user:
            login(request,user); return redirect('user_dashboard')
        else:
            messages.error(request,'Invalid credentials')
    return render(request,'login.html')

def user_logout(request):
    logout(request); return redirect('home')

@login_required
def apply_loan(request):
    if request.method=='POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            client = Client.objects.filter(user=request.user).first()
            app = form.save(commit=False)
            app.client = client
            app.save()
            # create notification and send email to admin
            msg = f'New loan #{app.id} by {client} - Amount: {app.amount}'
            Notification.objects.create(loan=app, message=msg)
            # send email (console backend will print in dev)
            send_mail(
                subject=f'New Loan Application - {client}',
                message=msg + f'\nView in admin dashboard: /admin-dashboard/',
                from_email=None,
                recipient_list=[settings.ADMIN_EMAIL]
            )
            messages.success(request,'Application submitted. Admin notified.')
            return redirect('user_dashboard')
    else:
        form = LoanApplicationForm()
    return render(request,'apply.html',{'form':form})

@login_required
def user_dashboard(request):
    client = Client.objects.filter(user=request.user).first()
    apps = LoanApplication.objects.filter(client=client).order_by('-submitted_at')
    return render(request,'user_dashboard.html',{'apps':apps})

def staff_check(u):
    return u.is_staff

@login_required
@user_passes_test(staff_check)
def admin_dashboard(request):
    apps = LoanApplication.objects.order_by('-submitted_at')
    # notifications count (unread)
    notifs = Notification.objects.filter(read=False).order_by('-created_at')
    notif_count = notifs.count()
    labels = ['Approved','Assessed','Rejected','Submitted']
    data = [
        LoanApplication.objects.filter(status='approved').count(),
        LoanApplication.objects.filter(status='assessed').count(),
        LoanApplication.objects.filter(status='rejected').count(),
        LoanApplication.objects.filter(status='submitted').count(),
    ]
    return render(request,'admin_dashboard.html',{'apps':apps,'chart_labels':labels,'chart_data':data,'notif_count':notif_count,'notifs':notifs})

@login_required
@user_passes_test(staff_check)
def assess_application(request, app_id):
    app = get_object_or_404(LoanApplication, pk=app_id)
    if request.method=='POST':
        notes = request.POST.get('notes','')
        try:
            income = app.annual_income or Decimal('0')
            debt = app.existing_debt or Decimal('0')
            dti = (debt / (income + Decimal('0.01'))) * 100
            ratio = (app.amount / (income + Decimal('0.01'))) * 100
            term_factor = Decimal(app.term_months) * Decimal('0.1')
            score = float(ratio + dti + term_factor)
        except Exception:
            score = 999.0
        if score < 50: grade='A'
        elif score < 100: grade='B'
        elif score < 200: grade='C'
        else: grade='D'
        ra, created = RiskAssessment.objects.get_or_create(application=app, defaults={'score':score,'grade':grade,'assessed_by':request.user,'notes':notes})
        if not created:
            ra.score=score; ra.grade=grade; ra.assessed_by=request.user; ra.notes=notes; ra.save()
        app.status = 'approved' if grade in ['A','B'] else 'rejected'
        app.save()
        messages.success(request,f'Assessed: score={score:.2f}, grade={grade}')
        return redirect('admin_dashboard')
    return render(request,'assess.html',{'app':app})

@login_required
def pay_application(request, app_id):
    app = get_object_or_404(LoanApplication, pk=app_id)
    if request.method=='POST':
        gateway = request.POST.get('gateway')
        reference = str(uuid.uuid4())[:12]
        amount = app.amount
        Payment.objects.create(application=app,gateway=gateway,reference=reference,amount=amount)
        app.status = 'paid'
        app.save()
        messages.success(request,f'Payment received via {gateway}. Ref: {reference}')
        return redirect('user_dashboard')
    return render(request,'pay.html',{'app':app})

@login_required
@user_passes_test(staff_check)
def export_loans_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loans_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID','Client','Amount','Term','Status','Submitted At'])
    for a in LoanApplication.objects.all():
        writer.writerow([a.id,str(a.client),str(a.amount),a.term_months,a.status,a.submitted_at])
    return response

@login_required
@user_passes_test(staff_check)
def notifications_view(request):
    notifs = Notification.objects.order_by('-created_at')
    return render(request,'notifications.html',{'notifs':notifs})

@login_required
@user_passes_test(staff_check)
def mark_notification_read(request, notif_id):
    n = get_object_or_404(Notification, pk=notif_id)
    n.read = True
    n.save()
    return redirect('admin_dashboard')
