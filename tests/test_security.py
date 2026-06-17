import socket
from django.core.exceptions import ValidationError
import pytest
from unittest.mock import patch

from pretix_listmonk.security import validate_listmonk_url, is_safe_listmonk_url


def test_safe_url():
    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))
        ]
        assert is_safe_listmonk_url('https://example.com') is True
        validate_listmonk_url('https://example.com')  # should not raise


def test_http_scheme_rejected():
    assert is_safe_listmonk_url('http://example.com') is False
    with pytest.raises(ValidationError, match='must use the HTTPS scheme'):
        validate_listmonk_url('http://example.com')


def test_loopback_rejected():
    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))
        ]
        assert is_safe_listmonk_url('https://localhost') is False
        with pytest.raises(ValidationError, match='Private or loopback IP addresses are not allowed'):
            validate_listmonk_url('https://localhost')


def test_private_ip_rejected():
    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 0))
        ]
        assert is_safe_listmonk_url('https://internal.lan') is False
        with pytest.raises(ValidationError, match='Private or loopback IP addresses are not allowed'):
            validate_listmonk_url('https://internal.lan')


def test_ipv6_loopback_rejected():
    with patch('socket.getaddrinfo') as mock_getaddrinfo:
        mock_getaddrinfo.return_value = [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 0, 0, 0))
        ]
        assert is_safe_listmonk_url('https://localhost6') is False
        with pytest.raises(ValidationError, match='Private or loopback IP addresses are not allowed'):
            validate_listmonk_url('https://localhost6')


def test_dns_resolution_failure():
    with patch('socket.getaddrinfo', side_effect=socket.gaierror):
        assert is_safe_listmonk_url('https://nonexistent-domain.foo') is False
        with pytest.raises(ValidationError, match='Could not resolve hostname'):
            validate_listmonk_url('https://nonexistent-domain.foo')
