from celery import shared_task
import csv
import io
import os
from django.conf import settings


@shared_task(bind=True)
def export_csv_task(self, user_id, params):
    """Generate and save a CSV export of transactions."""
    from apps.transactions.models import Transaction
    from apps.users.models import User

    try:
        user = User.objects.get(pk=user_id)
        qs = Transaction.objects.filter(user=user).select_related('account', 'category')

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Type', 'Amount', 'Currency', 'Description', 'Category', 'Account', 'Tags'])
        for tx in qs:
            writer.writerow([
                tx.date, tx.transaction_type, tx.amount, tx.currency,
                tx.description,
                tx.category.name if tx.category else '',
                tx.account.name,
                ','.join(tx.tags),
            ])

        # Save to media
        filename = f"exports/transactions_{user_id}_{self.request.id}.csv"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            f.write(output.getvalue())

        return {'status': 'done', 'file': f"/media/{filename}"}
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def export_pdf_task(self, user_id, params):
    """Generate a PDF financial summary report."""
    from apps.users.models import User
    from apps.transactions.models import Transaction
    from django.db.models import Sum
    from decimal import Decimal
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    import datetime

    try:
        user = User.objects.get(pk=user_id)
        filename = f"exports/report_{user_id}_{self.request.id}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Financial Report — {user.full_name}", styles['Title']))
        story.append(Paragraph(f"Generated: {datetime.date.today()}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Summary table
        today = datetime.date.today()
        month_start = today.replace(day=1)
        qs = Transaction.objects.filter(user=user, date__gte=month_start)
        income = qs.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or Decimal('0')
        expense = qs.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or Decimal('0')

        data = [['Metric', 'Amount'],
                ['Income (this month)', f"{user.currency_preference} {income:.2f}"],
                ['Expenses (this month)', f"{user.currency_preference} {expense:.2f}"],
                ['Net', f"{user.currency_preference} {income - expense:.2f}"]]

        table = Table(data, colWidths=[300, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F3F4')]),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        doc.build(story)
        return {'status': 'done', 'file': f"/media/{filename}"}
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task
def send_weekly_summary():
    """Every Monday: email weekly income/expense recap to all users."""
    from apps.users.models import User
    from apps.transactions.models import Transaction
    from django.db.models import Sum
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    import datetime
    from decimal import Decimal

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=7)

    for user in User.objects.filter(is_active=True, is_verified=True):
        qs = Transaction.objects.filter(user=user, date__gte=week_start, date__lte=today)
        income = qs.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or Decimal('0')
        expense = qs.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or Decimal('0')
        net = income - expense

        send_mail(
            subject=f"Your Weekly Finance Summary — {today.strftime('%b %d, %Y')}",
            message=(
                f"Hi {user.first_name},\n\n"
                f"Here's your week ({week_start} – {today}):\n\n"
                f"  Income:   {user.currency_preference} {income:.2f}\n"
                f"  Expenses: {user.currency_preference} {expense:.2f}\n"
                f"  Net:      {user.currency_preference} {net:.2f}\n\n"
                f"Keep track at http://localhost:8000/api/docs/\n"
            ),
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    return "Weekly summaries sent."
