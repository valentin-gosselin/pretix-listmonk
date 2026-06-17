import socket
import ipaddress
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_listmonk_url(url):
    """
    Validates that the given URL uses HTTPS and does not resolve to a private or loopback IP address.
    """
    if not url:
        return

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError(_('Invalid URL.'))

    if not parsed.scheme or parsed.scheme.lower() != 'https':
        raise ValidationError(_('Listmonk URL must use the HTTPS scheme.'))

    host = parsed.hostname
    if not host:
        raise ValidationError(_('Invalid hostname in URL.'))

    try:
        # Resolve all IP addresses for the hostname
        # AF_UNSPEC gets both IPv4 and IPv6
        addr_info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ValidationError(_('Could not resolve hostname.'))

    for info in addr_info:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValidationError(_('Invalid IP address resolved.'))

        if (
            ip.is_loopback or
            ip.is_private or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_multicast or
            ip.is_unspecified
        ):
            raise ValidationError(_('Private or loopback IP addresses are not allowed.'))

def is_safe_listmonk_url(url):
    """
    Returns True if the URL is valid, uses HTTPS, and resolves to public IP addresses only.
    Otherwise returns False.
    """
    try:
        validate_listmonk_url(url)
        return True
    except ValidationError:
        return False
