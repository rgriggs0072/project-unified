ROUTE_LABELS: dict[str, dict[str, str]] = {
    "chat": {
        "display":            "Xovia AI",
        "display_with_model": "Xovia AI (Claude Sonnet)",
        "icon":               "⚡",
    },
    "code": {
        "display":            "Xovia AI — Code",
        "display_with_model": "Xovia AI — Code (Claude Sonnet)",
        "icon":               "⚡",
    },
    "image": {
        "display":            "Xovia AI — Image",
        "display_with_model": "Xovia AI — Image (gpt-image-1)",
        "icon":               "🎨",
    },
    "data": {
        "display":            "Xovia AI — Analysis",
        "display_with_model": "Xovia AI — Analysis (Claude Sonnet)",
        "icon":               "📊",
    },
    "agentic": {
        "display":            "Xovia AI — Cowork",
        "display_with_model": "Xovia AI — Cowork (Claude Sonnet)",
        "icon":               "🤖",
    },
    "video": {
        "display":            "Xovia AI — Video",
        "display_with_model": "Xovia AI — Video",
        "icon":               "🎬",
    },
    "audio": {
        "display":            "Xovia AI — Audio",
        "display_with_model": "Xovia AI — Audio",
        "icon":               "🎵",
    },
}

_FALLBACK = ROUTE_LABELS["chat"]


def get_display_label(category: str, show_model: bool = False) -> str:
    """Return the branded display label for a routing category."""
    entry = ROUTE_LABELS.get(category, _FALLBACK)
    return entry["display_with_model"] if show_model else entry["display"]


def get_icon(category: str) -> str:
    """Return the icon for a routing category."""
    return ROUTE_LABELS.get(category, _FALLBACK)["icon"]
