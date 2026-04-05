# Low-Latency Trade Execution Engine

A fast, in-memory stock-exchange simulation that processes buy and sell orders and executes trades instantly using price-time priority — just like a real exchange matching engine.

---

## What it does

- Accepts **BUY** and **SELL** limit orders
- Matches orders when `BUY price ≥ SELL price`
- Executes trades at the **sell-order price** (sell-side price protection)
- Supports **partial fills** — unmatched quantity stays in the order book
- Enforces **price-time priority**: higher price wins; ties broken by arrival time

### Example

```
BUY  100 shares @ ₹50
SELL  50 shares @ ₹45
→ Trade executed: 50 shares at ₹45   (remaining BUY: 50 shares)
```

---

## Architecture

| File | Responsibility |
|---|---|
| `order.py` | `Order` dataclass — id, type, quantity, price, timestamp |
| `order_book.py` | `OrderBook` — buy max-heap + sell min-heap |
| `matching_engine.py` | `MatchingEngine` — continuous matching loop |
| `trade.py` | `Trade` dataclass — records each executed trade |
| `trade_execution_engine.py` | `TradeExecutionEngine` — public API |
| `main.py` | CLI entry point (interactive + demo mode) |
| `tests.py` | 31 unit / integration tests |

### Priority rules

- **BUY side** — max-heap (highest price first → earliest timestamp on ties)
- **SELL side** — min-heap (lowest price first → earliest timestamp on ties)

---

## Running

### Demo mode

```bash
python main.py --demo
```

### Interactive mode

```bash
python main.py
```

Available commands:

```
buy  <qty> <price>   Place a BUY order
sell <qty> <price>   Place a SELL order
book                 Show the current order book
trades               Show all executed trades
help                 Show help
quit / exit          Exit
```

### Run tests

```bash
python -m unittest tests -v
```

---

## Requirements

Python 3.8+ (standard library only — no external dependencies).
