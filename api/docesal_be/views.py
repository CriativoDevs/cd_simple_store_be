from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, views

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.conf import settings
from django.views.generic import View

import jwt
import time

from .models import Product
from .serializer import ProductSerializer, UserSerializer, UserSerializerWithToken
from .utils import generate_token, TokenGenerator


import threading


class TokenRefreshView(views.APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST
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
        self.email_message.send()


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
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        # Token is verified by the authentication_classes
        return Response({"detail": "Token is valid"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def getUsers(request):
    user = User.objects.all().order_by("-id")
    serializer = UserSerializer(user, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def getRoutes(request):
    return Response("Hello")


@api_view(["GET"])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def getProduct(request, pk):
    product = Product.objects.get(_id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(["POST"])
def registerUser(request):
    data = request.data
    try:
        user = User.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
            username=data["email"],
            email=data["email"],
            password=make_password(data["password"]),
            is_active=False,
        )

        # Will be here for and when I got a good email service
        # generate token for sending mail
        email_subject = "Activate your account"
        uid = force_text(urlsafe_base64_encode(force_bytes(user.pk)))
        token = generate_token.make_token(user)
        message = render_to_string(
            "activate.html",
            {
                "user": user,
                "domain": settings.HOST_URL,
                "uid": uid,
                "token": token,
            },
        )

        email_message = EmailMessage(
            email_subject,
            message,
            settings.EMAIL_HOST_USER,
            [data["email"]],
        )

        EmailThread(email_message).start()

        activation_message = {"detail": "Check your email for activation link"}

        return Response(activation_message, status=status.HTTP_201_CREATED)

        # serialize = UserSerializerWithToken(user, many=False)
        # return Response(serialize.data)
    except Exception as e:
        message = {"detail": "User with this email already exists"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            message = {"details": "Account Activated Sucessfylly"}
            return render(request, "activatesuccess.html", message)
        else:
            return render(request, "activatefail.html")
