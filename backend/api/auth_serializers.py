# backend/api/auth_serializers.py
from django.contrib.auth import authenticate
from rest_framework import serializers


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        request = self.context.get("request")
        user = authenticate(request=request, username=email, password=password)

        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )

        attrs["user"] = user
        return attrs
