import socket
import pytest
from unittest.mock import patch

from pretix.base.models import Organizer
from pretix_listmonk.forms import ListmonkOrganizerSettingsForm


@pytest.mark.django_db
def test_form_password_required_when_not_saved():
    o = Organizer.objects.create(name='Org', slug='org')

    # Form without password should be invalid
    form_data = {
        'listmonk_url': 'https://newsletter.example.com',
        'listmonk_api_user': 'user',
        'listmonk_api_password': '',
        'listmonk_list_id': '1',
        'listmonk_trigger': 'order_placed',
    }
    form = ListmonkOrganizerSettingsForm(
        data=form_data,
        list_choices=[('1', 'List 1')],
        organizer=o
    )
    assert form.is_valid() is False
    assert 'listmonk_api_password' in form.errors


@pytest.mark.django_db
def test_form_password_optional_when_already_saved():
    o = Organizer.objects.create(name='Org', slug='org')
    o.settings.set('listmonk_api_password', 'stored_password')

    form_data = {
        'listmonk_url': 'https://newsletter.example.com',
        'listmonk_api_user': 'user',
        'listmonk_api_password': '',
        'listmonk_list_id': '1',
        'listmonk_trigger': 'order_placed',
    }
    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))
        ]
        form = ListmonkOrganizerSettingsForm(
            data=form_data,
            list_choices=[('1', 'List 1')],
            organizer=o
        )
        assert form.is_valid() is True


@pytest.mark.django_db
def test_form_invalid_url_rejected():
    o = Organizer.objects.create(name='Org', slug='org')

    form_data = {
        'listmonk_url': 'http://newsletter.example.com',  # HTTP instead of HTTPS
        'listmonk_api_user': 'user',
        'listmonk_api_password': 'password',
        'listmonk_list_id': '1',
        'listmonk_trigger': 'order_placed',
    }
    form = ListmonkOrganizerSettingsForm(
        data=form_data,
        list_choices=[('1', 'List 1')],
        organizer=o
    )
    assert form.is_valid() is False
    assert 'listmonk_url' in form.errors
