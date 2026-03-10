import logging

from django import forms
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from pretix.base.signals import order_placed
from pretix.presale.signals import contact_form_fields

logger = logging.getLogger(__name__)


@receiver(contact_form_fields, dispatch_uid='pretix_listmonk_contact_field')
def add_newsletter_field(sender, **kwargs):
    """Inject the newsletter consent checkbox into the checkout contact form."""
    if not _plugin_is_active(sender):
        return {}

    label = sender.settings.get('listmonk_checkbox_label', default=_('I would like to subscribe to the newsletter'))

    return {
        'listmonk_newsletter_consent': forms.BooleanField(
            label=label,
            required=False,
        )
    }


@receiver(order_placed, dispatch_uid='pretix_listmonk_order_placed')
def on_order_placed(sender, order, **kwargs):
    """Trigger Listmonk subscription after order is placed."""
    if not _plugin_is_active(sender):
        return

    import json
    meta = json.loads(order.meta_info or '{}')
    contact_data = meta.get('contact_form_data', {})

    if not contact_data.get('listmonk_newsletter_consent'):
        return

    from .tasks import subscribe_to_listmonk
    subscribe_to_listmonk.apply_async(
        kwargs={
            'email': order.email,
            'name': _get_order_name(order),
            'event_slug': sender.slug,
            'organizer_slug': sender.organizer.slug,
            'order_code': order.code,
        }
    )


def _plugin_is_active(event):
    return 'pretix_listmonk' in (event.plugins or '')


def _get_order_name(order):
    try:
        parts = order.invoice_address.name_parts
        return parts.get('_legacy') or ' '.join(filter(None, [
            parts.get('given_name', ''),
            parts.get('family_name', ''),
        ]))
    except Exception:
        return ''
