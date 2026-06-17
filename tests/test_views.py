import pytest
from unittest.mock import patch
from django.core.cache import cache
from django.test import RequestFactory

from pretix.base.models import Organizer
from pretix_listmonk.views import ListmonkOrganizerSettingsView


@pytest.mark.django_db
def test_get_list_choices_instance_cache():
    o = Organizer.objects.create(name='Org', slug='org')
    o.settings.set('listmonk_url', 'https://newsletter.example.com')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')

    request = RequestFactory().get('/settings/')
    request.organizer = o

    view = ListmonkOrganizerSettingsView()
    view.request = request

    with patch('pretix_listmonk.views._fetch_listmonk_lists') as mock_fetch:
        mock_fetch.return_value = [('1', 'List 1')]

        # Clear cache first
        cache_key = f'pretix_listmonk_lists_{o.slug}'
        cache.delete(cache_key)

        # Force refresh to populate cache
        request.GET = {'refresh': '1'}
        choices1 = view._get_list_choices()
        assert choices1 == [('1', 'List 1')]
        assert mock_fetch.call_count == 1

        # Second call in same request lifecycle: should hit instance cache
        choices2 = view._get_list_choices()
        assert choices2 == [('1', 'List 1')]
        assert mock_fetch.call_count == 1


@pytest.mark.django_db
def test_get_list_choices_no_fetch_on_standard_get():
    o = Organizer.objects.create(name='Org', slug='org')
    o.settings.set('listmonk_url', 'https://newsletter.example.com')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')

    request = RequestFactory().get('/settings/')  # No ?refresh=1
    request.organizer = o

    view = ListmonkOrganizerSettingsView()
    view.request = request

    # Clear cache
    cache_key = f'pretix_listmonk_lists_{o.slug}'
    cache.delete(cache_key)

    with patch('pretix_listmonk.views._fetch_listmonk_lists') as mock_fetch:
        choices = view._get_list_choices()
        # Should not fetch from Listmonk on standard GET if cache is empty
        assert mock_fetch.call_count == 0
        # Should return fallback choices (saved list ID)
        assert choices == [('12', 'Current List (ID 12)')]
