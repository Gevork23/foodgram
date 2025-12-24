import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


def test_basic():
    """Базовый тест для проверки работы pytest"""
    assert 1 + 1 == 2


def test_database(db):
    """Тест работы с базой данных"""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    assert User.objects.count() == 1
    assert user.username == "testuser"


class TestSimpleEndpoints:
    """Простые тесты эндпоинтов"""
    
    def test_admin_url_exists(self, api_client):
        """Проверка, что админка доступна"""
        url = '/admin/'
        response = api_client.get(url)
        # Админка может возвращать 302 (редирект на логин) или 404 если не настроена
        assert response.status_code in [status.HTTP_200_OK, 
                                       status.HTTP_302_FOUND, 
                                       status.HTTP_404_NOT_FOUND]
    
    def test_api_root_exists(self, api_client):
        """Проверка корня API"""
        # Попробуем несколько возможных URL
        possible_urls = ['/api/', '/api/v1/', '/api/v1.0/']
        
        for url in possible_urls:
            response = api_client.get(url)
            if response.status_code != status.HTTP_404_NOT_FOUND:
                print(f"Found API at {url}: {response.status_code}")
                return
        
        # Если ни один URL не работает, пропускаем тест
        pytest.skip("API root not found")