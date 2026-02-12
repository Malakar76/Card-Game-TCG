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

    def search_cards_by_exact_name(self, name: str, language: Language) -> list[CardResume]:
        """Search cards with an exact name match."""
        self.sdk.setLanguage(language)
        query = Query().equal("name", name)
        return self.sdk.card.listSync(query)

    def get_card_in_language(self, card_id: str, language: Language) -> Card | None:
        """Fetch a card by ID in a specific language."""
        self.sdk.setLanguage(language)
        return self.sdk.card.getSync(card_id)

    def search_by_evolve_from(self, name: str, language: Language) -> list[CardResume]:
        """Find cards that evolve from the given Pokémon name."""
        self.sdk.setLanguage(language)
        query = Query().equal("evolveFrom", name)
        return self.sdk.card.listSync(query)
