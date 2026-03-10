import json
import logging

from django import forms
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pretix.base.signals import order_paid, order_placed
from pretix.control.signals import nav_event, nav_organizer
from pretix.presale.signals import contact_form_fields

logger = logging.getLogger(__name__)

DEFAULT_LABEL = _('I would like to subscribe to the newsletter')


# ---------------------------------------------------------------------------
# Checkout: inject newsletter consent checkbox
# ---------------------------------------------------------------------------

@receiver(contact_form_fields, dispatch_uid='pretix_listmonk_contact_field')
def add_newsletter_field(sender, **kwargs):
    if not _plugin_is_active(sender):
        return {}

    # Label: event-level override, falls back to organizer default
    label = (
        sender.settings.get('listmonk_checkbox_label')
        or DEFAULT_LABEL
    )
    return {
        'listmonk_newsletter_consent': forms.BooleanField(
            label=label,
            required=False,
        )
    }


# ---------------------------------------------------------------------------
# Order signals
# ---------------------------------------------------------------------------

@receiver(order_placed, dispatch_uid='pretix_listmonk_order_placed')
def on_order_placed(sender, order, **kwargs):
    if not _plugin_is_active(sender):
        return
    trigger = sender.organizer.settings.get('listmonk_trigger', default='order_placed')
    if trigger != 'order_placed':
        return
    _maybe_subscribe(sender, order)


@receiver(order_paid, dispatch_uid='pretix_listmonk_order_paid')
def on_order_paid(sender, order, **kwargs):
    if not _plugin_is_active(sender):
        return
    trigger = sender.organizer.settings.get('listmonk_trigger', default='order_placed')
    if trigger != 'order_paid':
        return
    _maybe_subscribe(sender, order)


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

@receiver(nav_organizer, dispatch_uid='pretix_listmonk_nav_organizer')
def control_nav_organizer(sender, request=None, **kwargs):
    if not request.user.has_organizer_permission(
        request.organizer, 'can_change_organizer_settings', request=request
    ):
        return []
    return [{
        'label': _('Listmonk Newsletter'),
        'icon': 'envelope',
        'url': reverse('plugins:pretix_listmonk:organizer-settings', kwargs={
            'organizer': request.organizer.slug,
        }),
        'active': 'listmonk' in (request.resolver_match.url_name or ''),
    }]


@receiver(nav_event, dispatch_uid='pretix_listmonk_nav_event')
def control_nav_event(sender, request=None, **kwargs):
    if not _plugin_is_active(request.event):
        return []
    if not request.user.has_event_permission(
        request.organizer, request.event, 'can_change_event_settings', request=request
    ):
        return []
    return [{
        'label': _('Listmonk Newsletter'),
        'icon': 'envelope',
        'url': reverse('plugins:pretix_listmonk:event-settings', kwargs={
            'organizer': request.organizer.slug,
            'event': request.event.slug,
        }),
        'active': 'listmonk' in (request.resolver_match.url_name or ''),
        'parent': 'settings',
    }]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plugin_is_active(event):
    return 'pretix_listmonk' in (event.plugins or '')


def _maybe_subscribe(event, order):
    meta = json.loads(order.meta_info or '{}')
    contact_data = meta.get('contact_form_data', {})
    if not contact_data.get('listmonk_newsletter_consent'):
        return

    from .tasks import subscribe_to_listmonk
    subscribe_to_listmonk.apply_async(kwargs={
        'email': order.email,
        'name': _get_order_name(order),
        'event_slug': event.slug,
        'organizer_slug': event.organizer.slug,
        'order_code': order.code,
    })


def _get_order_name(order):
    try:
        parts = order.invoice_address.name_parts
        return parts.get('_legacy') or ' '.join(filter(None, [
            parts.get('given_name', ''),
            parts.get('family_name', ''),
        ]))
    except Exception:
        return ''
