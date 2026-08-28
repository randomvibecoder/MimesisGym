from __future__ import annotations

import hashlib
import http.client
import io
import ipaddress
import json
import socket
import ssl
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from PIL import Image

from .task import ImageTask, load_reference

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 4096 * 4096
MAX_REDIRECTS = 3


def _validate_https(url: str) -> tuple[str, int, str, str]:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("reference URL must be HTTPS and contain no credentials")
    port = parsed.port or 443
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("reference hostname did not resolve")
    public_addresses: list[str] = []
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if not address.is_global:
            raise ValueError(f"reference URL resolves to a non-public address: {address}")
        public_addresses.append(str(address))
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    return parsed.hostname, port, target, public_addresses[0]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to the address we validated while retaining hostname TLS checks."""

    def __init__(self, host: str, port: int, address: str, timeout: float):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._validated_address = address

    def connect(self) -> None:
        raw = socket.create_connection(
            (self._validated_address, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def download_reference(url: str, catalog_dir: Path, *, timeout_seconds: float = 15.0) -> ImageTask:
    current = url
    body: bytes | None = None
    mime = ""
    for redirect in range(MAX_REDIRECTS + 1):
        host, port, target, address = _validate_https(current)
        connection = _PinnedHTTPSConnection(host, port, address, timeout_seconds)
        try:
            connection.request("GET", target, headers={"User-Agent": "MimesisGym/0.1", "Accept": "image/*"})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location or redirect == MAX_REDIRECTS:
                    raise ValueError("reference URL exceeded redirect limit")
                current = urljoin(current, location)
                continue
            if response.status != 200:
                raise ValueError(f"reference download returned HTTP {response.status}")
            mime = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
            if not mime.startswith("image/"):
                raise ValueError(f"reference response is not an image ({mime or 'missing MIME type'})")
            declared = response.getheader("Content-Length")
            if declared and int(declared) > MAX_DOWNLOAD_BYTES:
                raise ValueError("reference download exceeds 20 MiB")
            body = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(body) > MAX_DOWNLOAD_BYTES:
                raise ValueError("reference download exceeds 20 MiB")
            break
        finally:
            connection.close()
    if body is None:
        raise ValueError("reference download failed")
    with Image.open(io.BytesIO(body)) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("animated reference images are not supported")
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("reference image exceeds the 4096² pixel limit")
        source.load()
        canonical = source.convert("RGB")
    digest = hashlib.sha256(body).hexdigest()
    catalog_dir.mkdir(parents=True, exist_ok=True)
    path = catalog_dir / f"{digest}.png"
    canonical.save(path, format="PNG")
    metadata = {"kind": "url", "requested_url": url, "final_url": current, "content_type": mime, "sha256": digest}
    (catalog_dir / f"{digest}.json").write_text(json.dumps(metadata, indent=2))
    return load_reference(path, task_id=digest[:12], display_name=f"URL reference {digest[:8]}", source=metadata)
