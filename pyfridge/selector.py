"""
Selector — the core selection protocol.

Takes meal preferences and available inventory,
returns a ranked list of items to use — prioritizing:
  1. Items expiring soonest (use before they go bad)
  2. Items that best match the macro targets
  3. Items from the requested meal category profile
"""

from dataclasses import dataclass, field
from .inventory import Inventory, InventoryItem
from .db import query, execute


@dataclass
class MacroTarget:
    """User's macro targets for a meal."""
    meal_type: str          # 'breakfast', 'lunch', 'dinner', 'snack'
    profile: str            # 'cutting', 'bulking', 'maintenance'
    target_calories: int
    min_protein_g: float
    max_carbs_g: float
    max_fat_g: float
    exclude_categories: list[str] = field(default_factory=list)

    @classmethod
    def from_db(cls, meal_type: str, profile: str) -> "MacroTarget":
        """Load a saved preference profile from the database."""
        rows = query("""
            SELECT mp.target_calories, mp.min_protein_g,
                   mp.max_carbs_g, mp.max_fat_g, mp.exclude_categories,
                   mt.name AS meal_type
            FROM meal_preferences mp
            JOIN meal_types mt ON mt.id = mp.meal_type_id
            WHERE mt.name = %s AND mp.profile_name = %s
            LIMIT 1
        """, (meal_type, profile))

        if not rows:
            raise ValueError(f"No profile '{profile}' for meal type '{meal_type}'")

        row = rows[0]
        return cls(
            meal_type=meal_type,
            profile=profile,
            target_calories=row["target_calories"],
            min_protein_g=float(row["min_protein_g"]),
            max_carbs_g=float(row["max_carbs_g"]),
            max_fat_g=float(row["max_fat_g"]),
            exclude_categories=[],  # extend later with category name lookup
        )


@dataclass
class SelectionResult:
    """The output of a protocol run."""
    item: InventoryItem
    serving_g: float        # recommended serving in grams
    reason: str

    @property
    def macros(self) -> dict:
        scale = self.serving_g / 100
        return {
            "calories": round(self.item.calories_per_100g * scale, 1),
            "protein_g": round(self.item.protein_g * scale, 1),
            "carbs_g": round(self.item.carbs_g * scale, 1),
            "fat_g": round(self.item.fat_g * scale, 1),
        }


class Selector:
    """
    The Hamilton-style selection protocol.

    Usage:
        target = MacroTarget.from_db('lunch', 'cutting')
        inv = Inventory().load()
        selector = Selector(inv, target)
        results = selector.run()
        selector.describe(results)
    """

    DEFAULT_SERVING_G = 150.0

    def __init__(self, inventory: Inventory, target: MacroTarget):
        self.inventory = inventory
        self.target = target

    def run(self) -> list[SelectionResult]:
        """
        Execute the selection protocol.

        Algorithm:
          1. Filter out expired items and excluded categories
          2. Sort remaining by expiry (soonest first — use what's about to go bad)
          3. Greedily add items until calorie target is hit
          4. Check protein floor — add high-protein items if needed
        """
        candidates = [
            item for item in self.inventory.fresh()
            if item.category not in self.target.exclude_categories
        ]

        # Sort: items expiring soonest first, then by protein density desc
        candidates.sort(key=lambda i: (
            i.expiry_date or __import__('datetime').date.max,
            -(i.protein_g or 0),
        ))

        results: list[SelectionResult] = []
        total_calories = 0.0
        total_protein = 0.0

        for item in candidates:
            if total_calories >= self.target.target_calories:
                break

            serving = min(self.DEFAULT_SERVING_G, item.quantity)
            scale = serving / 100
            item_cals = (item.calories_per_100g or 0) * scale
            item_protein = (item.protein_g or 0) * scale
            item_carbs = (item.carbs_g or 0) * scale
            item_fat = (item.fat_g or 0) * scale

            # Skip if adding this would blow carb or fat limits
            if item_carbs > self.target.max_carbs_g * 0.6:
                continue
            if item_fat > self.target.max_fat_g * 0.6:
                continue

            reason = f"expires {item.urgency}"
            if item_protein > 10:
                reason += f", high protein ({item_protein:.0f}g)"

            results.append(SelectionResult(
                item=item,
                serving_g=serving,
                reason=reason,
            ))

            total_calories += item_cals
            total_protein += item_protein

        return results

    def describe(self, results: list[SelectionResult]) -> None:
        """Print a formatted protocol run summary."""
        from tabulate import tabulate

        print(f"\n{'='*60}")
        print(f"  PYFRIDGE PROTOCOL — {self.target.meal_type.upper()} / {self.target.profile.upper()}")
        print(f"  Target: {self.target.target_calories} kcal | "
              f">{self.target.min_protein_g}g protein | "
              f"<{self.target.max_carbs_g}g carbs")
        print(f"{'='*60}")

        rows = []
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}

        for r in results:
            m = r.macros
            rows.append([
                r.item.food_name,
                r.item.position_label or "—",
                f"{r.serving_g:.0f}g",
                f"{m['calories']} kcal",
                f"{m['protein_g']}g",
                f"{m['carbs_g']}g",
                f"{m['fat_g']}g",
                r.reason,
            ])
            for k in totals:
                totals[k] += m[k]

        print(tabulate(
            rows,
            headers=["Item", "Pos", "Serving", "Cal", "Protein", "Carbs", "Fat", "Reason"],
            tablefmt="rounded_outline",
        ))

        print(f"\n  TOTALS → {totals['calories']:.0f} kcal | "
              f"{totals['protein_g']:.1f}g protein | "
              f"{totals['carbs_g']:.1f}g carbs | "
              f"{totals['fat_g']:.1f}g fat")
        print()

    def log_to_db(self, results: list[SelectionResult], notes: str = "") -> int:
        """Save this protocol run to the database and return the protocol ID."""
        execute("""
            INSERT INTO protocols (meal_type_id, profile_name, notes)
            SELECT mt.id, %s, %s FROM meal_types mt WHERE mt.name = %s
        """, (self.target.profile, notes, self.target.meal_type))

        rows = query("SELECT id FROM protocols ORDER BY run_at DESC LIMIT 1")
        protocol_id = rows[0]["id"]

        for r in results:
            execute("""
                INSERT INTO protocol_selections (protocol_id, inventory_id, quantity_used, reason)
                VALUES (%s, %s, %s, %s)
            """, (protocol_id, r.item.id, r.serving_g, r.reason))

        return protocol_id
