"""
Deck — the Hamilton-inspired physical layout of the fridge.

A Deck contains Zones (shelf, drawer, door).
Each Zone contains Positions (individual slots).
Each Position holds an inventory item.

This mirrors the Hamilton liquid handler model:
  Deck → Carrier → Position → Sample
"""

from dataclasses import dataclass
from .db import query


@dataclass
class Position:
    id: int
    zone_id: int
    slot: int
    label: str
    max_weight_g: float
    is_occupied: bool


@dataclass
class Zone:
    id: int
    name: str
    zone_type: str          # 'shelf', 'drawer', 'door'
    temp_c: float
    position_order: int
    positions: list[Position]


class Deck:
    """
    Represents the full fridge as a Hamilton-style deck.

    Usage:
        deck = Deck()
        deck.load()
        deck.describe()
        zone = deck.get_zone('crisper_left')
    """

    def __init__(self):
        self.zones: dict[str, Zone] = {}

    def load(self) -> "Deck":
        """Load all zones and positions from the database."""
        zones_raw = query("""
            SELECT z.id, z.name, z.zone_type, z.temp_c, z.position_order,
                   p.id AS pos_id, p.slot, p.label, p.max_weight_g, p.is_occupied
            FROM fridge_zones z
            LEFT JOIN fridge_positions p ON p.zone_id = z.id
            ORDER BY z.position_order, p.slot
        """)

        zone_map: dict[int, Zone] = {}
        for row in zones_raw:
            zid = row["id"]
            if zid not in zone_map:
                zone_map[zid] = Zone(
                    id=zid,
                    name=row["name"],
                    zone_type=row["zone_type"],
                    temp_c=float(row["temp_c"] or 0),
                    position_order=row["position_order"],
                    positions=[],
                )
            if row["pos_id"]:
                zone_map[zid].positions.append(Position(
                    id=row["pos_id"],
                    zone_id=zid,
                    slot=row["slot"],
                    label=row["label"],
                    max_weight_g=float(row["max_weight_g"] or 0),
                    is_occupied=row["is_occupied"],
                ))

        self.zones = {z.name: z for z in zone_map.values()}
        return self

    def get_zone(self, name: str) -> Zone | None:
        return self.zones.get(name)

    def available_positions(self) -> list[Position]:
        """Return all unoccupied positions across all zones."""
        return [
            p for zone in self.zones.values()
            for p in zone.positions
            if not p.is_occupied
        ]

    def describe(self) -> None:
        """Print a visual summary of the deck layout."""
        print(f"\n{'='*55}")
        print(f"{'PYFRIDGE DECK':^55}")
        print(f"{'='*55}")
        for zone in sorted(self.zones.values(), key=lambda z: z.position_order):
            occupied = sum(1 for p in zone.positions if p.is_occupied)
            total = len(zone.positions)
            bar = ("█" * occupied) + ("░" * (total - occupied))
            print(f"  {zone.name:<20} [{bar:<8}] {occupied}/{total}  ({zone.temp_c}°C)")
        print(f"{'='*55}\n")
