import pytest
from rest_framework import status


class TestUserProfile:
    """Тесты для профиля пользователя"""
    
    def test_get_user_list_no_auth(self, api_client):
        """Тест получения списка пользователей без авторизации"""
        url = '/api/users/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
    
    def test_get_user_list_with_auth(self, authenticated_client):
        """Тест получения списка пользователей с авторизацией"""
        client, user = authenticated_client
        url = '/api/users/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
    
    def test_get_user_list_with_limit(self, authenticated_client):
        """Тест получения списка пользователей с limit параметром"""
        client, user = authenticated_client
        url = '/api/users/?limit=1'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) <= 1
    
    def test_get_user_profile_no_auth(self, api_client, create_user):
        """Тест получения профиля пользователя без авторизации"""
        user = create_user(username="testuser")
        url = f'/api/users/{user.id}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert 'is_subscribed' in response.data
    
    def test_get_current_user_profile(self, authenticated_client):
        """Тест получения профиля текущего пользователя"""
        client, user = authenticated_client
        url = '/api/users/me/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
        assert response.data['is_subscribed'] is False
    
    def test_get_current_user_no_auth(self, api_client):
        """Тест получения текущего пользователя без авторизации"""
        url = '/api/users/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_change_password_success(self, authenticated_client):
        """Тест успешной смены пароля"""
        client, user = authenticated_client
        url = '/api/users/set_password/'
        data = {
            "current_password": "testpass123",
            "new_password": "NewPassword123!"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_change_password_wrong_current(self, authenticated_client):
        """Тест смены пароля с неверным текущим паролем"""
        client, user = authenticated_client
        url = '/api/users/set_password/'
        data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123!"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST