from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.conf import settings

import six
import io
import datetime
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
        )


generate_token = TokenGenerator()


def generate_purchase_pdf(user, cart_items):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 14)

    # Title
    p.drawString(100, 600, f"CD Simple Store - {user.username}")

    # Greeting and Contact Info
    p.setFont("Helvetica", 12)
    p.drawString(100, 580, "Thanks for purchasing with us. If you need anything, contact us.")
    p.drawString(100, 565, "Below you can see what you purchased.")
    
    # Date
    now = datetime.datetime.now()
    p.drawString(100, 545, f"Date: {now.strftime('%d/%m/%Y %H:%M:%S')}")

    # User Info
    p.drawString(100, 530, f"User: {user.username}")

    # Table Header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 500, "Product")
    p.drawString(250, 500, "Quantity")
    p.drawString(350, 500, "Price")
    p.setFont("Helvetica", 12)

    # Table Body
    y = 480
    for item in cart_items:
        p.drawString(100, y, item["name"])
        p.drawString(250, y, str(item["qty"]))
        p.drawString(350, y, f"€{item['price']}")
        y -= 20

    # Draw line
    p.line(100, y, 400, y)

    # Total Amount
    total_amount = sum(float(item["price"]) * item["qty"] for item in cart_items)
    p.drawString(100, y - 20, f"Total: €{total_amount}")

    p.showPage()
    p.save()

    buffer.seek(0)

    return buffer


def send_email_with_pdf(user_email, pdf_buffer):
    email = EmailMessage(
        "CD Simple Store - Purchase Confirmation",
        "Purchase Confirmation",
        settings.EMAIL_HOST_USER,
        [user_email],
    )
    email.attach("purchase_details.pdf", pdf_buffer.getvalue(), "application/pdf")
    email.send()
