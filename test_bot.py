#!/usr/bin/env python3
"""Smoke test: verifica que todos los módulos se importan y la estrategia no falla con datos mínimos."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Verificar imports
try:
    from config import *
    from indicators import *
    from exchange_okx import OKXClient
    from strategy_rama_b import StrategyRamaB
    from position_manager import Position
    from risk_manager import RiskManager
    print("✅ Todos los módulos importados correctamente")
except Exception as e:
    print(f"❌ Error de importación: {e}")
    exit(1)

# Generar datos sintéticos para probar la estrategia
def generar_datos(n=200, symbol='BTC'):
    np.random.seed(42)
    base = 30000 if symbol == 'BTC' else 2000
    ts = pd.date_range(end=datetime.utcnow(), periods=n, freq='5min')
    df = pd.DataFrame({
        'ts': ts,
        'o': base + np.random.normal(0, 50, n).cumsum(),
        'h': base + np.random.normal(0, 50, n).cumsum() + abs(np.random.normal(20, 5, n)),
        'l': base + np.random.normal(0, 50, n).cumsum() - abs(np.random.normal(20, 5, n)),
        'c': base + np.random.normal(0, 50, n).cumsum(),
        'vol': np.random.uniform(100, 1000, n)
    })
    df['h'] = df[['h','c','o']].max(axis=1)
    df['l'] = df[['l','c','o']].min(axis=1)
    return df

# Crear datos mínimos
data_5m = {sym: generar_datos(200, sym) for sym in UNIVERSO}
# Generar 15m resampleado (igual que en el bot)
data_15m = {}
for sym, df in data_5m.items():
    df_idx = df.set_index('ts')
    df15 = df_idx['c'].resample('15min', label='right').last().dropna()
    data_15m[sym] = pd.DataFrame({'c': df15})

# Instanciar la estrategia sin exchange real (solo para test lógico)
from types import SimpleNamespace
mock_exchange = SimpleNamespace()
strategy = StrategyRamaB(mock_exchange)

signal = strategy.generate_signal(data_5m, data_15m)
if signal is not None:
    print(f"✅ Señal generada: {signal['symbol']} {signal['direction']} (score={signal['score']:.3f})")
else:
    print("ℹ️ No se generó señal (posible en datos aleatorios)")

print("✅ Smoke test completado con éxito")
