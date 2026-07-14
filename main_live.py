#!/usr/bin/env python3
import time, threading
from datetime import datetime, timedelta
import pandas as pd
from config import *
from exchange_okx import OKXClient
from strategy_rama_b import StrategyRamaB
from position_manager import Position
from risk_manager import RiskManager

class TradingBot:
    def __init__(self):
        self.exchange = OKXClient()
        self.strategy = StrategyRamaB(self.exchange)
        self.risk_mgr = RiskManager(INITIAL_CAPITAL)
        self.open_positions = []
        self.running = True

    def fetch_data(self):
        data_5m, data_15m = {}, {}
        for sym in UNIVERSO:
            df5 = self.exchange.fetch_candles(sym, '5m', 200)
            if df5 is not None and len(df5) >= 60:
                data_5m[sym] = df5
                # Generar 15m a partir de 5m
                df5_indexed = df5.set_index('ts')
                df15 = df5_indexed['c'].resample('15min', label='right').last().dropna()
                if len(df15) >= 20:
                    data_15m[sym] = pd.DataFrame({'c': df15})
        return data_5m, data_15m

    def update_open_positions(self):
        for pos in self.open_positions[:]:
            if pos.closed:
                continue
            df5 = self.exchange.fetch_candles(pos.symbol, '5m', 2)
            if df5 is None or len(df5) == 0:
                continue
            full_df = self.exchange.fetch_candles(pos.symbol, '5m', 200)
            if full_df is None:
                continue
            if pos.update(df5.iloc[-1], full_df):
                # Cerrar posición en exchange
                positions = self.exchange.get_positions()
                for p in positions:
                    if p['instId'] == f'{pos.symbol}-USDT-SWAP' and p['posSide'] == pos.side:
                        self.exchange.close_position(pos.symbol, p['posId'])
                        break
                print(f"🔒 {pos.symbol} cerrado: {pos.reason} @ {pos.exit_price}")
                self.open_positions.remove(pos)

    def run(self):
        print("🚀 KRISHNA OMEGA ULTRA - BOT INICIADO (RAMA B)")
        while self.running:
            now = datetime.utcnow()
            if now.hour < 14 and now.hour > 0:   # sesión UTC 14-0h
                time.sleep(60)
                continue

            balance = self.exchange.get_balance()
            self.risk_mgr.update_capital(balance)
            if self.risk_mgr.check_kill_switch():
                print("🛑 KILL SWITCH ACTIVADO.")
                self.running = False
                break

            data_5m, data_15m = self.fetch_data()
            self.update_open_positions()

            if len([p for p in self.open_positions if not p.closed]) >= MAX_POSITIONS:
                time.sleep(30)
                continue

            signal = self.strategy.generate_signal(data_5m, data_15m)
            if signal:
                size = self.risk_mgr.calculate_size(signal['entry'], signal['symbol'])
                if size > 0:
                    side = 'buy' if signal['direction'] == 'Long' else 'sell'
                    resp = self.exchange.place_order(signal['symbol'], side, size,
                                                     signal['tp'], signal['sl'])
                    if resp.get('code') == '0':
                        print(f"✅ Orden: {signal['symbol']} {signal['direction']} x{size}")
                        pos = Position(signal['symbol'], signal['direction'].lower(),
                                       signal['entry'], size, signal['tp'], signal['sl'],
                                       datetime.utcnow())
                        self.open_positions.append(pos)
                    else:
                        print(f"❌ Error orden: {resp}")

            next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=5)
            sleep_secs = (next_run - datetime.utcnow()).total_seconds()
            if sleep_secs > 0:
                time.sleep(sleep_secs)

if __name__ == '__main__':
    TradingBot().run()
