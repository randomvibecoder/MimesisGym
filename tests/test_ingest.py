import socket
from unittest.mock import patch

import pytest

from mimesisgym.tracks.image.ingest import _validate_https


def _address(ip: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]


def test_url_validation() -> None:
    with pytest.raises(ValueError):
        _validate_https("http://example.com/a.png")
    with pytest.raises(ValueError):
        _validate_https("https://user:pass@example.com/a.png")
    with patch("socket.getaddrinfo", return_value=_address("127.0.0.1")):
        with pytest.raises(ValueError, match="non-public"):
            _validate_https("https://example.com/a.png")
    with patch("socket.getaddrinfo", return_value=_address("93.184.216.34")):
        assert _validate_https("https://example.com/a.png") == (
            "example.com",
            443,
            "/a.png",
            "93.184.216.34",
        )
