import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PARAM_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "gclid",
    "fbclid",
    "utm_term",
    "utm_content",
    "sessionid",
    "sid",
}


def canonicalize_url(url: str) -> str:
    """Normaliza URLs para deduplicación.

    - Quita parámetros de tracking
    - Elimina barra final
    """
    if not url:
        return url
    p = urlparse(url)
    # normaliza path (sin slash final)
    path = p.path or ""
    if path != "/":
        path = path.rstrip("/")

    # filtra tracking
    params = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAM_KEYS]
    query = urlencode(params, doseq=True)

    return urlunparse((p.scheme, p.netloc.lower(), path, "", query, ""))


def url_canonical_hash(url: str) -> str:
    canon = canonicalize_url(url)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()

