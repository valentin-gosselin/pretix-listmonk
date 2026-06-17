from django import forms
from django.utils.translation import gettext_lazy as _

from .security import validate_listmonk_url


class ListmonkOrganizerSettingsForm(forms.Form):
    """Settings stored at organizer level — shared across all events."""

    listmonk_url = forms.URLField(
        label=_('Listmonk URL'),
        help_text=_('Base URL of your Listmonk instance, e.g. https://newsletter.example.com'),
        required=True,
        validators=[validate_listmonk_url],
        widget=forms.URLInput(attrs={'placeholder': 'https://newsletter.example.com'}),
    )
    listmonk_api_user = forms.CharField(
        label=_('API username'),
        required=True,
    )
    listmonk_api_password = forms.CharField(
        label=_('API password / token'),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text=_('Leave empty to keep the currently saved password.'),
    )
    listmonk_list_id = forms.ChoiceField(
        label=_('Newsletter list'),
        required=True,
        help_text=_('Save URL and credentials first to load available lists'),
    )
    listmonk_trigger = forms.ChoiceField(
        label=_('Subscribe on'),
        choices=[
            ('order_placed', _('Order placed (recommended)')),
            ('order_paid', _('Payment confirmed')),
        ],
        required=True,
        initial='order_placed',
        help_text=_('When to send the subscription to Listmonk'),
    )
    listmonk_double_optin = forms.BooleanField(
        label=_('Enable double opt-in'),
        help_text=_('If checked, Listmonk will send a subscription confirmation email. If unchecked, subscribers are pre-confirmed.'),
        required=False,
        initial=False,
    )

    def __init__(self, *args, list_choices=None, organizer=None, **kwargs):
        self.organizer = organizer
        super().__init__(*args, **kwargs)
        if list_choices:
            self.fields['listmonk_list_id'].choices = list_choices
        else:
            self.fields['listmonk_list_id'].choices = [('', _('— Save URL & credentials first —'))]
            self.fields['listmonk_list_id'].required = False

    def clean_listmonk_api_password(self):
        password = self.cleaned_data.get('listmonk_api_password')
        has_saved_password = False
        if self.organizer:
            has_saved_password = bool(self.organizer.settings.get('listmonk_api_password'))

        if not password and not has_saved_password:
            raise forms.ValidationError(_('API password is required.'))
        return password


class ListmonkEventSettingsForm(forms.Form):
    """Optional per-event customisation."""

    listmonk_checkbox_label = forms.CharField(
        label=_('Consent checkbox label'),
        help_text=_('Leave empty to use the default text'),
        required=False,
    )

