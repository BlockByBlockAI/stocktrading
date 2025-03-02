import json
import os
from pathlib import Path

def load_trades():
    """Load trades from JSON file"""
    trades_file = Path("data/paper_trades.json")
    
    if not trades_file.exists():
        trades_file.parent.mkdir(exist_ok=True)
        return []
    
    try:
        with open(trades_file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_trades(trades):
    """Save trades to JSON file"""
    trades_file = Path("data/paper_trades.json")
    trades_file.parent.mkdir(exist_ok=True)
    
    with open(trades_file, 'w') as f:
        json.dump(trades, f, indent=4)
