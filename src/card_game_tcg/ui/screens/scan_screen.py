"""Screen for scanning Pokémon cards via camera and OCR."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import Screen
from tcgdexsdk import Language

from card_game_tcg.clients import TCGDEX
from card_game_tcg.services import ocr_service
from card_game_tcg.ui.constants import LANGUAGES

logger = logging.getLogger(__name__)

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "scanscreen.kv"))

_camera_available = False
try:
    from camera4kivy import Preview  # noqa: F401

    _camera_available = True
except ImportError:
    pass

_is_android = "android" in sys.modules or hasattr(sys, "getandroidapilevel")

_MAX_OCR_ATTEMPTS = 3

_client = TCGDEX()


class ScanScreen(Screen):
    """Screen that uses the camera to scan and identify Pokémon cards."""

    status_text = StringProperty("")
    pokemon_name = StringProperty("")
    is_loading = BooleanProperty(False)
    preview_label = StringProperty("Caméra non disponible")
    selected_language = StringProperty("Français")

    _preview: object | None = None
    _capture_dir: str = ""

    def on_enter(self) -> None:
        """Start camera preview when entering the screen."""
        if not _camera_available:
            self.preview_label = "camera4kivy non installé"
            return

        self._request_camera_permission()

    def on_leave(self) -> None:
        """Stop camera preview when leaving the screen."""
        if self._preview is not None:
            try:
                self._preview.disconnect_camera()  # type: ignore[union-attr]
            except Exception:
                pass

    def _request_camera_permission(self) -> None:
        """Request camera permission on Android, then start preview."""
        try:
            from android.permissions import (  # type: ignore[import-not-found]
                Permission,
                request_permissions,
            )

            def _callback(permissions: list[str], results: list[bool]) -> None:
                if all(results):
                    Clock.schedule_once(lambda _dt: self._start_preview())
                else:
                    self.status_text = "Permission caméra refusée"

            request_permissions([Permission.CAMERA], _callback)
        except ImportError:
            # Desktop: no permission needed
            self._start_preview()

    def _start_preview(self) -> None:
        """Initialize and start the camera preview widget."""
        container = self.ids.preview_container
        placeholder = self.ids.preview_placeholder

        if self._preview is not None:
            return

        self._capture_dir = self._get_capture_dir()

        try:
            from camera4kivy import Preview

            preview = Preview(aspect_ratio="4:3")
            self._preview = preview

            container.remove_widget(placeholder)
            container.add_widget(preview)

            # Connect camera one frame later so the widget has a valid size.
            # On Android, CameraX needs the layout to be resolved first.
            Clock.schedule_once(lambda _dt: self._connect_camera(), 0)

            self.preview_label = ""
        except Exception as exc:
            self.status_text = f"Erreur caméra : {exc}"

    def _connect_camera(self) -> None:
        """Connect the camera after the Preview widget has been laid out."""
        if self._preview is None:
            return
        try:
            self._preview.connect_camera(  # type: ignore[union-attr]
                enable_analyze_pixels=False,
                facing="back",
                mirrored=False,
                filepath_callback=self._on_capture_complete,
            )
        except TypeError:
            # Older camera4kivy versions may not support all kwargs
            self._preview.connect_camera(  # type: ignore[union-attr]
                mirrored=False,
                filepath_callback=self._on_capture_complete,
            )

    @staticmethod
    def _get_capture_dir() -> str:
        """Return a writable directory for photo capture."""
        if _is_android:
            # On Android, use the app's private storage (writable by Java CameraX)
            private = os.environ.get("ANDROID_PRIVATE", "")
            if private:
                capture = os.path.join(private, "capture")
                os.makedirs(capture, exist_ok=True)
                return capture
        return tempfile.mkdtemp()

    def analyze(self) -> None:
        """Capture a photo and run OCR in a background thread."""
        if self.is_loading:
            return

        if self._preview is None:
            self.status_text = "Caméra non disponible"
            return

        self.is_loading = True
        self.status_text = "Capture en cours..."
        self.pokemon_name = ""

        try:
            self._preview.capture_photo(  # type: ignore[union-attr]
                location=self._capture_dir,
            )
        except Exception as exc:
            self.is_loading = False
            self.status_text = f"Erreur capture : {exc}"

    def _on_capture_complete(self, file_path: str) -> None:
        """Called by camera4kivy when the photo has been saved."""
        logger.info("filepath_callback received: %r", file_path)

        # If callback path is valid, use it directly
        if file_path and Path(file_path).exists():
            self._start_ocr(file_path)
            return

        # Fallback: scan capture dir for newest image (CameraX may not
        # return the path through the callback on all devices)
        found = self._find_latest_capture()
        if found:
            logger.info("Found capture via directory scan: %s", found)
            self._start_ocr(found)
            return

        msg = f"Fichier introuvable (callback={file_path!r}, dir={self._capture_dir})"
        logger.warning(msg)
        Clock.schedule_once(lambda _dt: self._on_ocr_error(msg))

    def _find_latest_capture(self) -> str | None:
        """Find the most recently modified image in the capture directory."""
        if not self._capture_dir:
            return None
        capture_dir = Path(self._capture_dir)
        if not capture_dir.exists():
            return None
        images = sorted(
            capture_dir.glob("*.jpg"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not images:
            # Also try png
            images = sorted(
                capture_dir.glob("*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        return str(images[0]) if images else None

    def _start_ocr(self, file_path: str) -> None:
        """Launch OCR processing in a background thread."""
        Thread(
            target=self._run_ocr,
            args=(file_path,),
            daemon=True,
        ).start()

    def _get_language(self) -> Language:
        """Resolve the selected language label to a ``Language`` enum."""
        for label, lang in LANGUAGES:
            if label == self.selected_language:
                return lang
        return Language.FR

    def _run_ocr(self, file_path: str) -> None:
        """Run OCR on the captured image and validate via TCGdex."""
        try:
            rotation = 0 if _is_android else 270
            language = self._get_language()

            for attempt in range(1, _MAX_OCR_ATTEMPTS + 1):
                Clock.schedule_once(
                    lambda _dt, a=attempt: self._update_status(
                        f"Analyse OCR (tentative {a}/{_MAX_OCR_ATTEMPTS})..."
                    )
                )

                raw_text = ocr_service.recognize_text_from_file(file_path, rotation)
                candidates = ocr_service.extract_pokemon_candidates(raw_text)

                if not candidates:
                    continue

                for name in candidates:
                    try:
                        results = _client.search_cards_by_name(name, language, page_size=1)
                    except Exception:
                        results = []
                    if results:
                        Clock.schedule_once(lambda _dt, n=name: self._on_ocr_result(n, raw_text))
                        return

            # All attempts exhausted – fall back to first candidate if any
            fallback = candidates[0] if candidates else None
            Clock.schedule_once(
                lambda _dt: self._on_ocr_result(fallback, raw_text, validated=False)
            )
        except Exception as err:
            msg = str(err)
            Clock.schedule_once(lambda _dt: self._on_ocr_error(msg))

    def _update_status(self, text: str) -> None:
        """Update the status label (must be called on the main thread)."""
        self.status_text = text

    def _on_ocr_result(self, name: str | None, raw_text: str, *, validated: bool = True) -> None:
        """Handle OCR result on the main thread."""
        self.is_loading = False
        if name and validated:
            self.pokemon_name = name
            self.status_text = "Pokémon validé via TCGdex !"
        elif name:
            self.pokemon_name = name
            self.status_text = "Nom détecté (non validé par TCGdex)"
        else:
            self.pokemon_name = ""
            preview = raw_text[:80] if raw_text else ""
            if preview:
                self.status_text = f"Aucun nom détecté. Texte : {preview}"
            else:
                self.status_text = "Aucun texte détecté"

    def _on_ocr_error(self, error: str) -> None:
        """Handle OCR error on the main thread."""
        self.is_loading = False
        self.status_text = f"Erreur OCR : {error}"
