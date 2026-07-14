import numpy as np
from config import *

class RiskManager:
    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.kill_switch = False

    def update_capital(self, balance):
        self.current_capital = balance
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

    def check_kill_switch(self):
        if self.peak_capital == 0:
            return False
        dd_pct = (self.peak_capital - self.current_capital) / self.peak_capital * 100
        if dd_pct >= KILL_SWITCH_DD_PCT:
            self.kill_switch = True
            return True
        return False

    def calculate_size(self, entry_price, symbol):
        if self.kill_switch:
            return 0.0
        dd = (self.peak_capital - self.current_capital) / self.peak_capital * 100 if self.peak_capital > 0 else 0
        if dd < 5:
            size_factor = 1.0
        elif dd < 10:
            size_factor = 0.6
        else:
            size_factor = 0.2

        base_qty = (self.current_capital * LEVERAGE) / entry_price * size_factor
        spec = INSTRUMENT_SPECS.get(symbol, {})
        min_sz = spec.get('minSz', 0.001)
        lot_sz = spec.get('lotSz', 0.001)
        if base_qty < min_sz:
            return 0.0
        qty = round(base_qty / lot_sz) * lot_sz
        return qty
