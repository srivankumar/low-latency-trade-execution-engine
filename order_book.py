"""Order Book — stores and prioritises buy and sell orders.

Priority rules (price-time priority):
  BUY  side  → max-heap  (highest price first; ties broken by earliest timestamp)
  SELL side  → min-heap  (lowest price first;  ties broken by earliest timestamp)
"""

import heapq
from typing import List, Optional, Tuple

from order import Order, OrderType


class OrderBook:
    """
    Maintains two priority queues — one for buy orders and one for sell orders.

    Heap entry layout
    -----------------
    BUY  heap:  (-price, timestamp, order)   — negated so Python's min-heap behaves as max-heap
    SELL heap:  ( price, timestamp, order)
    """

    def __init__(self) -> None:
        self._buy_heap: List[Tuple] = []   # max-heap (negated price)
        self._sell_heap: List[Tuple] = []  # min-heap

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_order(self, order: Order) -> None:
        """Push an order onto the appropriate heap."""
        if order.order_type == OrderType.BUY:
            heapq.heappush(self._buy_heap, (-order.price, order.timestamp, order))
        else:
            heapq.heappush(self._sell_heap, (order.price, order.timestamp, order))

    def best_buy(self) -> Optional[Order]:
        """Return the highest-priority buy order without removing it."""
        while self._buy_heap:
            _, _, order = self._buy_heap[0]
            if order.quantity > 0:
                return order
            heapq.heappop(self._buy_heap)
        return None

    def best_sell(self) -> Optional[Order]:
        """Return the highest-priority sell order without removing it."""
        while self._sell_heap:
            _, _, order = self._sell_heap[0]
            if order.quantity > 0:
                return order
            heapq.heappop(self._sell_heap)
        return None

    def pop_best_buy(self) -> Optional[Order]:
        """Remove and return the highest-priority buy order."""
        while self._buy_heap:
            _, _, order = heapq.heappop(self._buy_heap)
            if order.quantity > 0:
                return order
        return None

    def pop_best_sell(self) -> Optional[Order]:
        """Remove and return the highest-priority sell order."""
        while self._sell_heap:
            _, _, order = heapq.heappop(self._sell_heap)
            if order.quantity > 0:
                return order
        return None

    def push_back_buy(self, order: Order) -> None:
        """Re-insert a partially filled buy order."""
        heapq.heappush(self._buy_heap, (-order.price, order.timestamp, order))

    def push_back_sell(self, order: Order) -> None:
        """Re-insert a partially filled sell order."""
        heapq.heappush(self._sell_heap, (order.price, order.timestamp, order))

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def buy_orders(self) -> List[Order]:
        """Return all active buy orders sorted by priority (best first)."""
        return sorted(
            [o for _, _, o in self._buy_heap if o.quantity > 0],
            key=lambda o: (-o.price, o.timestamp),
        )

    def sell_orders(self) -> List[Order]:
        """Return all active sell orders sorted by priority (best first)."""
        return sorted(
            [o for _, _, o in self._sell_heap if o.quantity > 0],
            key=lambda o: (o.price, o.timestamp),
        )

    def __repr__(self) -> str:
        buys = self.buy_orders()
        sells = self.sell_orders()
        lines = ["=== Order Book ==="]
        lines.append("SELL orders:")
        for o in reversed(sells):
            lines.append(f"  {o}")
        lines.append("BUY orders:")
        for o in buys:
            lines.append(f"  {o}")
        return "\n".join(lines)
