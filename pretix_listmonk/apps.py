from django.utils.translation import gettext_lazy as _
from pretix.base.plugins import PluginConfig


class PretixPluginMeta:
    name = _('Listmonk Newsletter')
    author = 'Valentin Gosselin'
    version = '1.0.0'
    description = _('Subscribe attendees to a Listmonk newsletter list at checkout')
    category = 'INTEGRATION'
    compatibility = 'pretix>=4.0.0'


class ListmonkPluginConfig(PluginConfig):
    name = 'pretix_listmonk'
    verbose_name = 'Listmonk Newsletter'

    class Meta:
        app_label = 'pretix_listmonk'

    def ready(self):
        from . import signals  # noqa


default_app_config = 'pretix_listmonk.apps.ListmonkPluginConfig'
