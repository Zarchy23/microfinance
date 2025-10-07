# Smartmicro Finance - Django Prototype (v3)

Features:
- Professional landing page with hero image and brand "Smartmicro Finance"
- Two interfaces: Admin Dashboard (/admin-dashboard/) and User Dashboard (/dashboard/)
- Registration & authentication
- Validation: National ID, Phone, Email uniqueness
- Notification system (DB + email via console) for new loan submissions
- Mock EcoCash & Zipit payment buttons
- Chart.js visualizations and CSV export
- Console email backend by default (change settings.py for SMTP)

Run:
1. pip install -r requirements.txt
2. python manage.py migrate
3. python manage.py createsuperuser
4. python manage.py runserver
