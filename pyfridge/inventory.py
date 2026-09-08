"""
Inventory — query and manage what is currently in the fridge.
"""

from dataclasses import dataclass
from datetime import date
from .db import query, execute


@dataclass
class InventoryItem:
    id: int
    food_name: str
    category: str
    position_label: str | None
    zone_name: str | None
    quantity: float
    unit_type: str
    purchase_date: date
    expiry_date: date | None
    opened: bool
    brand: str | None
    notes: str | None
    # macros per 100g
    calories_per_100g: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float

    @property
    def days_until_expiry(self) -> int | None:
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return self.expiry_date < date.today()

    @property
    def urgency(self) -> str:
        """Expiry urgency label for display."""
        d = self.days_until_expiry
        if d is None:
            return "no expiry"
        if d < 0:
            return "EXPIRED"
        if d == 0:
            return "expires TODAY"
        if d <= 2:
            return f"⚠️  {d}d left"
        if d <= 5:
            return f"⏰ {d}d left"
        return f"{d}d left"


class Inventory:
    """
    Loads and filters the current fridge inventory.

    Usage:
        inv = Inventory().load()
        fresh = inv.fresh()
        expiring = inv.expiring_soon(days=3)
        produce = inv.by_category('produce')
    """

    def __init__(self):
        self.items: list[InventoryItem] = []

    def load(self) -> "Inventory":
        """Load all inventory with food and location details."""
        rows = query("""
            SELECT
                i.id,
                fi.name                 AS food_name,
                fc.name                 AS category,
                fp.label                AS position_label,
                fz.name                 AS zone_name,
                i.quantity,
                fi.unit_type,
                i.purchase_date,
                i.expiry_date,
                i.opened,
                i.brand,
                i.notes,
                fi.calories_per_100g,
                fi.protein_g,
                fi.carbs_g,
                fi.fat_g,
                fi.fiber_g
            FROM inventory i
            JOIN food_items fi     ON fi.id = i.food_item_id
            JOIN food_categories fc ON fc.id = fi.category_id
            LEFT JOIN fridge_positions fp ON fp.id = i.position_id
            LEFT JOIN fridge_zones fz ON fz.id = fp.zone_id
            ORDER BY i.expiry_date ASC NULLS LAST
        """)
        self.items = [InventoryItem(**row) for row in rows]
        return self

    def fresh(self) -> list[InventoryItem]:
        """Items that are not expired."""
        return [i for i in self.items if not i.is_expired]

    def expired(self) -> list[InventoryItem]:
        return [i for i in self.items if i.is_expired]

    def expiring_soon(self, days: int = 3) -> list[InventoryItem]:
        """Items expiring within N days (not yet expired)."""
        return [
            i for i in self.fresh()
            if i.days_until_expiry is not None and i.days_until_expiry <= days
        ]

    def by_category(self, category: str) -> list[InventoryItem]:
        return [i for i in self.items if i.category.lower() == category.lower()]

    def by_zone(self, zone_name: str) -> list[InventoryItem]:
        return [i for i in self.items if i.zone_name == zone_name]

    def describe(self) -> None:
        """Print inventory summary table."""
        from tabulate import tabulate
        rows = [
            [
                i.food_name,
                i.category,
                i.position_label or "—",
                f"{i.quantity} {i.unit_type}",
                i.brand or "—",
                i.urgency,
            ]
            for i in self.items
        ]
        print(tabulate(
            rows,
            headers=["Item", "Category", "Position", "Qty", "Brand", "Expiry"],
            tablefmt="rounded_outline",
        ))
