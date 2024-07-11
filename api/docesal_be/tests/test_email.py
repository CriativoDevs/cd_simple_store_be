import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Email settings
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false") == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")


def send_test_email():
    try:
        logger.error("Setting up email connection")

        if EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()

        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        msg = MIMEMultipart()
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = "ipizette@icloud.com"  # Replace with your email for testing
        msg["Subject"] = "Test Email - Purchase Confirmation"

        body = "This is a test email for purchase confirmation."
        msg.attach(MIMEText(body, "plain"))

        # Assuming pdf_buffer is a BytesIO object, as in your original function
        pdf_buffer = b"%PDF-1.4 test pdf content"  # Dummy PDF content for testing
        attachment = MIMEApplication(pdf_buffer, _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename="purchase_details.pdf"
        )
        msg.attach(attachment)

        logger.error(f"Attempting to send test email to ipizette@icloud.com")

        server.send_message(msg)

        server.quit()
        logger.error("Email successfully sent and connection closed")
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")


if __name__ == "__main__":
    send_test_email()
