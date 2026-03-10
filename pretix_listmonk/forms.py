from django import forms
from django.utils.translation import gettext_lazy as _


class ListmonkOrganizerSettingsForm(forms.Form):
    """Settings stored at organizer level — shared across all events."""

    listmonk_url = forms.URLField(
        label=_('Listmonk URL'),
        help_text=_('Base URL of your Listmonk instance, e.g. https://newsletter.example.com'),
        required=True,
        widget=forms.URLInput(attrs={'placeholder': 'https://newsletter.example.com'}),
    )
    listmonk_api_user = forms.CharField(
        label=_('API username'),
        required=True,
    )
    listmonk_api_password = forms.CharField(
        label=_('API password / token'),
        required=True,
        widget=forms.PasswordInput(render_value=True),
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

    def __init__(self, *args, list_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if list_choices:
            self.fields['listmonk_list_id'].choices = list_choices
        else:
            self.fields['listmonk_list_id'].choices = [('', _('— Save URL & credentials first —'))]
            self.fields['listmonk_list_id'].required = False


class ListmonkEventSettingsForm(forms.Form):
    """Optional per-event customisation."""

    listmonk_checkbox_label = forms.CharField(
        label=_('Consent checkbox label'),
        help_text=_('Leave empty to use the default text'),
        required=False,
    )
