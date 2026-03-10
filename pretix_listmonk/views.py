import logging

import requests
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from pretix.control.permissions import OrganizerPermissionRequiredMixin
from pretix.control.views.event import EventSettingsViewMixin

from .forms import ListmonkEventSettingsForm, ListmonkOrganizerSettingsForm

logger = logging.getLogger(__name__)

ORGANIZER_KEYS = [
    'listmonk_url',
    'listmonk_api_user',
    'listmonk_api_password',
    'listmonk_list_id',
    'listmonk_trigger',
]

LISTMONK_TIMEOUT = 5


def _fetch_listmonk_lists(base_url, api_user, api_password):
    """Fetch all lists from Listmonk. Returns list of (id, name) tuples or None on error."""
    try:
        resp = requests.get(
            f'{base_url.rstrip("/")}/api/lists',
            params={'per_page': 'all'},
            auth=(api_user, api_password),
            timeout=LISTMONK_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get('data', {}).get('results') or []
        return [(str(lst['id']), f"{lst['name']} (ID {lst['id']})") for lst in results]
    except Exception as e:
        logger.warning('pretix-listmonk: could not fetch lists: %s', e)
        return None


class ListmonkOrganizerSettingsView(OrganizerPermissionRequiredMixin, FormView):
    form_class = ListmonkOrganizerSettingsForm
    template_name = 'pretix_listmonk/organizer_settings.html'
    permission = 'can_change_organizer_settings'

    def _get_list_choices(self):
        """Try to fetch lists from Listmonk using currently saved credentials."""
        s = self.request.organizer.settings
        base_url = s.get('listmonk_url', '')
        api_user = s.get('listmonk_api_user', '')
        api_password = s.get('listmonk_api_password', '')
        if not all([base_url, api_user, api_password]):
            return None
        return _fetch_listmonk_lists(base_url, api_user, api_password)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['list_choices'] = self._get_list_choices()
        return kwargs

    def get_initial(self):
        s = self.request.organizer.settings
        return {
            'listmonk_url': s.get('listmonk_url', ''),
            'listmonk_api_user': s.get('listmonk_api_user', ''),
            'listmonk_api_password': s.get('listmonk_api_password', ''),
            'listmonk_list_id': str(s.get('listmonk_list_id') or ''),
            'listmonk_trigger': s.get('listmonk_trigger', 'order_placed'),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        s = self.request.organizer.settings
        has_credentials = all([
            s.get('listmonk_url'),
            s.get('listmonk_api_user'),
            s.get('listmonk_api_password'),
        ])
        ctx['listmonk_has_credentials'] = has_credentials
        ctx['listmonk_lists_error'] = (
            has_credentials and self._get_list_choices() is None
        )
        return ctx

    def form_valid(self, form):
        s = self.request.organizer.settings
        for key in ORGANIZER_KEYS:
            val = form.cleaned_data.get(key)
            if val:
                s.set(key, val)

        # After saving credentials, try to fetch lists to confirm they work
        base_url = form.cleaned_data.get('listmonk_url', '').rstrip('/')
        api_user = form.cleaned_data.get('listmonk_api_user', '')
        api_password = form.cleaned_data.get('listmonk_api_password', '')
        if all([base_url, api_user, api_password]):
            lists = _fetch_listmonk_lists(base_url, api_user, api_password)
            if lists is None:
                messages.warning(
                    self.request,
                    _('Settings saved, but could not connect to Listmonk. Check your URL and credentials.'),
                )
            else:
                messages.success(self.request, _('Listmonk settings saved.'))
        else:
            messages.success(self.request, _('Listmonk settings saved.'))

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('plugins:pretix_listmonk:organizer-settings', kwargs={
            'organizer': self.request.organizer.slug,
        })


class ListmonkEventSettingsView(EventSettingsViewMixin, FormView):
    form_class = ListmonkEventSettingsForm
    template_name = 'pretix_listmonk/event_settings.html'
    permission = 'can_change_event_settings'

    def get_initial(self):
        s = self.request.event.settings
        return {
            'listmonk_checkbox_label': s.get('listmonk_checkbox_label', ''),
        }

    def form_valid(self, form):
        self.request.event.settings.set(
            'listmonk_checkbox_label',
            form.cleaned_data.get('listmonk_checkbox_label'),
        )
        messages.success(self.request, _('Listmonk settings saved.'))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('plugins:pretix_listmonk:event-settings', kwargs={
            'organizer': self.request.organizer.slug,
            'event': self.request.event.slug,
        })
