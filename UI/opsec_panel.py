"""
UI/opsec_panel.py
Panel para mostrar sugerencias de OpSec/Tácticas en EchoMaze CLI UI.
Implements Observer pattern for dynamic updates with debounce and error handling.
"""

import threading
from asciimatics.widgets import Frame, Layout, Label, Divider, TextBox
from asciimatics.screen import Screen
from hooks.opsec_hooks import OpSecHooks
from UI.models import Observer, inject_risk_palette, risk_colour_key_for_score


class OpSecPanel(Frame, Observer):
    """
    OpSec/Tactical Suggestions panel widget for the EchoMaze UI.
    Displays actionable OpSec/tactical tips based on the current state.
    
    Implements Observer to receive dynamic updates from Observable subjects
    (ScoringEngine, TacticalSuggestions, GenericModel).
    
    States:
        - ok: normal operation, auto-updates enabled
        - pending: update scheduled via debounce, waiting for flush
        - error: an error occurred, auto-updates disabled until manual refresh
    """
    DEBOUNCE_INTERVAL = 0.12  # 120ms debounce window

    def __init__(self, screen: Screen, model, noise_score=0, pivot_path=None, service=None, height=10):
        super(OpSecPanel, self).__init__(
            screen,
            height,
            width=screen.width//2,
            can_scroll=False,
            title="OpSec Guidance"
        )
        Observer.__init__(self)
        inject_risk_palette(self.palette)
        self.model = model
        self.opsec = OpSecHooks()
        self.noise_score = noise_score
        self.pivot_path = pivot_path or []
        self.service = service
        self._state = "ok"  # ok | pending | error
        self.global_entropy = 0.0
        self.global_entropy_warning = ""
        self._pending_update = False
        self._debounce_timer = None
        self._last_render_data = None
        self._init_layout()
        self._render_suggestions()

    def _init_layout(self):
        layout = Layout([1])
        self.add_layout(layout)
        self.suggestions_label = Label("[OpSec Suggestions will appear here]")
        layout.add_widget(self.suggestions_label)
        self.add_layout(Layout([1]))
        self.fix()

    # ===== Observer interface =====

    def observer_update(self, event_type: str, payload: dict):
        '''
        Called by Observable subjects when an event occurs.
        Updates internal state and schedules a debounced redraw.
        In error state, data is updated but NO redraw occurs.
        '''
        try:
            # Always update data regardless of state
            if event_type == "score_changed":
                self.noise_score = payload.get("score", self.noise_score)
            elif event_type == "tactics_changed":
                if "service" in payload:
                    self.service = payload["service"]
                if "path" in payload:
                    self.pivot_path = payload["path"]
            elif event_type == "profile_changed":
                pass  # profile changes don't directly affect panel display
            elif event_type == "selected_ip_changed":
                # Fetch fresh opsec data from model for the newly selected IP
                ip = payload.get("ip", "")
                if hasattr(self, 'model') and self.model and hasattr(self.model, 'get_opsec_data'):
                    try:
                        data = self.model.get_opsec_data(ip)
                        self.noise_score = data.get("noise_score", self.noise_score)
                        self.service = data.get("service", self.service)
                        self.pivot_path = data.get("pivot_path", self.pivot_path)

                        # Load global entropy
                        if hasattr(self.model, 'repo') and self.model.repo and hasattr(self.model.repo, 'crud'):
                            from core.entropy import calcular_entropia, get_entropy_warning
                            historial = self.model.repo.crud.select_all_actions()
                            self.global_entropy = calcular_entropia(historial)
                            self.global_entropy_warning = get_entropy_warning(self.global_entropy)
                    except Exception:
                        self._state = "error"
                        return

            # If in error state, don't auto-refresh (prevent flicker storm)
            if self._state == "error":
                return

            # Schedule debounced redraw
            self._schedule_debounce()

        except Exception:
            self._state = "error"

    # ===== Debounce logic =====

    def _schedule_debounce(self):
        """Schedule a debounced redraw. Resets timer if called again before flush."""
        self._pending_update = True
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
        self._debounce_timer = threading.Timer(
            self.DEBOUNCE_INTERVAL, self._flush_updates
        )
        self._debounce_timer.daemon = True
        self._debounce_timer.start()

    def _flush_updates(self):
        """Flush pending updates: render suggestions and redraw."""
        self._pending_update = False
        self._debounce_timer = None
        try:
            self._render_suggestions()
            self._redraw()
        except Exception:
            self._state = "error"

    # ===== Manual refresh =====

    def refresh(self):
        """
        Manual refresh: clears error state, re-fetches data from model,
        and immediately redraws. Bypasses debounce.
        """
        # Cancel any pending debounce
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        self._state = "ok"
        self._pending_update = False

        # Re-fetch data from model if available
        if hasattr(self, 'model') and self.model and hasattr(self.model, 'get_opsec_data'):
            try:
                data = self.model.get_opsec_data(
                    getattr(self.model, 'selected_ip', None) or ''
                )
                self.noise_score = data.get("noise_score", self.noise_score)
                self.service = data.get("service", self.service)
                self.pivot_path = data.get("pivot_path", self.pivot_path)
            except Exception:
                self._state = "error"
                return

        self._render_suggestions()
        self._redraw()

    # ===== Rendering =====

    def _render_suggestions(self):
        """Compose the suggestions label text from current state."""
        tips = []
        try:
            if self.noise_score is not None:
                tip = self.opsec.on_noise_score_update(self.noise_score)
                if tip:
                    tips.append(tip)
            if self.pivot_path:
                tips.extend(self.opsec.on_pivot_path_change(self.pivot_path))
            if self.service:
                tips.extend(self.opsec.on_service_selected(self.service))
        except Exception:
            self._state = "error"
            if hasattr(self, 'suggestions_label'):
                self.suggestions_label.text = "[ERROR] Failed to load OpSec suggestions"
            return

        # Compose label
        label = "\n- ".join([str(t) for t in tips if t])
        if not label:
            label = f"[No current OpSec suggestions] (Noise Score: {self.noise_score:.2f})" if self.noise_score is not None else "[No current OpSec suggestions]"
        else:
            label = f"[OpSec Guidance (Noise Score: {self.noise_score:.2f})]\n- " + label if self.noise_score is not None else "[OpSec Guidance]\n- " + label

        if hasattr(self, 'global_entropy_warning') and self.global_entropy_warning:
            label += f"\n\n[Global Entropy: {self.global_entropy:.2f}]\n{self.global_entropy_warning}"

        # Add state indicator
        if self._state == "error":
            label = "[ERROR] " + label
        elif self._state == "pending" or self._pending_update:
            label = "[PENDING] " + label

        if hasattr(self, 'suggestions_label'):
            self.suggestions_label.text = label
            self.suggestions_label.custom_colour = risk_colour_key_for_score(self.noise_score)

        self._last_render_data = dict(
            noise_score=self.noise_score,
            pivot_path=self.pivot_path,
            service=self.service,
            tips=tips,
            state=self._state,
        )

    def _redraw(self):
        """Force UI redraw. Safe to call even without screen."""
        if hasattr(self, 'screen') and self.screen:
            try:
                self.screen.force_update()
            except Exception:
                pass

    # ===== Legacy compatibility =====

    def update_panel(self, noise_score=None, pivot_path=None, service=None):
        """Legacy method for direct updates. Kept for backward compatibility."""
        if noise_score is not None:
            self.noise_score = noise_score
        if pivot_path is not None:
            self.pivot_path = pivot_path
        if service is not None:
            self.service = service
        self._render_suggestions()
        self._redraw()
