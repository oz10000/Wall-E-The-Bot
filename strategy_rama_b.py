import pandas as pd
import numpy as np
from indicators import *
from config import *

class StrategyRamaB:
    def __init__(self, exchange):
        self.exchange = exchange

    def generate_signal(self, data_5m, data_15m):
        best_rank = -1e9
        best_signal = None

        for symbol in UNIVERSO:
            if symbol not in data_5m or symbol not in data_15m:
                continue
            df5 = data_5m[symbol]
            if len(df5) < 60:
                continue

            sc = compute_score(df5)
            if abs(sc) < MIN_SCORE:
                continue

            adx_val = adx(df5, ADX_THRESHOLD).iloc[-1]
            ker_val = ker(df5['c'], KER_PERIOD).iloc[-1]
            if adx_val < ADX_THRESHOLD or ker_val < KER_THRESHOLD:
                continue

            regime = classify_regime(df5)
            if regime in ['Chop', 'Compresión']:
                continue

            # Confirmación 15m
            df15 = data_15m[symbol]
            if len(df15) < 20:
                continue
            ema_15 = df15['c'].ewm(span=20, adjust=False).mean().iloc[-1]
            direction = 'Long' if sc > 0 else 'Short'
            if direction == 'Long' and df5.iloc[-1]['c'] < ema_15:
                continue
            if direction == 'Short' and df5.iloc[-1]['c'] > ema_15:
                continue

            atr_val = atr(df5, ATR_PERIOD).iloc[-1]
            macro_val = macro(df5, MACRO_LOOKBACK).iloc[-1]
            mom_val = df5['c'].pct_change(MOMENTUM_PERIOD).iloc[-1] * 100
            vw_z = abs(vwap_zscore(df5, VWAP_PERIOD).iloc[-1]) / 3.0
            atr_rel_norm = min(1.0, atr_val / df5.iloc[-1]['c'] * 100 / 3.5)
            adx_norm = min(1.0, adx_val / 40.0)
            mom_norm = min(1.0, abs(mom_val) / 5.0)

            rank = (abs(sc) * 0.25 + adx_norm * 0.20 + ker_val * 0.15 +
                    macro_val * 0.10 + atr_rel_norm * 0.10 + vw_z * 0.10 + mom_norm * 0.10)

            if rank > best_rank:
                best_rank = rank
                entry = df5.iloc[-1]['c']
                if direction == 'Long':
                    tp = entry + atr_val * TP_MULT_INIT
                    sl = entry - atr_val * SL_MULT
                else:
                    tp = entry - atr_val * TP_MULT_INIT
                    sl = entry + atr_val * SL_MULT

                best_signal = {
                    'symbol': symbol,
                    'direction': direction,
                    'entry': entry,
                    'tp': tp,
                    'sl': sl,
                    'score': sc,
                    'atr': atr_val,
                    'regime': regime
                }
        return best_signal
