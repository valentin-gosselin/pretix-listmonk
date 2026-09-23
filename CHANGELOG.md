# Changelog

## 1.0.1

### Security

- **The event settings view did not enforce any permission.** It declared
  `permission = 'can_change_event_settings'` but inherited only from
  `EventSettingsViewMixin`, which adds a context variable and enforces nothing,
  so the declaration was inert. Any team member with access to the event — even
  one holding only `event.orders:read` — could open the Listmonk settings and
  change the consent checkbox label. Fixed by adding
  `EventPermissionRequiredMixin`, the mixin that actually performs the check.

  The organizer-level view, which holds the Listmonk URL and credentials, was
  **not** affected: it already used `OrganizerPermissionRequiredMixin`.

  Anyone running 1.0.0 should upgrade. No data is exposed by the flaw beyond the
  event-level checkbox label, but it allowed an unauthorised write.

- Added a test suite covering access control on both settings views.

## 1.0.0

- Initial release.
