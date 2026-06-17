import logging

import requests
from celery import shared_task
from django.conf import settings as django_settings

from .security import is_safe_listmonk_url

logger = logging.getLogger(__name__)

LISTMONK_TIMEOUT = 10  # seconds


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def subscribe_to_listmonk(self, email, name, event_slug, organizer_slug, order_code):
    """Subscribe a user to a Listmonk list. Retries up to 3 times on failure."""
    from django_scopes import scopes_disabled
    from pretix.base.models import Event, Organizer

    try:
        with scopes_disabled():
            organizer = Organizer.objects.get(slug=organizer_slug)
            event = Event.objects.get(slug=event_slug, organizer=organizer)
    except Exception as e:
        logger.error('pretix-listmonk: could not load event %s/%s: %s', organizer_slug, event_slug, e)
        return

    base_url = organizer.settings.get('listmonk_url', '').rstrip('/')
    api_user = organizer.settings.get('listmonk_api_user', '')
    api_password = organizer.settings.get('listmonk_api_password', '')
    list_id = organizer.settings.get('listmonk_list_id', '')
    double_optin = organizer.settings.get('listmonk_double_optin', as_type=bool)

    if not all([base_url, api_user, api_password, list_id]):
        logger.warning('pretix-listmonk: incomplete configuration for event %s, skipping', event_slug)
        return

    if not is_safe_listmonk_url(base_url):
        logger.warning('pretix-listmonk: URL validation failed for event %s, skipping', event_slug)
        return

    try:
        list_id = int(list_id)
    except ValueError:
        logger.error('pretix-listmonk: listmonk_list_id is not a valid integer: %s', list_id)
        return

    auth = (api_user, api_password)
    subscriber_id = _get_or_create_subscriber(
        base_url, auth, email, name, list_id, event_slug, order_code, double_optin
    )

    if subscriber_id:
        logger.info('pretix-listmonk: subscribed order %s to list %s', order_code, list_id)


def _get_or_create_subscriber(base_url, auth, email, name, list_id, event_slug, order_code, double_optin):
    """Create subscriber, or add to list if already exists."""
    payload = {
        'email': email,
        'name': name,
        'status': 'enabled',
        'lists': [list_id],
        'preconfirm_subscriptions': not double_optin,
        'attribs': {
            'source': 'pretix',
            'event': event_slug,
            'order_code': order_code,
        },
    }

    try:
        resp = requests.post(
            f'{base_url}/api/subscribers',
            json=payload,
            auth=auth,
            timeout=LISTMONK_TIMEOUT,
        )

        if resp.status_code == 200:
            return resp.json()['data']['id']

        # Email already exists — fetch the subscriber and add to list
        if resp.status_code in (400, 409):
            return _add_existing_subscriber_to_list(base_url, auth, email, list_id, order_code)

        logger.error('pretix-listmonk: unexpected status %s: %s', resp.status_code, resp.text)

    except requests.RequestException as e:
        logger.error('pretix-listmonk: API request failed: %s', e)
        raise  # triggers Celery retry

    return None


def _add_existing_subscriber_to_list(base_url, auth, email, list_id, order_code):
    """Find an existing subscriber by email and add them to the list."""
    # Escape backslashes and single quotes to prevent SQL injection in Listmonk query syntax
    escaped_email = email.replace('\\', '\\\\').replace("'", "''")
    try:
        resp = requests.get(
            f'{base_url}/api/subscribers',
            params={'query': f"subscribers.email = '{escaped_email}'"},
            auth=auth,
            timeout=LISTMONK_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get('data', {}).get('results', [])
        if not results:
            logger.warning('pretix-listmonk: could not find existing subscriber for order %s', order_code)
            return None

        subscriber_id = results[0]['id']

        put_resp = requests.put(
            f'{base_url}/api/subscribers/lists',
            json={
                'ids': [subscriber_id],
                'action': 'add',
                'target_list_ids': [list_id],
                'status': 'confirmed',
            },
            auth=auth,
            timeout=LISTMONK_TIMEOUT,
        )
        put_resp.raise_for_status()
        return subscriber_id

    except requests.RequestException as e:
        logger.error('pretix-listmonk: failed to add existing subscriber to list: %s', e)
        return None

