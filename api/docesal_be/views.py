from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, views, generics, filters, pagination

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import (
    force_bytes,
    force_text,
    DjangoUnicodeDecodeError,
    force_str,
)
from django.conf import settings
from django.views.generic import View
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse

import jwt
import time

from .models import Product, Purchase
from .serializer import ProductSerializer, UserSerializer, UserSerializerWithToken
from .utils import (
    generate_token,
    TokenGenerator,
    send_email_with_pdf,
    generate_purchase_pdf,
)
from smtplib import SMTPException

import threading
import stripe

import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class TokenRefreshView(views.APIView):
    authentication_classes = [
        JWTAuthentication,
    ]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        print("REFRESH: ", refresh_token)

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            print("REFRESH: ", refresh)
            access_token = str(refresh.access_token)

            print("ACCESS: ", access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Invalid refresh token: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["POST"])
def refresh_token(request):
    token = request.headers.get("Authorization").split(" ")[
        1
    ]  # Extract the token from the Authorization header

    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # Check if the token is expired
        if decoded_token["exp"] < time.time():
            # Generate a new token
            new_token = jwt.encode(
                {
                    "user_id": decoded_token["user_id"],
                    "exp": time.time() + settings.JWT_EXPIRATION_DELTA,
                },
                settings.SECRET_KEY,
                algorithm="HS256",
            )
            return Response({"access_token": new_token}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Token is not expired"}, status=status.HTTP_400_BAD_REQUEST
            )
    except jwt.ExpiredSignatureError:
        return Response(
            {"error": "Token is expired"}, status=status.HTTP_400_BAD_REQUEST
        )
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class EmailThread(threading.Thread):
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.email_message.send()
                logger.info("Email sent successfully.")
                break
            except SMTPException as e:
                logger.error(f"Attempt {attempt + 1} to send email failed: {e}")
                if attempt + 1 == max_retries:
                    logger.error("All attempts to send email failed.")
                else:
                    logger.info("Retrying...")


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        serializer = UserSerializerWithToken(self.user).data

        for k, v in serializer.items():
            data[k] = v

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class TokenVerificationView(views.APIView):
    authentication_classes = [
        JWTAuthentication,
    ]

    def get(self, request):
        # Token is verified by the authentication_classes
        return Response({"detail": "Token is valid"}, status=status.HTTP_200_OK)


