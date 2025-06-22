import pandas as pd
import requests
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_binance_data(symbols, interval='1d', limit=365):
    """
    Fetch historical data for multiple cryptocurrencies from Binance US.
    Returns a single DataFrame with an added 'symbol' column.
    """
    all_dfs = []
    for symbol in symbols:
        url = f'https://api.binance.us/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch data for {symbol}: {response.status_code}")
            continue
        try:
            data = response.json()
        except Exception as e:
            logger.exception(f"Error parsing JSON for {symbol}: {e}")
            continue

        if not isinstance(data, list):
            logger.error(f"Unexpected data format for {symbol}: {data}")
            continue

        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(
            df['close_time'],
            unit='ms'
        )
        # Short date format (YYYY-MM-DD)
        df['date'] = df['open_time'].dt.strftime('%Y-%m-%d')
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        # Handle NaNs explicitly before calculating volatility
        df['volatility'] = (df['high'].fillna(0) - df['low'].fillna(0)).where(df['high'].notna() & df['low'].notna(), float('nan'))
        df['volatility'] = df['high'] - df['low']

        # Optionally, fetch bid/ask for each symbol
        # (current only, not historical)
        try:
            ticker_url = f'https://api.binance.us/api/v3/ticker/bookTicker?symbol={symbol}'
            ticker_resp = requests.get(ticker_url)
            bid_ask = ticker_resp.json()
            if not df.empty and isinstance(bid_ask, dict):
                df['bid'] = float(bid_ask.get('bidPrice', np.nan))
                df['ask'] = float(bid_ask.get('askPrice', np.nan))
            else:
                df['bid'] = np.nan
                df['ask'] = np.nan
        except Exception:
            df['bid'] = None
            df['ask'] = None

        df['symbol'] = symbol
        all_dfs.append(df)

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()
