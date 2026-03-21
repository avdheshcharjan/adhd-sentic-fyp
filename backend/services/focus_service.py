import time
from typing import Optional, Dict, Any

class FocusService:
    def __init__(self):
        # No active task until one is set
        self.current_task = None

        # Focus Session state — read default block from settings (seconds)
        default_minutes = 25
        self.focus_session = {
            "total": float(default_minutes * 60),
            "is_running": False,
            "label": "Focus"
        }
        
        self.last_start_time: Optional[float] = None
        self.accumulated_time: float = 0.0

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        if self.current_task is None:
            return None
        self.current_task["is_active"] = self.focus_session["is_running"]
        return self.current_task

    def get_focus_session(self) -> Optional[Dict[str, Any]]:
        elapsed = self.accumulated_time
        if self.focus_session["is_running"] and self.last_start_time is not None:
            elapsed += (time.time() - self.last_start_time)
            
        return {
            "elapsed": float(elapsed),
            "total": float(self.focus_session["total"]),
            "is_running": bool(self.focus_session["is_running"]),
            "label": str(self.focus_session["label"])
        }

    def toggle_focus(self) -> Dict[str, str]:
        if self.focus_session["is_running"]:
            # Pause
            if self.last_start_time:
                self.accumulated_time += (time.time() - self.last_start_time)
            self.last_start_time = None
            self.focus_session["is_running"] = False
            return {"status": "paused"}
        else:
            # Start
            self.last_start_time = time.time()
            self.focus_session["is_running"] = True
            return {"status": "started"}

    def complete_task(self, task_id: str) -> Dict[str, str]:
        if self.current_task is not None and self.current_task["id"] == task_id:
            self.current_task["progress"] = 1.0
            self.current_task["is_active"] = False
            
            # Stop focus session
            if self.focus_session["is_running"]:
                self.toggle_focus()
                
            return {"status": "completed", "id": task_id}
        return {"status": "not_found", "id": task_id}
