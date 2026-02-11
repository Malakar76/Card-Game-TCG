"""Tests for CardController QObject bridge."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from card_game_tcg.ui.controllers.card_controller import CardController
from tests.utils.test_runtime import AsyncRuntimeForTests


@pytest.fixture(scope="session")
def runtime():
    rt = AsyncRuntimeForTests()
    rt.start()
    yield rt
    rt.stop()


@pytest.fixture
def controller(qtbot, runtime):
    ctrl = CardController(runtime=runtime)
    return ctrl


class TestSignalsExist:
    def test_has_card_created_signal(self, controller):
        assert hasattr(controller, "cardCreated")

    def test_has_card_creation_failed_signal(self, controller):
        assert hasattr(controller, "cardCreationFailed")


class TestNameValidation:
    def test_empty_name_emits_failed(self, controller, qtbot):
        with qtbot.waitSignal(controller.cardCreationFailed, timeout=1000) as blocker:
            controller.createCard("", "desc", 1, 1, 1)
        assert "obligatoire" in blocker.args[0].lower()

    def test_whitespace_name_emits_failed(self, controller, qtbot):
        with qtbot.waitSignal(controller.cardCreationFailed, timeout=1000) as blocker:
            controller.createCard("   ", "desc", 1, 1, 1)
        assert "obligatoire" in blocker.args[0].lower()


class TestCreateCard:
    @patch("card_game_tcg.ui.controllers.card_controller.card_service")
    def test_success_emits_card_created(self, mock_service, controller, qtbot):
        fake_card = MagicMock()
        fake_card.name = "Dragon"
        mock_service.create_card = AsyncMock(return_value=fake_card)

        with qtbot.waitSignal(controller.cardCreated, timeout=3000) as blocker:
            controller.createCard("Dragon", "Fire breather", 5, 3, 4)
        assert "Dragon" in blocker.args[0]

    @patch("card_game_tcg.ui.controllers.card_controller.card_service")
    def test_service_error_emits_failed(self, mock_service, controller, qtbot):
        mock_service.create_card = AsyncMock(side_effect=RuntimeError("DB down"))

        with qtbot.waitSignal(controller.cardCreationFailed, timeout=3000) as blocker:
            controller.createCard("Dragon", "Fire breather", 5, 3, 4)
        assert "DB down" in blocker.args[0]
