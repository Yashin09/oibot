import json
import os
from datetime import datetime

def save_state(tracker, filename='oi_state.json'):
    """Сохранить состояние трекера в файл"""
    data = {}
    for symbol, state in tracker.states.items():
        data[symbol] = {
            'history': [
                {
                    'timestamp': snap.timestamp.isoformat(),
                    'open_interest': snap.open_interest,
                    'price': snap.price
                }
                for snap in state.history
            ],
            'last_alert_level': state.last_alert_level,
            'alert_baseline_oi': state.alert_baseline_oi,
            'first_baseline_oi': state.first_baseline_oi
        }

    with open(filename, 'w') as f:
        json.dump(data, f)
    print(f"State saved: {len(data)} symbols")

def load_state(tracker, filename='oi_state.json'):
    """Загрузить состояние трекера из файла"""
    if not os.path.exists(filename):
        return

    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        for symbol, state_data in data.items():
            state = tracker.get_or_create_state(symbol)

            # Восстанавливаем историю
            for snap_data in state_data.get('history', []):
                from tracker import OISnapshot
                snapshot = OISnapshot(
                    timestamp=datetime.fromisoformat(snap_data['timestamp']),
                    open_interest=snap_data['open_interest'],
                    price=snap_data['price']
                )
                state.add_snapshot(snapshot)

            state.last_alert_level = state_data.get('last_alert_level')
            state.alert_baseline_oi = state_data.get('alert_baseline_oi')
            state.first_baseline_oi = state_data.get('first_baseline_oi')

        print(f"State loaded: {len(data)} symbols")
    except Exception as e:
        print(f"Failed to load state: {e}")
