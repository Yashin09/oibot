import telepot
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self, token: str, admin_id: int):
        self.bot = telepot.Bot(token)
        self.admin_id = admin_id

    def send_oi_alert(self, 
                     chat_id: int,
                     symbol: str,
                     change_percent: float,
                     level: float,
                     alert_type: str,
                     baseline_oi: float,
                     current_oi: float,
                     from_baseline_percent: float,
                     price: float,
                     funding_rate: float,
                     long_pct: float,
                     short_pct: float,
                     mark_price: float,
                     volume_24h: float):

        change_emoji = "🟢" if change_percent > 0 else "🔴"
        baseline_m = baseline_oi / 1_000_000
        current_m = current_oi / 1_000_000

        if alert_type == "first":
            oi_line = f"OI: {change_emoji}+{change_percent:.2f}% (${baseline_m:.2f}M → ${current_m:.2f}M)"
        else:
            oi_line = f"OI: {change_emoji}+{change_percent:.2f}% (+{from_baseline_percent:.2f}% от прошлого)"

        ls_green = "🟢"
        ls_red = "🔴"
        time_str = datetime.utcnow().strftime("%H:%M")
        funding_pct = funding_rate * 100

        message = f"""<b>OI bot</b> | <i>OI alpha</i>

<code>${symbol}</code> | Bybit
{oi_line}

💵 Цена: ${price:.6f}
⚡ Funding: {funding_pct:+.4f}%
📊 L/S: {ls_green} {long_pct:.1f}% / {ls_red} {short_pct:.1f}%
📦 Mark: ${mark_price:.6f} (short)
📦 Vol: ${volume_24h/1_000_000:.2f}M

{time_str} UTC"""

        try:
            self.bot.sendMessage(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info(f"Sent alert to {chat_id}: {symbol} +{change_percent:.2f}%")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def send_startup_message(self, chat_id: int, symbols_count: int):
        message = f"""🤖 <b>OI Bot запущен</b>

Отслеживаю {symbols_count} монет
Период: 4ч | Порог: 20% | Шаг: 5%

Ожидаю изменения OI..."""
        self.bot.sendMessage(chat_id=chat_id, text=message, parse_mode="HTML")

    def send_error(self, chat_id: int, error: str):
        self.bot.sendMessage(chat_id=chat_id, text=f"❌ Ошибка: {error}")
