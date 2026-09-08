"""
pyfridge — Hamilton-inspired smart fridge inventory and meal selection library.

Model your fridge as a hierarchical deck (zones → positions → items),
track macros and expiry, and run selection protocols to match your meal targets.
"""

from .db import get_connection
from .deck import Deck
from .inventory import Inventory
from .selector import Selector

__version__ = "0.1.0"
__all__ = ["Deck", "Inventory", "Selector", "get_connection"]
