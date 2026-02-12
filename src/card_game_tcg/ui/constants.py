"""Shared constants for the UI layer."""

from tcgdexsdk import Language

LANGUAGES: list[tuple[str, Language]] = [
    ("Français", Language.FR),
    ("English", Language.EN),
    ("Deutsch", Language.DE),
    ("Español", Language.ES),
    ("Italiano", Language.IT),
    ("日本語", Language.JA),
]