class GetUserProfile(views.APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        user = request.user
        token = request.headers.get("Authorization")
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class GetUsers(generics.ListAPIView):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


@api_view(["GET"])
def getRoutes(request):
    return Response("Hello")


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    pagination_class = pagination.PageNumberPagination
    search_fields = ["product_name", "product_brand", "product_description"]
    permission_classes = []

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.query_params.get("search", None)
        if search_term:
            queryset = queryset.filter(
                Q(product_name__icontains=search_term)
                | Q(product_brand__icontains=search_term)
                | Q(product_description__icontains=search_term)
            )
        return queryset


class ProductDetail(generics.RetrieveAPIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )


class RegisterUser(views.APIView):
    def post(self, request):
        data = request.data
        try:
            if User.objects.filter(username=data["email"]).exists():
                message = {"detail": "A user with this email already exists."}
                logger.error(f"Error creating user: {message}")
                return Response(message, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                user = User.objects.create(
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    username=data["email"],
                    email=data["email"],
                    password=make_password(data["password"]),
                    is_active=False,
                )

                logger.info(f"User created: {user}")

                email_subject = "Activate your account"
                uid = force_str(urlsafe_base64_encode(force_bytes(user.pk)))
                token = generate_token.make_token(user)

                domain = settings.HOST_URL

                message = render_to_string(
                    "activate.html",
                    {
                        "user": user,
                        "domain": domain,
                        "uid": uid,
                        "token": token,
                    },
                )
                logger.info(
                    f"The message is: {message}, Email subject: {email_subject}"
                )

                # Create a plain text message for email clients that don't support HTML
                text_message = f"""
                Hi {user.first_name} {user.last_name},

                Please click the link below to verify your account:

                http://{domain}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}
                """

                email_message = EmailMultiAlternatives(
                    email_subject,
                    text_message,
                    settings.EMAIL_HOST_USER,
                    [data["email"]],
                )
                email_message.attach_alternative(message, "text/html")
                email_message.send()
                logger.info(f"Email sent: {email_message}")

            activation_message = {"detail": "Check your email for activation link"}
            logger.info(f"Activation message: {activation_message}")

            return Response(activation_message, status=status.HTTP_201_CREATED)

        except Exception as e:
            message = {"detail": f"{str(e)}"}
            logger.error(f"Error creating user: {str(e)}")
            return Response(message, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            logger.info(f"User: {user}")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            logger.info(f"User: {user}")

        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            return render(
                request, "activatesuccess.html", {"domain": settings.HOST_URL}
            )
        else:
            return render(request, "activatefail.html")


class PasswordResetRequestView(views.APIView):
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.HOST_FE_URL}/reset-password/{uid}/{token}"
            logger.info(f"Reset link: {reset_link}")

            context = {
                "user": user,
                "link": reset_link,
            }

            message = render_to_string("password_reset.html", context)
            email_subject = "Password Reset Request"

            # Create a plain text message for email clients that don't support HTML
            text_message = f"""
            Hi {user.first_name},

            Please click the link below to reset your password:

            {reset_link}
            """

            email_message = EmailMultiAlternatives(
                email_subject,
                text_message,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email_message.attach_alternative(message, "text/html")

            # Send email in a thread
            EmailThread(email_message).start()
            logger.info(f"Email sent: {email_message}")

            return Response(
                {"detail": "Password reset email sent."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetConfirmView(views.APIView):

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            with transaction.atomic():
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = f"{settings.HOST_FE_URL}/reset-password/{uid}/{token}"
                logger.info(f"Reset link: {reset_link}")

                context = {
                    "user": user,
                    "link": reset_link,
                }

                message = render_to_string("password_reset.html", context)
                email_subject = "Password Reset Request"

                # Create a plain text message for email clients that don't support HTML
                text_message = f"""
                Hi {user.first_name},

                Please click the link below to reset your password:

                {reset_link}
                """

                email_message = EmailMultiAlternatives(
                    email_subject,
                    text_message,
                    settings.EMAIL_HOST_USER,
                    [email],
                )
                email_message.attach_alternative(message, "text/html")
                email_message.send()

                logger.info(f"Email sent: {email_message}")

            return Response(
                {"detail": "Password reset email sent."}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error during password reset email process: {str(e)}")
            return Response(
                {"detail": "An error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreatePaymentIntent(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if not user.is_authenticated:
                return Response(
                    {"error": "User is not authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            cart_items = request.data.get("cartItems", [])
            amount = sum(
                int(float(item["price"]) * 100) * item["qty"] for item in cart_items
            )

            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="eur",
            )

            for item in cart_items:
                try:
                    product = get_object_or_404(Product, _id=item["product"])
                    Purchase.objects.create(
                        user=user,
                        product=product,
                        quantity=item["qty"],
                        was_bought=True,
                    )
                except Exception as e:
                    logger.error(f"Error processing cart item: {item}, Error: {str(e)}")
                    return Response(
                        {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )

            try:
                # Generate the PDF
                pdf_buffer = generate_purchase_pdf(user, cart_items)
            except Exception as e:
                logger.error(f"Error generating PDF: {str(e)}")
                return Response(
                    {"error": f"Error generating PDF: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                # Email details
                subject = "Purchase Confirmation"
                body = "Thank you for your purchase!"

                # Send email with PDF
                send_email_with_pdf(user.email, subject, body, pdf_buffer)
                logger.info("Email sent to {}".format(user.email))
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                return Response(
                    {"error": f"Error sending email: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"clientSecret": intent["client_secret"]}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"General error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_purchase_status(request, product_id):
    user = request.user
    product = get_object_or_404(Product, _id=product_id)
    has_bought = Purchase.objects.filter(
        user=user, product=product, was_bought=True
    ).exists()
    return Response({"has_bought": has_bought})
