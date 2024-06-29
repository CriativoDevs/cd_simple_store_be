from .models import Product, UserProfile, LogEntry

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User

import logging


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone_number", "address1", "address2"]


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    _id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "_id", "username", "email", "name", "isAdmin", "profile"]

    def get__id(self, obj):
        return obj.id

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        first_name = obj.first_name
        last_name = obj.last_name
        name = first_name + " " + last_name
        if name.strip() == "":
            name = obj.email

        return name

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        profile = instance.profile

        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()

        if profile_data:
            profile.phone_number = profile_data.get(
                "phone_number", profile.phone_number
            )
            profile.address1 = profile_data.get("address1", profile.address1)
            profile.address2 = profile_data.get("address2", profile.address2)
            profile.save()

        return instance


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "_id", "username", "email", "name", "isAdmin", "token"]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = LogEntry(
            level=record.levelname,
            message=record.getMessage(),
            module=record.module,
        )
        log_entry.save()
