from django.contrib.auth.tokens import PasswordResetTokenGenerator

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from dotenv import load_dotenv

import six
import io
import datetime
import logging
import smtplib
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


logger = logging.getLogger(__name__)
load_dotenv()


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


# Email settings
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false") == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


def send_email_with_pdf(user_email, pdf_buffer):
    try:
        logger.info("Setting up email connection using SSL")

        server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        logger.info("SSL connection established")

        logger.info("Logging in to the email server")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        logger.info("Logged in to the email server")

        msg = MIMEMultipart()
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = user_email
        msg["Subject"] = "CD Simple Store - Purchase Confirmation"

        body = "Purchase Confirmation"
        msg.attach(MIMEText(body, "plain"))

        # Attach the PDF
        attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename="purchase_details.pdf"
        )
        msg.attach(attachment)

        logger.info(f"Attempting to send email to {user_email}")

        server.send_message(msg)

        logger.info("Email sent successfully")
        server.quit()
        logger.info("Email connection closed")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {str(e)}")
        raise
