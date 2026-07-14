import time, hmac, base64, json, requests
from datetime import datetime
import pandas as pd
from config import *

class OKXClient:
    def __init__(self):
        self.api_key = OKX_API_KEY
        self.secret = OKX_SECRET_KEY
        self.passphrase = OKX_PASSPHRASE
        self.base_url = "https://www.okx.com"
        self.demo = OKX_DEMO

    def _sign(self, timestamp, method, request_path, body=''):
        message = f'{timestamp}{method}{request_path}{body}'
        mac = hmac.new(self.secret.encode(), message.encode(), 'sha256').digest()
        return base64.b64encode(mac).decode()

    def _request(self, method, path, params=None, body=None):
        timestamp = str(int(time.time()))
        body_str = json.dumps(body) if body else ''
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': self._sign(timestamp, method, path, body_str),
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json',
        }
        if self.demo:
            headers['x-simulated-trading'] = '1'
        url = self.base_url + path
        resp = requests.request(method, url, params=params, data=body_str, headers=headers)
        return resp.json()

    def fetch_candles(self, symbol, bar='5m', limit=200):
        path = '/api/v5/market/candles'
        params = {'instId': f'{symbol}-USDT-SWAP', 'bar': bar, 'limit': limit}
        resp = self._request('GET', path, params=params)
        data = resp.get('data', [])
        if not data:
            return None
        rows = []
        for d in reversed(data):
            ts = datetime.fromtimestamp(int(d[0]) / 1000)
            rows.append([ts, float(d[1]), float(d[2]), float(d[3]), float(d[4]), float(d[5])])
        return pd.DataFrame(rows, columns=['ts', 'o', 'h', 'l', 'c', 'vol'])

    def get_positions(self):
        path = '/api/v5/account/positions'
        params = {'instType': 'SWAP'}
        resp = self._request('GET', path, params=params)
        return resp.get('data', [])

    def place_order(self, symbol, side, sz, tp_price, sl_price):
        path = '/api/v5/trade/order'
        body = {
            'instId': f'{symbol}-USDT-SWAP',
            'tdMode': 'isolated',
            'side': side,
            'ordType': 'market',
            'sz': str(sz),
            'tpTriggerPx': str(tp_price),
            'tpOrdPx': str(tp_price),
            'slTriggerPx': str(sl_price),
            'slOrdPx': str(sl_price),
        }
        resp = self._request('POST', path, body=body)
        return resp

    def close_position(self, symbol, pos_id):
        path = '/api/v5/trade/close-position'
        body = {
            'instId': f'{symbol}-USDT-SWAP',
            'posId': pos_id,
            'mgnMode': 'isolated',
        }
        resp = self._request('POST', path, body=body)
        return resp

    def get_balance(self, ccy='USDT'):
        path = '/api/v5/account/balance'
        params = {'ccy': ccy}
        resp = self._request('GET', path, params=params)
        details = resp.get('data', [{}])[0].get('details', [])
        for d in details:
            if d['ccy'] == ccy:
                return float(d['availBal'])
        return 0.0
