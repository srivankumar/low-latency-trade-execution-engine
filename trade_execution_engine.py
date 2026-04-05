"""Trade Execution Engine — public API that ties the system together.

This is the main entry point for users of the library.

Example::

    engine = TradeExecutionEngine()
    engine.place_order(OrderType.BUY,  quantity=100, price=50)
    engine.place_order(OrderType.SELL, quantity=50,  price=45)
    # After each order placement the engine automatically tries to match.
"""

from typing import List

from matching_engine import MatchingEngine
from order import Order, OrderType
from order_book import OrderBook
from trade import Trade


class TradeExecutionEngine:
    """
    Low-latency trade execution engine.

    All state is held in memory.  Matching runs on every new order so that
    latency between order placement and trade execution is minimised.
    """

    def __init__(self) -> None:
        self._order_book = OrderBook()
        self._matching_engine = MatchingEngine(self._order_book)
        self._trade_log: List[Trade] = []
        self._next_order_id: int = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place_order(
        self, order_type: OrderType, quantity: int, price: float
    ) -> Order:
        """
        Add a new order to the book and immediately attempt matching.

        Parameters
        ----------
        order_type: OrderType
            ``OrderType.BUY`` or ``OrderType.SELL``.
        quantity:
            Number of shares (must be > 0).
        price:
            Limit price per share in ₹ (must be > 0).

        Returns
        -------
        Order
            The newly created order object.
        """
        order = Order(
            order_id=self._next_order_id,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        self._next_order_id += 1
        self._order_book.add_order(order)

        # Run the matching engine after every new order.
        new_trades = self._matching_engine.match()
        self._trade_log.extend(new_trades)

        for trade in new_trades:
            print(trade.display())

        return order

    def get_trade_log(self) -> List[Trade]:
        """Return all trades executed so far."""
        return list(self._trade_log)

    def get_order_book(self) -> OrderBook:
        """Return the current state of the order book."""
        return self._order_book

    def display_order_book(self) -> None:
        """Print the current order book to stdout."""
        print(self._order_book)

    def display_trade_log(self) -> None:
        """Print all executed trades to stdout."""
        if not self._trade_log:
            print("No trades executed yet.")
            return
        print("=== Trade Log ===")
        for trade in self._trade_log:
            print(f"  {trade.display()}")
