from django.urls import path
from . import views

urlpatterns = [
    path(
        'control/organizer/<str:organizer>/settings/listmonk/',
        views.ListmonkOrganizerSettingsView.as_view(),
        name='organizer-settings',
    ),
    path(
        'control/event/<str:organizer>/<str:event>/settings/listmonk/',
        views.ListmonkEventSettingsView.as_view(),
        name='event-settings',
    ),
]
