import os

# Telegram
TELEGRAM_TOKEN = "8751436206:AAHiK0wlVwa0-mpSwyAIZvZwxNHU02bQuvY"
ADMIN_ID = 855255816

# Bybit (можно оставить пустым для публичных данных)
BYBIT_API_KEY = ""
BYBIT_API_SECRET = ""

# Настройки бота
TRACKING_INTERVAL = 60  # секунд
BASE_PERIOD = 4  # часа
FIRST_ALERT_THRESHOLD = 20  # %
SUBSEQUENT_ALERT_STEP = 5  # %
MIN_OI_USD = 500000

# Монеты для отслеживания (None = все)
TRACKED_SYMBOLS = None
