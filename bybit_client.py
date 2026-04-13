import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    symbol: str
    open_interest: float
    price: float
    funding_rate: float
    long_short_ratio: float
    mark_price: float
    volume_24h: float
    timestamp: datetime

class BybitClient:
    BASE_URL = "https://api.bybit.com/v5"

    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

    def get_linear_symbols(self) -> List[str]:
        url = f"{self.BASE_URL}/market/instruments-info"
        params = {"category": "linear"}

        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("retCode") == 0:
                symbols = []
                for item in data["result"]["list"]:
                    if item.get("status") == "Trading":
                        symbols.append(item["symbol"])
                return symbols
            return []
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []

    def get_ticker_data(self, symbol: str) -> Optional[Dict]:
        url = f"{self.BASE_URL}/market/tickers"
        params = {"category": "linear", "symbol": symbol}

        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("retCode") == 0 and data["result"]["list"]:
                return data["result"]["list"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None

    def get_open_interest(self, symbol: str, interval: str = "5min") -> Optional[float]:
        url = f"{self.BASE_URL}/market/open-interest"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": 1
        }

        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("retCode") == 0 and data["result"]["list"]:
                return float(data["result"]["list"][0]["openInterest"])
            return None
        except Exception as e:
            logger.error(f"Error fetching OI for {symbol}: {e}")
            return None

    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        ticker = self.get_ticker_data(symbol)
        oi = self.get_open_interest(symbol)

        if not ticker or oi is None:
            return None

        try:
            ls_ratio = float(ticker.get("longShortRatio", 1.0))
            long_pct = ls_ratio / (1 + ls_ratio) * 100

            return MarketData(
                symbol=symbol,
                open_interest=oi,
                price=float(ticker.get("lastPrice", 0)),
                funding_rate=float(ticker.get("fundingRate", 0)),
                long_short_ratio=long_pct,
                mark_price=float(ticker.get("markPrice", 0)),
                volume_24h=float(ticker.get("volume24h", 0)),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error parsing data for {symbol}: {e}")
            return None
