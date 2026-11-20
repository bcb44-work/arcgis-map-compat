from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass
class GISContext:
    """Browser configuration that can be supplied without importing arcgis."""

    portal_url: str = "https://www.arcgis.com"
    token: str = field(default="", repr=False)
    username: str = ""
    proxy_rules: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_gis(cls, gis):
        """Accept an existing GIS or an object with the same connection attributes."""
        if gis is None:
            return cls()
        if isinstance(gis, cls):
            return gis
        if isinstance(gis, Mapping):
            return cls(**gis)

        session = getattr(gis, "_session", None)
        auth = getattr(session, "auth", None)
        token = getattr(auth, "token", None)
        if not token:
            modes = getattr(auth, "authentication_modes", ())
            token = next((mode.token for mode in modes if getattr(mode, "token", None)), "")
        return cls(
            portal_url=getattr(gis, "_public_rest_url", None) or gis.url,
            token=str(token or ""),
            username=str(getattr(gis, "_username", "") or ""),
            proxy_rules=dict(getattr(session, "proxies", None) or {}),
        )
