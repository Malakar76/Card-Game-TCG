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

_client = TCGDEX()

_ocr_warmed_up = False


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
        global _ocr_warmed_up  # noqa: PLW0603

        self.is_loading = False
        self.pokemon_name = ""
        self.status_text = ""

        if not _ocr_warmed_up:
            _ocr_warmed_up = True
            Thread(target=ocr_service.warm_up, daemon=True).start()

        if not _camera_available:
            self.preview_label = "camera4kivy non installé"
            return

        self._request_camera_permission()

    def on_leave(self) -> None:
        """Leave camera running — disconnecting causes native SIGSEGV on reconnect."""

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

            perms = [Permission.CAMERA]
            # API 33+: READ_MEDIA_IMAGES to access CameraX captures in DCIM
            if hasattr(Permission, "READ_MEDIA_IMAGES"):
                perms.append(Permission.READ_MEDIA_IMAGES)
            else:
                perms.append(Permission.READ_EXTERNAL_STORAGE)
            request_permissions(perms, _callback)
        except ImportError:
            # Desktop: no permission needed
            self._start_preview()

    def _start_preview(self) -> None:
        """Initialize and start the camera preview widget."""
        if self._preview is not None:
            return

        try:
            container = self.ids.preview_container
            placeholder = self.ids.preview_placeholder
        except ReferenceError:
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
                enable_video=False,
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
        try:
            logger.info("filepath_callback received: %r", file_path)

            resolved = self._resolve_capture_path(file_path)
            if resolved:
                self._start_ocr(resolved)
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
        except Exception as exc:
            logger.exception("Error in _on_capture_complete")
            msg = str(exc)
            Clock.schedule_once(lambda _dt: self._on_ocr_error(msg))

    @staticmethod
    def _resolve_capture_path(file_path: str) -> str | None:
        """Resolve a capture path returned by camera4kivy.

        On Android, camera4kivy may return a relative path (e.g.
        ``DCIM/Card Game TCG/...``) relative to external storage.
        """
        if not file_path or file_path.startswith("Image Capture"):
            return None

        try:
            p = Path(file_path)
            if p.is_absolute() and p.exists():
                return file_path

            # Android: resolve relative path against external storage
            if _is_android:
                for base in ("/storage/emulated/0", "/sdcard"):
                    candidate = Path(base) / file_path
                    if candidate.exists():
                        logger.info("Resolved capture path: %s", candidate)
                        return str(candidate)
        except OSError as exc:
            logger.warning("Error resolving capture path %r: %s", file_path, exc)

        return None

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

            Clock.schedule_once(lambda _dt: self._update_status("Analyse OCR..."))

            raw_text = ocr_service.recognize_text_from_file(file_path, rotation)
            candidates = ocr_service.extract_pokemon_candidates(raw_text)

            if not candidates:
                Clock.schedule_once(
                    lambda _dt: self._on_ocr_result(None, raw_text, validated=False)
                )
                return

            for name in candidates:
                try:
                    results = _client.search_cards_by_name(name, language, page_size=1)
                except Exception:
                    results = []
                if results:
                    Clock.schedule_once(lambda _dt, n=name: self._on_ocr_result(n, raw_text))
                    return

            # No candidate validated – fall back to first candidate
            fallback = candidates[0]
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
            self._navigate_to_evolution(name)
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

    def _navigate_to_evolution(self, name: str) -> None:
        """Navigate to the evolution screen for the detected Pokémon."""
        evolution_screen = self.manager.get_screen("evolution")
        evolution_screen.pokemon_name = name
        evolution_screen.selected_language = self.selected_language
        self.manager.current = "evolution"

    def _on_ocr_error(self, error: str) -> None:
        """Handle OCR error on the main thread."""
        self.is_loading = False
        self.status_text = f"Erreur OCR : {error}"
