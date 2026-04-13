from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class OISnapshot:
    timestamp: datetime
    open_interest: float
    price: float

@dataclass
class SymbolState:
    symbol: str
    history: deque = field(default_factory=lambda: deque(maxlen=500))
    last_alert_level: Optional[float] = None
    alert_baseline_oi: Optional[float] = None
    last_alert_time: Optional[datetime] = None
    first_baseline_oi: Optional[float] = None

    def add_snapshot(self, snapshot: OISnapshot):
        self.history.append(snapshot)

    def get_snapshot_n_hours_ago(self, hours: int) -> Optional[OISnapshot]:
        target_time = datetime.utcnow() - timedelta(hours=hours)
        closest = None
        min_diff = timedelta(hours=1)

        for snap in self.history:
            diff = abs(snap.timestamp - target_time)
            if diff < min_diff:
                min_diff = diff
                closest = snap

        if closest and min_diff <= timedelta(minutes=15):
            return closest
        return None

    def calculate_change_percent(self, current_oi: float, hours: int = 4) -> Optional[float]:
        old_snapshot = self.get_snapshot_n_hours_ago(hours)
        if not old_snapshot or old_snapshot.open_interest == 0:
            return None

        return ((current_oi - old_snapshot.open_interest) / old_snapshot.open_interest) * 100

class OITracker:
    def __init__(self, base_period: int = 4, first_threshold: float = 20, step: float = 5):
        self.base_period = base_period
        self.first_threshold = first_threshold
        self.step = step
        self.states: Dict[str, SymbolState] = {}

    def get_or_create_state(self, symbol: str) -> SymbolState:
        if symbol not in self.states:
            self.states[symbol] = SymbolState(symbol=symbol)
        return self.states[symbol]

    def update_symbol(self, symbol: str, current_oi: float, current_price: float):
        state = self.get_or_create_state(symbol)
        snapshot = OISnapshot(
            timestamp=datetime.utcnow(),
            open_interest=current_oi,
            price=current_price
        )
        state.add_snapshot(snapshot)
        return state

    def check_alert(self, symbol: str, current_oi: float) -> Optional[Dict]:
        state = self.get_or_create_state(symbol)

        change_percent = state.calculate_change_percent(current_oi, self.base_period)
        if change_percent is None:
            return None

        now = datetime.utcnow()

        # Первый алерт
        if state.last_alert_level is None:
            if change_percent >= self.first_threshold:
                old_snapshot = state.get_snapshot_n_hours_ago(self.base_period)
                state.last_alert_level = self.first_threshold
                state.alert_baseline_oi = current_oi
                state.first_baseline_oi = old_snapshot.open_interest if old_snapshot else current_oi
                state.last_alert_time = now
                return {
                    "type": "first",
                    "level": self.first_threshold,
                    "change_percent": change_percent,
                    "baseline_oi": state.first_baseline_oi,
                    "current_oi": current_oi,
                    "from_baseline_percent": change_percent
                }
            return None

        # Последующие алерты
        if state.alert_baseline_oi and state.alert_baseline_oi > 0:
            growth_from_baseline = ((current_oi - state.alert_baseline_oi) / state.alert_baseline_oi) * 100
            next_threshold = state.last_alert_level + self.step

            if growth_from_baseline >= self.step:
                old_baseline = state.alert_baseline_oi
                state.last_alert_level = next_threshold
                state.alert_baseline_oi = current_oi
                state.last_alert_time = now

                return {
                    "type": "subsequent",
                    "level": next_threshold,
                    "change_percent": change_percent,
                    "baseline_oi": old_baseline,
                    "current_oi": current_oi,
                    "from_baseline_percent": growth_from_baseline
                }

        return None

    def reset_symbol(self, symbol: str):
        if symbol in self.states:
            old_state = self.states[symbol]
            new_state = SymbolState(symbol=symbol)
            new_state.history = old_state.history
            self.states[symbol] = new_state
            logger.info(f"Reset alerts for {symbol}")
