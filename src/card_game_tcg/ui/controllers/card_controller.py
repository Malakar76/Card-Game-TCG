from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from card_game_tcg.services import card_service


class CardController(QObject):
    """QObject controller exposed to QML for card operations."""

    cardCreated = Signal(str)  # noqa: N815
    cardCreationFailed = Signal(str)  # noqa: N815

    cardsLoaded = Signal(list)  # noqa: N815
    cardsLoadFailed = Signal(str)  # noqa: N815

    _uiSuccess = Signal(object)  # noqa: N815
    _uiError = Signal(str)  # noqa: N815
    _uiCards = Signal(list)  # noqa: N815
    _uiCardsError = Signal(str)  # noqa: N815

    def __init__(self, runtime, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._runtime = runtime
        self._uiSuccess.connect(self._handle_success)
        self._uiError.connect(self._handle_error)
        self._uiCards.connect(self._handle_cards_loaded)
        self._uiCardsError.connect(self._handle_cards_error)

    @Slot(str, str, int, int, int)
    def createCard(  # noqa: N802
        self, name: str, description: str, attack: int, defense: int, cost: int
    ) -> None:
        name = name.strip()
        if not name:
            self.cardCreationFailed.emit("Le nom de la carte est obligatoire.")
            return

        fut = self._runtime.submit(
            card_service.create_card(name, description, attack, defense, cost)
        )
        fut.add_done_callback(self._on_create_done)

    def _on_create_done(self, fut) -> None:
        try:
            card = fut.result()
            self._uiSuccess.emit(card)
        except Exception as exc:
            self._uiError.emit(str(exc))

    @Slot()
    def loadCards(self) -> None:  # noqa: N802
        """Load all cards from DB and emit cardsLoaded(list_of_dicts)."""
        fut = self._runtime.submit(card_service.get_all_cards())
        fut.add_done_callback(self._on_load_cards_done)

    def _on_load_cards_done(self, fut) -> None:
        try:
            cards = fut.result()
            self._uiCards.emit(self._to_qml_cards(cards))
        except Exception as exc:
            self._uiCardsError.emit(str(exc))

    def _to_qml_cards(self, cards: Any) -> list[dict]:
        """Convert service return into a QML-friendly list of dicts."""
        if not cards:
            return []

        out: list[dict] = []
        for c in cards:
            out.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "attack": c.attack,
                    "defense": c.defense,
                    "cost": c.cost,
                }
            )

        out.sort(key=lambda x: (x.get("name") or "").lower())
        return out

    @Slot(object)
    def _handle_success(self, card: Any) -> None:
        card_name = getattr(card, "name", None) or "?"
        self.cardCreated.emit(f"Carte « {card_name} » créée avec succès !")

    @Slot(str)
    def _handle_error(self, msg: str) -> None:
        self.cardCreationFailed.emit(msg)

    @Slot(list)
    def _handle_cards_loaded(self, cards: list) -> None:
        self.cardsLoaded.emit(cards)

    @Slot(str)
    def _handle_cards_error(self, msg: str) -> None:
        self.cardsLoadFailed.emit(msg)
