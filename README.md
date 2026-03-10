# pretix-listmonk

A Pretix plugin that automatically subscribes attendees to a [Listmonk](https://listmonk.app) newsletter list when they opt in during checkout.

## Features

- Adds an optional newsletter consent checkbox to the Pretix checkout contact form
- Automatically subscribes consenting attendees to a configured Listmonk list via the API
- Skips re-subscription if the email is already subscribed
- Stores Pretix metadata (event slug, order code) as Listmonk subscriber attributes
- Async processing via Celery to avoid blocking order confirmation

## Configuration

In the Pretix organizer/event settings, configure:

- **Listmonk URL** – e.g. `https://newsletter.example.com`
- **Listmonk API username**
- **Listmonk API password/token**
- **Listmonk List ID** – the numeric ID of the target list
- **Checkbox label** – the consent text shown to the attendee

## Installation

```bash
pip install pretix-listmonk
```

Or in development:

```bash
pip install -e /path/to/pretix-listmonk
```

## License

MIT
