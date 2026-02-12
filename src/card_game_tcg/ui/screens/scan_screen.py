"""Screen for scanning Pokémon cards via camera and OCR."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import Screen

from card_game_tcg.services import ocr_service

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "scanscreen.kv"))

_camera_available = False
try:
    from camera4kivy import Preview  # noqa: F401

    _camera_available = True
except ImportError:
    pass

_is_android = "android" in sys.modules or hasattr(sys, "getandroidapilevel")


class ScanScreen(Screen):
    """Screen that uses the camera to scan and identify Pokémon cards."""

    status_text = StringProperty("")
    pokemon_name = StringProperty("")
    is_loading = BooleanProperty(False)
    preview_label = StringProperty("Caméra non disponible")

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

        self._capture_dir = tempfile.mkdtemp()

        try:
            from camera4kivy import Preview

            preview = Preview(aspect_ratio="4:3")
            self._preview = preview

            container.remove_widget(placeholder)
            container.add_widget(preview)

            # mirrored=False: scanning a card, not a selfie
            # filepath_callback: receive actual saved file path
            try:
                preview.connect_camera(
                    enable_analyze_pixels=False,
                    facing="back",
                    mirrored=False,
                    filepath_callback=self._on_capture_complete,
                )
            except Exception:
                preview.connect_camera(
                    mirrored=False,
                    filepath_callback=self._on_capture_complete,
                )

            self.preview_label = ""
        except Exception as exc:
            self.status_text = f"Erreur caméra : {exc}"

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
        if not file_path or not Path(file_path).exists():
            Clock.schedule_once(lambda _dt: self._on_ocr_error("Fichier capturé introuvable"))
            return

        Thread(
            target=self._run_ocr,
            args=(file_path,),
            daemon=True,
        ).start()

    def _run_ocr(self, file_path: str) -> None:
        """Run OCR on the captured image (called in background thread)."""
        try:
            # Desktop webcam saves landscape frames; rotate 270° for OCR.
            # On Android, CameraX handles orientation natively.
            rotation = 0 if _is_android else 90
            raw_text = ocr_service.recognize_text_from_file(file_path, rotation)
            name = ocr_service.extract_pokemon_name(raw_text)
            Clock.schedule_once(lambda _dt: self._on_ocr_result(name, raw_text))
        except Exception as err:
            msg = str(err)
            Clock.schedule_once(lambda _dt: self._on_ocr_error(msg))

    def _on_ocr_result(self, name: str | None, raw_text: str) -> None:
        """Handle OCR result on the main thread."""
        self.is_loading = False
        if name:
            self.pokemon_name = name
            self.status_text = "Pokémon détecté !"
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
