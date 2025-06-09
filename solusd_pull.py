import requests
import pandas as pd


def get_binance_data(symbols, interval='1d', limit=365):
    """
    Fetch historical data for multiple cryptocurrencies from Binance US.
    Returns a single DataFrame with an added 'symbol' column.
    """
    all_dfs = []
    for symbol in symbols:
        url = f'https://api.binance.us/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        response = requests.get(url)
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        df['date'] = df['open_time'].dt.date
        df['open'] = df['open'].astype(float)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['volatility'] = df['high'] - df['low']

        # For bid/ask, you need to call the ticker/bookTicker endpoint
        # (current only, not historical)
        bid_ask_url = (
            f'https://api.binance.us/api/v3/ticker/bookTicker?symbol={symbol}'
        )
        bid_ask = requests.get(bid_ask_url).json()
        df['bid'] = float(bid_ask['bidPrice'])
        df['ask'] = float(bid_ask['askPrice'])

        df['symbol'] = symbol  # Add symbol column
        all_dfs.append(df[['open_time','close_time','date', 'symbol', 'open', 'close', 'bid', 'ask', 'volume', 'volatility']])

    # Concatenate all DataFrames
    result_df = pd.concat(all_dfs, ignore_index=True)
    return result_df