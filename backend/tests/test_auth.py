import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


class TestUserRegistration:
    """Тесты для регистрации пользователей"""
    
    def test_create_user_success(self, api_client, clear_test_users):
        """Тест успешной регистрации пользователя"""
        url = reverse('api:users-list')
        data = {
            "email": "vivanov@yandex.ru",
            "username": "vasya.ivanov",
            "first_name": "Вася",
            "last_name": "Иванов",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['username'] == 'vasya.ivanov'
        assert response.data['email'] == 'vivanov@yandex.ru'
        assert 'password' not in response.data
    
    def test_create_user_missing_email(self, api_client):
        """Тест регистрации без email"""
        url = reverse('api:users-list')
        data = {
            "username": "NoEmail",
            "first_name": "No",
            "last_name": "Email",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_user_missing_username(self, api_client):
        """Тест регистрации без username"""
        url = reverse('api:users-list')
        data = {
            "email": "no-username@user.ru",
            "first_name": "Username",
            "last_name": "NotProvided",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_user_with_invalid_username(self, api_client):
        """Тест регистрации с некорректным username"""
        url = reverse('api:users-list')
        data = {
            "email": "invalid-username@user.ru",
            "username": "InvalidU$ername",
            "first_name": "Invalid",
            "last_name": "Username",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_user_email_in_use(self, api_client, create_user):
        """Тест регистрации с уже используемым email"""
        # Сначала создаем пользователя
        create_user(
            username="vasya.ivanov",
            email="vivanov@yandex.ru",
            password="MySecretPas$word"
        )
        
        url = reverse('api:users-list')
        data = {
            "email": "vivanov@yandex.ru",
            "username": "EmailInUse",
            "first_name": "Email",
            "last_name": "InUse",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenAuthentication:
    """Тесты для получения токенов"""
    
    def test_get_token_success(self, api_client, create_user):
        """Тест успешного получения токена"""
        # Создаем пользователя
        user = create_user(
            username="vasya.ivanov",
            email="vivanov@yandex.ru",
            password="MySecretPas$word"
        )
        
        url = reverse('api:token-login')
        data = {
            "email": "vivanov@yandex.ru",
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'auth_token' in response.data
        assert isinstance(response.data['auth_token'], str)
    
    def test_get_token_wrong_password(self, api_client, create_user):
        """Тест получения токена с неверным паролем"""
        user = create_user(
            username="vasya.ivanov",
            email="vivanov@yandex.ru",
            password="MySecretPas$word"
        )
        
        url = reverse('api:token-login')
        data = {
            "email": "vivanov@yandex.ru",
            "password": "wrongpassword"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_token_no_email(self, api_client):
        """Тест получения токена без email"""
        url = reverse('api:token-login')
        data = {
            "password": "MySecretPas$word"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_logout_success(self, authenticated_client):
        """Тест успешного выхода из системы"""
        client, user = authenticated_client
        url = reverse('api:token-logout')
        
        response = client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT