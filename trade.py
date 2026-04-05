"""Trade record produced when two orders are matched."""

from dataclasses import dataclass


@dataclass
class Trade:
    """
    Records a single executed trade.

    Attributes:
        buy_order_id:  ID of the buy order that was matched.
        sell_order_id: ID of the sell order that was matched.
        quantity:      Number of shares traded.
        price:         Execution price per share (sell-order limit price).
    """

    buy_order_id: int
    sell_order_id: int
    quantity: int
    price: float

    def __repr__(self) -> str:
        return (
            f"Trade(buy_id={self.buy_order_id}, sell_id={self.sell_order_id}, "
            f"qty={self.quantity}, price=₹{self.price:.2f})"
        )

    def display(self) -> str:
        """Human-readable trade summary."""
        return (
            f"✅ Trade executed: {self.quantity} shares at ₹{self.price:.2f}  "
            f"[buy_order={self.buy_order_id}, sell_order={self.sell_order_id}]"
        )
