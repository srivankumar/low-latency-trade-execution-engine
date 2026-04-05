"""Matching engine — pairs buy and sell orders using price-time priority.

Matching rule:
  A trade occurs when the best BUY price >= best SELL price.
  Execution price = SELL order's limit price (sell-side price protection).
  Quantity filled = min(buy_quantity, sell_quantity).
  Partial fills are supported; the remaining portion stays in the book.
"""

from typing import List

from order_book import OrderBook
from trade import Trade


class MatchingEngine:
    """
    Continuously matches orders inside an :class:`OrderBook`.

    Usage::

        engine = MatchingEngine(order_book)
        trades = engine.match()
    """

    def __init__(self, order_book: OrderBook) -> None:
        self._book = order_book

    def match(self) -> List[Trade]:
        """
        Run the matching loop until no further matches can be made.

        Returns
        -------
        list[Trade]
            All trades executed in this matching pass (may be empty).
        """
        trades: List[Trade] = []

        while True:
            best_buy = self._book.best_buy()
            best_sell = self._book.best_sell()

            # No orders on one or both sides — nothing to match.
            if best_buy is None or best_sell is None:
                break

            # Core matching condition: buyer willing to pay at least the ask price.
            if best_buy.price < best_sell.price:
                break

            # Remove both orders from the book to process them.
            buy_order = self._book.pop_best_buy()
            sell_order = self._book.pop_best_sell()

            # Determine fill quantity and execution price.
            fill_qty = min(buy_order.quantity, sell_order.quantity)
            exec_price = sell_order.price  # sell-side price protection

            trades.append(
                Trade(
                    buy_order_id=buy_order.order_id,
                    sell_order_id=sell_order.order_id,
                    quantity=fill_qty,
                    price=exec_price,
                )
            )

            # Reduce quantities.
            buy_order.quantity -= fill_qty
            sell_order.quantity -= fill_qty

            # Push partially filled orders back.
            if buy_order.quantity > 0:
                self._book.push_back_buy(buy_order)
            if sell_order.quantity > 0:
                self._book.push_back_sell(sell_order)

        return trades
