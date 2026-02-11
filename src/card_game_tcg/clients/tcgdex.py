"""TCGdex API client for Pokémon TCG data."""

from tcgdexsdk import Card, CardResume, Language, Query, TCGdex


class TCGDEX:
    """Wrapper around the TCGdex SDK configured via project settings."""

    def __init__(self) -> None:
        self.sdk = TCGdex()

    # ── Cards ────────────────────────────────────────────────────────

    def get_card(self, card_id: str) -> Card | None:
        """Fetch a single card by its unique ID (e.g. ``'swsh3-136'``)."""
        return self.sdk.card.getSync(card_id)

    def search_cards_by_name(
        self,
        name: str,
        language: Language,
        page: int = 1,
        page_size: int = 20,
    ) -> list[CardResume]:
        """Search cards matching a name with pagination."""
        self.sdk.setLanguage(language)
        query = Query().like("name", name).paginate(page, page_size)
        return self.sdk.card.listSync(query)
