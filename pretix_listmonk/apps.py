from django.utils.translation import gettext_lazy as _
from pretix.base.plugins import PluginConfig


class ListmonkPluginConfig(PluginConfig):
    name = 'pretix_listmonk'
    verbose_name = 'Listmonk Newsletter'

    class Meta:
        app_label = 'pretix_listmonk'

    class PretixPluginMeta:
        name = _('Listmonk Newsletter')
        author = 'Valentin Gosselin'
        version = '1.0.0'
        description = _('Subscribe attendees to a Listmonk newsletter list at checkout')
        category = 'INTEGRATION'
        compatibility = 'pretix>=4.0.0'

    def ready(self):
        from . import signals  # noqa

    @property
    def url_namespace(self):
        return 'pretix_listmonk'

    @property
    def urls(self):
        from .urls import urlpatterns
        return urlpatterns


default_app_config = 'pretix_listmonk.apps.ListmonkPluginConfig'
