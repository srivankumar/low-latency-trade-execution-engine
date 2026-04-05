"""Unit tests for the Low-Latency Trade Execution Engine."""

import time
import unittest

from order import Order, OrderType
from order_book import OrderBook
from matching_engine import MatchingEngine
from trade_execution_engine import TradeExecutionEngine


# ---------------------------------------------------------------------------
# Order tests
# ---------------------------------------------------------------------------

class TestOrder(unittest.TestCase):
    def test_valid_buy_order(self):
        o = Order(order_id=1, order_type=OrderType.BUY, quantity=100, price=50.0)
        self.assertEqual(o.order_id, 1)
        self.assertEqual(o.order_type, OrderType.BUY)
        self.assertEqual(o.quantity, 100)
        self.assertEqual(o.price, 50.0)

    def test_valid_sell_order(self):
        o = Order(order_id=2, order_type=OrderType.SELL, quantity=50, price=45.0)
        self.assertEqual(o.order_type, OrderType.SELL)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            Order(order_id=1, order_type=OrderType.BUY, quantity=0, price=50.0)

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            Order(order_id=1, order_type=OrderType.BUY, quantity=10, price=-5.0)

    def test_repr(self):
        o = Order(order_id=3, order_type=OrderType.SELL, quantity=10, price=20.0)
        self.assertIn("SELL", repr(o))
        self.assertIn("10", repr(o))


# ---------------------------------------------------------------------------
# OrderBook tests
# ---------------------------------------------------------------------------

class TestOrderBook(unittest.TestCase):
    def _make_buy(self, order_id, price, qty=10, ts=None):
        o = Order(order_id=order_id, order_type=OrderType.BUY, quantity=qty, price=price)
        if ts is not None:
            o.timestamp = ts
        return o

    def _make_sell(self, order_id, price, qty=10, ts=None):
        o = Order(order_id=order_id, order_type=OrderType.SELL, quantity=qty, price=price)
        if ts is not None:
            o.timestamp = ts
        return o

    def test_best_buy_highest_price(self):
        book = OrderBook()
        book.add_order(self._make_buy(1, price=40))
        book.add_order(self._make_buy(2, price=50))
        book.add_order(self._make_buy(3, price=45))
        self.assertEqual(book.best_buy().price, 50)

    def test_best_sell_lowest_price(self):
        book = OrderBook()
        book.add_order(self._make_sell(1, price=60))
        book.add_order(self._make_sell(2, price=50))
        book.add_order(self._make_sell(3, price=55))
        self.assertEqual(book.best_sell().price, 50)

    def test_buy_time_priority_same_price(self):
        book = OrderBook()
        t0 = time.time()
        book.add_order(self._make_buy(1, price=50, ts=t0 + 1))  # later
        book.add_order(self._make_buy(2, price=50, ts=t0))      # earlier
        self.assertEqual(book.best_buy().order_id, 2)

    def test_sell_time_priority_same_price(self):
        book = OrderBook()
        t0 = time.time()
        book.add_order(self._make_sell(1, price=50, ts=t0 + 1))  # later
        book.add_order(self._make_sell(2, price=50, ts=t0))      # earlier
        self.assertEqual(book.best_sell().order_id, 2)

    def test_empty_book_returns_none(self):
        book = OrderBook()
        self.assertIsNone(book.best_buy())
        self.assertIsNone(book.best_sell())

    def test_pop_removes_order(self):
        book = OrderBook()
        book.add_order(self._make_buy(1, price=50))
        self.assertIsNotNone(book.pop_best_buy())
        self.assertIsNone(book.best_buy())

    def test_buy_orders_list_sorted(self):
        book = OrderBook()
        book.add_order(self._make_buy(1, price=40))
        book.add_order(self._make_buy(2, price=60))
        book.add_order(self._make_buy(3, price=50))
        prices = [o.price for o in book.buy_orders()]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_sell_orders_list_sorted(self):
        book = OrderBook()
        book.add_order(self._make_sell(1, price=70))
        book.add_order(self._make_sell(2, price=50))
        book.add_order(self._make_sell(3, price=60))
        prices = [o.price for o in book.sell_orders()]
        self.assertEqual(prices, sorted(prices))


