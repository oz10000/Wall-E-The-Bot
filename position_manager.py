from datetime import datetime
from config import *
from indicators import atr

class Position:
    def __init__(self, symbol, side, entry, size, tp_init, sl_init, entry_time):
        self.symbol = symbol
        self.side = side
        self.entry = entry
        self.size = size
        self.tp = tp_init
        self.sl = sl_init
        self.entry_time = entry_time
        self.closed = False
        self.exit_price = 0.0
        self.reason = ''
        self.be_activated = False
        self.tp_trail_activated = False
        self.comm_entry = 0.0

    def update(self, current_candle, df_5m):
        close = current_candle['c']
        high = current_candle['h']
        low = current_candle['l']
        elapsed = (datetime.utcnow() - self.entry_time).total_seconds() / 60

        a = atr(df_5m, ATR_PERIOD).iloc[-1]

        # Trailing Take Profit
        if not self.tp_trail_activated:
            if self.side == 'long' and high >= self.tp:
                self.tp_trail_activated = True
                self.sl = close - TP_TRAIL_CALLBACK * a
            elif self.side == 'short' and low <= self.tp:
                self.tp_trail_activated = True
                self.sl = close + TP_TRAIL_CALLBACK * a

        if self.tp_trail_activated:
            if self.side == 'long':
                new_sl = close - TP_TRAIL_CALLBACK * a
                if new_sl > self.sl:
                    self.sl = new_sl
            else:
                new_sl = close + TP_TRAIL_CALLBACK * a
                if new_sl < self.sl:
                    self.sl = new_sl

        # Break Even con beneficio real
        if not self.be_activated and not self.tp_trail_activated:
            if elapsed >= BREAK_EVEN_MINUTES:
                if self.side == 'long' and close > self.entry * (1 + 0.001):
                    self.be_activated = True
                    self.sl = self.entry * (1 + BREAK_EVEN_BUFFER / 100)
                elif self.side == 'short' and close < self.entry * (1 - 0.001):
                    self.be_activated = True
                    self.sl = self.entry * (1 - BREAK_EVEN_BUFFER / 100)

        # Cierre por SL
        if self.side == 'long' and low <= self.sl:
            self.exit_price = self.sl * (1 - SLIPPAGE_PCT)
            self.reason = 'SL'
            self.closed = True
            return True
        elif self.side == 'short' and high >= self.sl:
            self.exit_price = self.sl * (1 + SLIPPAGE_PCT)
            self.reason = 'SL'
            self.closed = True
            return True

        if elapsed >= MAX_HOLD_MINUTES:
            self.exit_price = close
            self.reason = 'Timeout'
            self.closed = True
            return True

        return False
