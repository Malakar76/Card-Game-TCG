"""Business logic for card operations."""

from card_game_tcg.models.card import Card


async def get_all_cards() -> list[Card]:
    return await Card.find_all().to_list()


async def get_card_by_name(name: str) -> Card | None:
    return await Card.find_one(Card.name == name)


async def create_card(
    name: str,
    description: str = "",
    attack: int = 0,
    defense: int = 0,
    cost: int = 0,
) -> Card:
    card = Card(name=name, description=description, attack=attack, defense=defense, cost=cost)
    await card.insert()
    return card


async def delete_card(card: Card) -> None:
    await card.delete()