# ---------------------------------------------------------------------------
# MatchingEngine tests
# ---------------------------------------------------------------------------

class TestMatchingEngine(unittest.TestCase):
    def _engine_with_orders(self, buys, sells):
        """Helper: create book+engine with given (qty, price) tuples."""
        book = OrderBook()
        oid = 1
        for qty, price in buys:
            book.add_order(Order(order_id=oid, order_type=OrderType.BUY, quantity=qty, price=price))
            oid += 1
        for qty, price in sells:
            book.add_order(Order(order_id=oid, order_type=OrderType.SELL, quantity=qty, price=price))
            oid += 1
        return MatchingEngine(book), book

    # --- problem statement example ---
    def test_basic_match_problem_statement(self):
        """BUY 100@50 vs SELL 50@45 → 50 shares at ₹45, 50 buy remaining."""
        engine, book = self._engine_with_orders(
            buys=[(100, 50)], sells=[(50, 45)]
        )
        trades = engine.match()
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual(trade.quantity, 50)
        self.assertEqual(trade.price, 45)
        # 50 shares of the buy order should remain
        remaining = book.buy_orders()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].quantity, 50)
        # sell side exhausted
        self.assertEqual(len(book.sell_orders()), 0)

    def test_no_match_when_buy_price_below_sell_price(self):
        engine, _ = self._engine_with_orders(
            buys=[(100, 40)], sells=[(50, 50)]
        )
        trades = engine.match()
        self.assertEqual(trades, [])

    def test_exact_price_match(self):
        """BUY and SELL at the same price should match."""
        engine, _ = self._engine_with_orders(
            buys=[(10, 50)], sells=[(10, 50)]
        )
        trades = engine.match()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 10)
        self.assertEqual(trades[0].price, 50)

    def test_partial_fill_sell_larger(self):
        """SELL qty > BUY qty → partial fill, remainder on sell side."""
        engine, book = self._engine_with_orders(
            buys=[(30, 50)], sells=[(100, 45)]
        )
        trades = engine.match()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 30)
        remaining_sells = book.sell_orders()
        self.assertEqual(len(remaining_sells), 1)
        self.assertEqual(remaining_sells[0].quantity, 70)

    def test_multiple_sells_against_one_buy(self):
        """One big BUY consumed by multiple SELL orders."""
        engine, book = self._engine_with_orders(
            buys=[(100, 60)],
            sells=[(40, 50), (40, 55), (40, 65)],  # last one won't match
        )
        trades = engine.match()
        # First two sell orders should match (prices 50 and 55 <= 60)
        self.assertEqual(len(trades), 2)
        total_filled = sum(t.quantity for t in trades)
        self.assertEqual(total_filled, 80)
        # 20 shares of buy remain; sell at 65 stays
        self.assertEqual(book.buy_orders()[0].quantity, 20)

    def test_price_time_priority_buy_side(self):
        """Higher-priced buy matches first."""
        t0 = time.time()
        book = OrderBook()
        # two buy orders; higher price should match first
        buy_low = Order(order_id=1, order_type=OrderType.BUY, quantity=10, price=50)
        buy_high = Order(order_id=2, order_type=OrderType.BUY, quantity=10, price=60)
        sell = Order(order_id=3, order_type=OrderType.SELL, quantity=10, price=45)
        buy_low.timestamp = t0
        buy_high.timestamp = t0 + 1  # later, but higher price
        book.add_order(buy_low)
        book.add_order(buy_high)
        book.add_order(sell)
        me = MatchingEngine(book)
        trades = me.match()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].buy_order_id, buy_high.order_id)

    def test_time_priority_same_price(self):
        """Earlier order at same price matches first."""
        t0 = time.time()
        book = OrderBook()
        buy_early = Order(order_id=1, order_type=OrderType.BUY, quantity=10, price=50)
        buy_late = Order(order_id=2, order_type=OrderType.BUY, quantity=10, price=50)
        sell = Order(order_id=3, order_type=OrderType.SELL, quantity=10, price=45)
        buy_early.timestamp = t0
        buy_late.timestamp = t0 + 1
        book.add_order(buy_early)
        book.add_order(buy_late)
        book.add_order(sell)
        me = MatchingEngine(book)
        trades = me.match()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].buy_order_id, buy_early.order_id)

    def test_execution_price_is_sell_price(self):
        """Execution price always equals the sell-order price."""
        engine, _ = self._engine_with_orders(
            buys=[(10, 100)], sells=[(10, 45)]
        )
        trades = engine.match()
        self.assertEqual(trades[0].price, 45)

    def test_empty_book_no_trades(self):
        book = OrderBook()
        me = MatchingEngine(book)
        self.assertEqual(me.match(), [])

    def test_only_buy_orders_no_trades(self):
        engine, _ = self._engine_with_orders(buys=[(10, 50)], sells=[])
        trades = engine.match()
        self.assertEqual(trades, [])

    def test_only_sell_orders_no_trades(self):
        engine, _ = self._engine_with_orders(buys=[], sells=[(10, 50)])
        trades = engine.match()
        self.assertEqual(trades, [])


