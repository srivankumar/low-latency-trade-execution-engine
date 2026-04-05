"""Interactive CLI for the Low-Latency Trade Execution Engine.

Usage:
    python main.py          # interactive mode
    python main.py --demo   # runs the built-in demonstration
"""

import sys

from order import OrderType
from trade_execution_engine import TradeExecutionEngine


# ---------------------------------------------------------------------------
# Demo scenario
# ---------------------------------------------------------------------------

def run_demo(engine: TradeExecutionEngine) -> None:
    """Run the example from the problem statement plus a few extra cases."""
    print("=" * 60)
    print(" Low-Latency Trade Execution Engine — Demo")
    print("=" * 60)

    print("\n--- Placing orders ---\n")

    # Problem-statement example
    print("Placing: BUY  100 shares @ ₹50")
    engine.place_order(OrderType.BUY, quantity=100, price=50)

    print("Placing: SELL  50 shares @ ₹45")
    engine.place_order(OrderType.SELL, quantity=50, price=45)

    print("\n--- Order Book after first match ---")
    engine.display_order_book()

    # Additional orders
    print("\nPlacing: SELL  30 shares @ ₹48")
    engine.place_order(OrderType.SELL, quantity=30, price=48)

    print("Placing: BUY   20 shares @ ₹47")
    engine.place_order(OrderType.BUY, quantity=20, price=47)

    print("Placing: SELL  10 shares @ ₹55  (no match — ask > best bid)")
    engine.place_order(OrderType.SELL, quantity=10, price=55)

    print("\n--- Final Order Book ---")
    engine.display_order_book()

    print()
    engine.display_trade_log()
    print()


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

HELP_TEXT = """
Commands:
  buy  <qty> <price>   Place a BUY order
  sell <qty> <price>   Place a SELL order
  book                 Show the current order book
  trades               Show all executed trades
  help                 Show this help message
  quit / exit          Exit
"""


def run_interactive(engine: TradeExecutionEngine) -> None:
    print("=" * 60)
    print(" Low-Latency Trade Execution Engine — Interactive Mode")
    print("=" * 60)
    print(HELP_TEXT)

    while True:
        try:
            raw = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            print("Goodbye!")
            break

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "book":
            engine.display_order_book()

        elif cmd == "trades":
            engine.display_trade_log()

        elif cmd in ("buy", "sell"):
            if len(parts) != 3:
                print(f"Usage: {cmd} <quantity> <price>")
                continue
            try:
                qty = int(parts[1])
                price = float(parts[2])
            except ValueError:
                print("quantity must be an integer and price must be a number.")
                continue
            order_type = OrderType.BUY if cmd == "buy" else OrderType.SELL
            order = engine.place_order(order_type, quantity=qty, price=price)
            remaining = order.quantity
            if remaining > 0:
                print(
                    f"  ↳ Order {order.order_id} resting in book "
                    f"(remaining qty: {remaining})"
                )
            else:
                print(f"  ↳ Order {order.order_id} fully filled.")

        else:
            print(f"Unknown command '{cmd}'. Type 'help' for available commands.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = TradeExecutionEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo(engine)
    else:
        run_interactive(engine)
