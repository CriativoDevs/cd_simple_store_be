from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import six
import io
import datetime
import logging
import smtplib

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


logger = logging.getLogger(__name__)


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
    p.drawString(
        100, 580, "Thanks for purchasing with us. If you need anything, contact us."
    )
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


def send_email_with_pdf(to_email, subject, body, pdf_buffer):
    try:
        if settings.EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(
                settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT
            )
            logger.info("SSL connection established", server)
        else:
            server = smtplib.SMTP(
                settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT
            )
            logger.info("Else SSL connection established", server)
            server.ehlo()
            if settings.EMAIL_USE_TLS:
                server.starttls()
                server.ehlo()

        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("Email connection established")

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_HOST_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Attach the PDF file
        attach = MIMEApplication(pdf_buffer.getvalue(), _subtype="pdf")
        attach.add_header("Content-Disposition", "attachment", filename="receipt.pdf")
        msg.attach(attach)
        print("PDF attached successfully")

        # Send the email
        server.sendmail(settings.EMAIL_HOST_USER, to_email, msg.as_string())
        print("Email sent successfully")
        server.quit()
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"Error sending email: {e}")


logger.info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
logger.info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
logger.info(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
logger.info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
logger.info(f"EMAIL_HOST_PASSWORD: {settings.EMAIL_HOST_PASSWORD}")