# ---------------------------------------------------------------------------
# TradeExecutionEngine integration tests
# ---------------------------------------------------------------------------

class TestTradeExecutionEngine(unittest.TestCase):
    def test_place_buy_then_sell_triggers_trade(self):
        engine = TradeExecutionEngine()
        engine.place_order(OrderType.BUY, quantity=100, price=50)
        engine.place_order(OrderType.SELL, quantity=50, price=45)
        trades = engine.get_trade_log()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 50)
        self.assertEqual(trades[0].price, 45)

    def test_remaining_buy_stays_in_book(self):
        engine = TradeExecutionEngine()
        engine.place_order(OrderType.BUY, quantity=100, price=50)
        engine.place_order(OrderType.SELL, quantity=50, price=45)
        remaining = engine.get_order_book().buy_orders()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].quantity, 50)

    def test_no_trade_when_sell_above_buy(self):
        engine = TradeExecutionEngine()
        engine.place_order(OrderType.BUY, quantity=10, price=40)
        engine.place_order(OrderType.SELL, quantity=10, price=50)
        self.assertEqual(engine.get_trade_log(), [])

    def test_multiple_trades_accumulated_in_log(self):
        engine = TradeExecutionEngine()
        engine.place_order(OrderType.BUY, quantity=10, price=50)
        engine.place_order(OrderType.BUY, quantity=10, price=48)
        engine.place_order(OrderType.SELL, quantity=10, price=45)
        engine.place_order(OrderType.SELL, quantity=10, price=47)
        trades = engine.get_trade_log()
        self.assertEqual(len(trades), 2)

    def test_order_ids_are_sequential(self):
        engine = TradeExecutionEngine()
        o1 = engine.place_order(OrderType.BUY, quantity=10, price=50)
        o2 = engine.place_order(OrderType.SELL, quantity=10, price=45)
        self.assertEqual(o1.order_id, 1)
        self.assertEqual(o2.order_id, 2)

    def test_invalid_order_raises_value_error(self):
        engine = TradeExecutionEngine()
        with self.assertRaises(ValueError):
            engine.place_order(OrderType.BUY, quantity=0, price=50)
        with self.assertRaises(ValueError):
            engine.place_order(OrderType.SELL, quantity=10, price=0)

    def test_sell_placed_before_buy_still_matches(self):
        """Matching must work regardless of which side arrives first."""
        engine = TradeExecutionEngine()
        engine.place_order(OrderType.SELL, quantity=20, price=45)
        engine.place_order(OrderType.BUY, quantity=20, price=50)
        trades = engine.get_trade_log()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 20)


if __name__ == "__main__":
    unittest.main()
