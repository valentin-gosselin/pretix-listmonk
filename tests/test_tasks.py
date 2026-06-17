import pytest
import responses
import socket
from django.utils.timezone import now
from unittest.mock import patch

from pretix.base.models import Event, Organizer
from pretix_listmonk.tasks import subscribe_to_listmonk


@pytest.mark.django_db
def test_incomplete_config():
    # Setup Organizer and Event
    o = Organizer.objects.create(name='Org', slug='org')
    e = Event.objects.create(organizer=o, name='Event', slug='event', date_from=now(), live=True)

    # Incomplete settings: listmonk_url missing
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')

    with patch('pretix_listmonk.tasks.logger') as mock_logger:
        subscribe_to_listmonk('test@example.com', 'Name', 'event', 'org', 'ORDER123')
        mock_logger.warning.assert_any_call(
            'pretix-listmonk: incomplete configuration for event %s, skipping', 'event'
        )


@pytest.mark.django_db
def test_unsafe_url():
    o = Organizer.objects.create(name='Org', slug='org')
    e = Event.objects.create(organizer=o, name='Event', slug='event', date_from=now(), live=True)

    o.settings.set('listmonk_url', 'https://127.0.0.1')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')

    with patch('socket.getaddrinfo') as mock_getaddrinfo, patch('pretix_listmonk.tasks.logger') as mock_logger:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))
        ]
        subscribe_to_listmonk('test@example.com', 'Name', 'event', 'org', 'ORDER123')
        mock_logger.warning.assert_any_call(
            'pretix-listmonk: URL validation failed for event %s, skipping', 'event'
        )


@pytest.mark.django_db
@responses.activate
def test_subscribe_success_double_optin_false():
    o = Organizer.objects.create(name='Org', slug='org')
    e = Event.objects.create(organizer=o, name='Event', slug='event', date_from=now(), live=True)

    o.settings.set('listmonk_url', 'https://newsletter.example.com')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')
    o.settings.set('listmonk_double_optin', False)

    responses.add(
        responses.POST,
        'https://newsletter.example.com/api/subscribers',
        json={'data': {'id': 42}},
        status=200
    )

    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))
        ]
        subscribe_to_listmonk('test@example.com', 'John Doe', 'event', 'org', 'ORDER123')

    assert len(responses.calls) == 1
    import json
    req_body = json.loads(responses.calls[0].request.body)
    assert req_body['email'] == 'test@example.com'
    assert req_body['name'] == 'John Doe'
    assert req_body['preconfirm_subscriptions'] is True
    assert req_body['lists'] == [12]
    assert req_body['attribs'] == {
        'source': 'pretix',
        'event': 'event',
        'order_code': 'ORDER123'
    }


@pytest.mark.django_db
@responses.activate
def test_subscribe_success_double_optin_true():
    o = Organizer.objects.create(name='Org', slug='org')
    e = Event.objects.create(organizer=o, name='Event', slug='event', date_from=now(), live=True)

    o.settings.set('listmonk_url', 'https://newsletter.example.com')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')
    o.settings.set('listmonk_double_optin', True)

    responses.add(
        responses.POST,
        'https://newsletter.example.com/api/subscribers',
        json={'data': {'id': 42}},
        status=200
    )

    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))
        ]
        subscribe_to_listmonk('test@example.com', 'John Doe', 'event', 'org', 'ORDER123')

    assert len(responses.calls) == 1
    import json
    req_body = json.loads(responses.calls[0].request.body)
    assert req_body['preconfirm_subscriptions'] is False



@pytest.mark.django_db
@responses.activate
def test_subscriber_already_exists_success():
    o = Organizer.objects.create(name='Org', slug='org')
    e = Event.objects.create(organizer=o, name='Event', slug='event', date_from=now(), live=True)

    o.settings.set('listmonk_url', 'https://newsletter.example.com')
    o.settings.set('listmonk_api_user', 'user')
    o.settings.set('listmonk_api_password', 'password')
    o.settings.set('listmonk_list_id', '12')

    # Mock POST to create returning 409 (Conflict)
    responses.add(
        responses.POST,
        'https://newsletter.example.com/api/subscribers',
        json={'message': 'subscriber already exists'},
        status=409
    )

    # Mock GET search query
    responses.add(
        responses.GET,
        'https://newsletter.example.com/api/subscribers',
        json={'data': {'results': [{'id': 42}]}},
        status=200
    )

    # Mock PUT add to list
    responses.add(
        responses.PUT,
        'https://newsletter.example.com/api/subscribers/lists',
        json={'data': True},
        status=200
    )

    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))
        ]
        subscribe_to_listmonk("john'o@example.com", "John O'Connor", 'event', 'org', 'ORDER123')

    # Verify requests
    assert len(responses.calls) == 3

    # Check SQL injection escaping in GET query param
    get_call = responses.calls[1]
    query_param = get_call.request.params['query']
    # 'john\'o@example.com' should be escaped to "subscribers.email = 'john''o@example.com'"
    assert query_param == "subscribers.email = 'john''o@example.com'"


