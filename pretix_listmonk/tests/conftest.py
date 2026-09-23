"""
Configure Django before the tests import the plugin.

Run them from inside a pretix container, which ships ``pretix.testutils.settings``::

    docker exec -w /plugins/pretix-listmonk pretix-dev \
        python -m pytest -q -p no:cacheprovider pretix_listmonk/tests/
"""
import os
from datetime import datetime, timezone as dt_timezone

import pytest


def pytest_configure(config):  # noqa: ARG001
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pretix.testutils.settings")
    import django

    django.setup()


@pytest.fixture
def organizer(db):
    from django_scopes import scopes_disabled
    from pretix.base.models import Organizer

    with scopes_disabled():
        return Organizer.objects.create(name="Test org", slug="listmonk-test")


@pytest.fixture
def event(db, organizer):
    from django_scopes import scopes_disabled
    from pretix.base.models import Event

    with scopes_disabled():
        event = Event.objects.create(
            organizer=organizer,
            name="Test event",
            slug="listmonk-event",
            date_from=datetime(2026, 12, 31, 19, 0, tzinfo=dt_timezone.utc),
            live=False,
            plugins="pretix_listmonk",
        )
        event.settings.set("timezone", "Europe/Paris")
        return event


def _user_in_team(organizer, email, permissions):
    """Create a user in a team holding exactly ``permissions``."""
    from django_scopes import scopes_disabled
    from pretix.base.models import Team, User

    with scopes_disabled():
        user = User.objects.create_user(email=email, password="dummy-password-for-tests")
        kwargs = {"organizer": organizer, "name": f"Team {email}", "all_events": True}
        field_names = {f.name for f in Team._meta.get_fields()}
        if "limit_event_permissions" in field_names:
            kwargs["all_event_permissions"] = False
            kwargs["limit_event_permissions"] = {p: True for p in permissions}
        else:  # pretix < 2026.5
            for p in permissions:
                kwargs[p] = True
        team = Team.objects.create(**kwargs)
        team.members.add(user)
        return user


@pytest.fixture
def settings_admin(db, organizer):
    """A user allowed to change event settings."""
    return _user_in_team(organizer, "admin@example.invalid", ["event.settings.general:write"])


@pytest.fixture
def orders_only_user(db, organizer):
    """A team member who may only read orders — no settings permission at all."""
    return _user_in_team(organizer, "orders@example.invalid", ["event.orders:read"])
