import time
import logging
from config import (
    TELEGRAM_TOKEN, ADMIN_ID, BYBIT_API_KEY, BYBIT_API_SECRET,
    TRACKING_INTERVAL, BASE_PERIOD, FIRST_ALERT_THRESHOLD, 
    SUBSEQUENT_ALERT_STEP, MIN_OI_USD, TRACKED_SYMBOLS
)
from bybit_client import BybitClient
from tracker import OITracker
from telegram_sender import TelegramSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OIBot:
    def __init__(self):
        self.telegram = TelegramSender(TELEGRAM_TOKEN, ADMIN_ID)
        self.tracker = OITracker(
            base_period=BASE_PERIOD,
            first_threshold=FIRST_ALERT_THRESHOLD,
            step=SUBSEQUENT_ALERT_STEP
        )
        self.tracked_symbols = TRACKED_SYMBOLS or []
        self.is_running = False
        self.client = BybitClient(BYBIT_API_KEY, BYBIT_API_SECRET)

    def initialize_symbols(self):
        if not self.tracked_symbols:
            logger.info("Fetching all linear symbols...")
            symbols = self.client.get_linear_symbols()
            self.tracked_symbols = [s for s in symbols if s.endswith("USDT")]
            logger.info(f"Found {len(self.tracked_symbols)} symbols")

        self.telegram.send_startup_message(ADMIN_ID, len(self.tracked_symbols))

    def process_symbol(self, symbol: str):
        try:
            data = self.client.get_market_data(symbol)
            if not data:
                return

            if data.open_interest < MIN_OI_USD / data.price:
                return

            state = self.tracker.update_symbol(symbol, data.open_interest, data.price)
            alert = self.tracker.check_alert(symbol, data.open_interest)

            if alert:
                short_pct = 100 - data.long_short_ratio
                self.telegram.send_oi_alert(
                    chat_id=ADMIN_ID,
                    symbol=symbol.replace("USDT", ""),
                    change_percent=alert["change_percent"],
                    level=alert["level"],
                    alert_type=alert["type"],
                    baseline_oi=alert["baseline_oi"],
                    current_oi=alert["current_oi"],
                    from_baseline_percent=alert.get("from_baseline_percent", alert["change_percent"]),
                    price=data.price,
                    funding_rate=data.funding_rate,
                    long_pct=data.long_short_ratio,
                    short_pct=short_pct,
                    mark_price=data.mark_price,
                    volume_24h=data.volume_24h
                )

        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")

    def run(self):
        self.is_running = True

        self.initialize_symbols()
        logger.info("Collecting initial data (need 4 hours of history)...")

        iteration = 0
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"Iteration {iteration}, checking {len(self.tracked_symbols)} symbols...")

                for symbol in self.tracked_symbols:
                    self.process_symbol(symbol)

                if iteration % 10 == 0:
                    active_states = sum(1 for s in self.tracker.states.values() if len(s.history) > 0)
                    logger.info(f"Active symbols: {active_states}/{len(self.tracked_symbols)}")

                time.sleep(TRACKING_INTERVAL)

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(10)

    def stop(self):
        self.is_running = False

def main():
    bot = OIBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        bot.stop()

if __name__ == "__main__":
    main()
