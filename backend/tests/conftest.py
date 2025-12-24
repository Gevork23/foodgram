import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User"
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
    return _create_user


@pytest.fixture
def get_token(db, create_user):
    def _get_token(user=None):
        if not user:
            user = create_user()
        token, _ = Token.objects.get_or_create(user=user)
        return token.key
    return _get_token


@pytest.fixture
def authenticated_client(api_client, create_user, get_token):
    user = create_user()
    token = get_token(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return api_client, user


@pytest.fixture
def clear_test_users(db):
    """Очистка тестовых пользователей перед тестами"""
    usernames_list = [
        'vasya.ivanov',
        'second-user',
        'third-user-username',
        'NoEmail',
        'NoFirstName',
        'NoLastName',
        'NoPassword',
        'TooLongEmail',
        'the-username-that-is-150-characters-long-and-should-not-pass-validation-if-the-serializer-is-configured-correctly-otherwise-the-current-test-will-fail-',
        'TooLongFirstName',
        'TooLongLastName',
        'InvalidU$ername',
        'EmailInUse'
    ]
    User.objects.filter(username__in=usernames_list).delete()
    yield
    # Очистка после тестов (если нужно)
    User.objects.filter(username__in=usernames_list).delete()