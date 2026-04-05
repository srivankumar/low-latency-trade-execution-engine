"""Order data class representing a single buy or sell order."""

import time
from dataclasses import dataclass, field
from enum import Enum


class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """
    Represents a single trade order.

    Attributes:
        order_id:  Unique identifier for the order.
        order_type: BUY or SELL.
        quantity:  Number of shares requested.
        price:     Limit price per share (in ₹).
        timestamp: Epoch time (seconds) when the order was placed.
                   Defaults to the current time so earlier orders get
                   priority when prices are equal.
    """

    order_id: int
    order_type: OrderType
    quantity: int
    price: float
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")

    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id}, {self.order_type.value}, "
            f"qty={self.quantity}, price=₹{self.price:.2f})"
        )
