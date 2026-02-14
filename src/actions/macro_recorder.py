"""
Macro recorder for imitation learning: record and replay user interactions.
"""
import json
import logging
import time
from pathlib import Path
from threading import Lock
from typing import Dict, Any, List, Optional

logger = logging.getLogger("MacroRecorder")


class MacroRecorder:
    """Records and replays mouse/keyboard events."""

    def __init__(self):
        self.recording = False
        self.start_ts = 0.0
        self.events: List[Dict[str, Any]] = []
        self.current_macro_name = ""
        self.output_dir = Path.home() / ".ai_agent" / "macros"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mouse_listener = None
        self.keyboard_listener = None
        self.mouse_controller = None
        self.keyboard_controller = None

        self._lock = Lock()
        self.available = self._check_dependencies()

    def _check_dependencies(self) -> bool:
        try:
            from pynput import keyboard, mouse

            self._keyboard_module = keyboard
            self._mouse_module = mouse
            self.mouse_controller = mouse.Controller()
            self.keyboard_controller = keyboard.Controller()
            return True
        except Exception as error:
            logger.warning(f"Macro recorder unavailable: {error}")
            return False

    def _now(self) -> float:
        return max(0.0, time.time() - self.start_ts)

    def _serialize_key(self, key) -> Dict[str, Any]:
        if hasattr(key, "char") and key.char is not None:
            return {"kind": "char", "value": key.char}
        return {"kind": "special", "value": str(key).replace("Key.", "")}

    def _capture_ui_context(self) -> Dict[str, Any]:
        context = {
            "window_title": "",
            "window_handle": None,
            "window_class": "",
            "automation_id": "",
        }

        try:
            from pywinauto import Desktop

            active = Desktop(backend="uia").get_active()
            context["window_title"] = active.window_text()
            context["window_handle"] = int(active.handle) if getattr(active, "handle", None) else None

            element_info = getattr(active, "element_info", None)
            if element_info:
                context["window_class"] = getattr(element_info, "class_name", "") or ""
                context["automation_id"] = getattr(element_info, "automation_id", "") or ""
        except Exception:
            pass

        return context

    def _append_event(self, event: Dict[str, Any]):
        with self._lock:
            if not self.recording:
                return
            event["timestamp"] = self._now()
            event["ui_context"] = self._capture_ui_context()
            self.events.append(event)

    def start_recording(self, macro_name: str) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "message": "Macro recorder dependencies unavailable"}

        if self.recording:
            return {"success": False, "message": "Macro recording already in progress"}

        self.current_macro_name = (macro_name or "default_macro").strip().replace(" ", "_")
        self.events = []
        self.start_ts = time.time()
        self.recording = True

        def on_click(x, y, button, pressed):
            self._append_event(
                {
                    "type": "mouse_click",
                    "x": int(x),
                    "y": int(y),
                    "button": str(button).replace("Button.", ""),
                    "pressed": bool(pressed),
                }
            )

        def on_move(x, y):
            self._append_event(
                {
                    "type": "mouse_move",
                    "x": int(x),
                    "y": int(y),
                }
            )

        def on_scroll(x, y, dx, dy):
            self._append_event(
                {
                    "type": "mouse_scroll",
                    "x": int(x),
                    "y": int(y),
                    "dx": int(dx),
                    "dy": int(dy),
                }
            )

        def on_press(key):
            self._append_event(
                {
                    "type": "key_press",
                    "key": self._serialize_key(key),
                }
            )

        def on_release(key):
            self._append_event(
                {
                    "type": "key_release",
                    "key": self._serialize_key(key),
                }
            )

        self.mouse_listener = self._mouse_module.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll)
        self.keyboard_listener = self._keyboard_module.Listener(on_press=on_press, on_release=on_release)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        logger.info(f"Macro recording started: {self.current_macro_name}")
        return {"success": True, "message": f"Started macro recording: {self.current_macro_name}"}

    def _macro_path(self, macro_name: str) -> Path:
        safe_name = (macro_name or "default_macro").strip().replace(" ", "_")
        return self.output_dir / f"{safe_name}.json"

    def stop_recording(self) -> Dict[str, Any]:
        if not self.recording:
            return {"success": False, "message": "No active macro recording"}

        self.recording = False

        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        except Exception:
            pass

        self.mouse_listener = None
        self.keyboard_listener = None

        output = {
            "macro_name": self.current_macro_name,
            "created_at": int(time.time()),
            "event_count": len(self.events),
            "events": self.events,
        }

        macro_path = self._macro_path(self.current_macro_name)
        with open(macro_path, "w", encoding="utf-8") as file_obj:
            json.dump(output, file_obj, indent=2)

        logger.info(f"Macro recording saved: {macro_path}")
        return {
            "success": True,
            "message": f"Saved macro '{self.current_macro_name}' with {len(self.events)} events",
            "macro_path": str(macro_path),
            "event_count": len(self.events),
        }

    def _deserialize_key(self, key_data: Dict[str, Any]):
        kind = key_data.get("kind")
        value = key_data.get("value")

        if kind == "char":
            return value

        return getattr(self._keyboard_module.Key, value, value)

    def replay(self, macro_name: str, speed: float = 1.0) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "message": "Macro recorder dependencies unavailable"}

        macro_path = self._macro_path(macro_name)
        if not macro_path.exists():
            return {"success": False, "message": f"Macro '{macro_name}' not found"}

        with open(macro_path, "r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)

        events = payload.get("events", [])
        if not events:
            return {"success": False, "message": f"Macro '{macro_name}' has no events"}

        speed = max(0.1, float(speed))
        previous_ts = 0.0

        for event in events:
            ts = float(event.get("timestamp", previous_ts))
            sleep_for = max(0.0, (ts - previous_ts) / speed)
            if sleep_for > 0:
                time.sleep(sleep_for)
            previous_ts = ts

            event_type = event.get("type")
            if event_type == "mouse_move":
                self.mouse_controller.position = (event.get("x", 0), event.get("y", 0))
            elif event_type == "mouse_click":
                button = getattr(self._mouse_module.Button, event.get("button", "left"), self._mouse_module.Button.left)
                if event.get("pressed", True):
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
            elif event_type == "mouse_scroll":
                self.mouse_controller.scroll(event.get("dx", 0), event.get("dy", 0))
            elif event_type == "key_press":
                self.keyboard_controller.press(self._deserialize_key(event.get("key", {})))
            elif event_type == "key_release":
                self.keyboard_controller.release(self._deserialize_key(event.get("key", {})))

        logger.info(f"Macro replay completed: {macro_name}")
        return {"success": True, "message": f"Replayed macro '{macro_name}'", "event_count": len(events)}


macro_recorder = MacroRecorder()
