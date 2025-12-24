import pytest
from rest_framework import status


class TestTags:
    """Тесты для тегов"""
    
    def test_get_tags_list_no_auth(self, api_client):
        """Тест получения списка тегов без авторизации"""
        url = '/api/tags/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_get_tags_list_with_auth(self, authenticated_client):
        """Тест получения списка тегов с авторизацией"""
        client, user = authenticated_client
        url = '/api/tags/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_get_tag_detail(self, api_client):
        """Тест получения детальной информации о теге"""
        # Сначала нужно получить список тегов
        url = '/api/tags/'
        response_list = api_client.get(url)
        
        if response_list.data:
            tag_id = response_list.data[0]['id']
            url_detail = f'/api/tags/{tag_id}/'
            response_detail = api_client.get(url_detail)
            assert response_detail.status_code == status.HTTP_200_OK
            assert 'id' in response_detail.data
            assert 'name' in response_detail.data
            assert 'slug' in response_detail.data
    
    def test_create_tag_not_allowed(self, authenticated_client):
        """Тест создания тега (не должно быть разрешено)"""
        client, user = authenticated_client
        url = '/api/tags/'
        data = {
            "name": "Завтрак",
            "slug": "breakfast"
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED