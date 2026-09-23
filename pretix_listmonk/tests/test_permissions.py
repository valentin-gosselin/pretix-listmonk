"""
Access control on the plugin's settings views.

Regression tests for the hole fixed in 1.0.1: ``ListmonkEventSettingsView``
declared ``permission = 'can_change_event_settings'`` but inherited only from
``EventSettingsViewMixin``, which just adds a context variable and enforces
nothing. Any team member with access to the event — including one who could
only read orders — was able to read and change the Listmonk settings.
"""
import re

import pytest
from django.test import Client
from django_scopes import scopes_disabled


def base_url(event):
    return f"/control/event/{event.organizer.slug}/{event.slug}"


def csrf_token(html):
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    return match.group(1) if match else None


def stored_label(event):
    from pretix.base.models import Event

    with scopes_disabled():
        return Event.objects.get(pk=event.pk).settings.get("listmonk_checkbox_label")


@pytest.mark.django_db
def test_event_settings_are_refused_without_the_settings_permission(
    event, orders_only_user
):
    client = Client()
    client.force_login(orders_only_user)

    response = client.get(f"{base_url(event)}/settings/listmonk/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_event_settings_cannot_be_written_without_the_settings_permission(
    event, orders_only_user
):
    client = Client()
    client.force_login(orders_only_user)

    response = client.post(
        f"{base_url(event)}/settings/listmonk/",
        {"listmonk_checkbox_label": "written by an unauthorised user"},
    )

    assert response.status_code == 403
    assert stored_label(event) != "written by an unauthorised user"


@pytest.mark.django_db
def test_event_settings_stay_usable_for_an_authorised_user(event, settings_admin):
    client = Client()
    client.force_login(settings_admin)

    page = client.get(f"{base_url(event)}/settings/listmonk/")
    assert page.status_code == 200

    response = client.post(
        f"{base_url(event)}/settings/listmonk/",
        {
            "csrfmiddlewaretoken": csrf_token(page.content.decode()),
            "listmonk_checkbox_label": "Subscribe me",
        },
    )

    assert response.status_code == 302
    assert stored_label(event) == "Subscribe me"


@pytest.mark.django_db
def test_settings_tab_is_hidden_from_unauthorised_users(event, orders_only_user):
    client = Client()
    client.force_login(orders_only_user)

    body = client.get(f"{base_url(event)}/settings/").content.decode()

    assert "/settings/listmonk/" not in body


@pytest.mark.django_db
def test_organizer_settings_are_refused_without_the_organizer_permission(
    organizer, orders_only_user
):
    client = Client()
    client.force_login(orders_only_user)

    response = client.get(f"/control/organizer/{organizer.slug}/settings/listmonk/")

    assert response.status_code == 403
