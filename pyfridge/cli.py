"""
pyfridge CLI — run selection protocols from the command line.

Usage:
    pyfridge deck                          # show fridge layout
    pyfridge inventory                     # list all items
    pyfridge expiring [--days 3]           # items expiring soon
    pyfridge select lunch cutting          # run selection protocol
    pyfridge select dinner bulking --log   # run and log to DB
"""

import argparse
import sys
from .deck import Deck
from .inventory import Inventory
from .selector import Selector, MacroTarget


def cmd_deck(_args):
    Deck().load().describe()


def cmd_inventory(_args):
    Inventory().load().describe()


def cmd_expiring(args):
    days = args.days if hasattr(args, "days") else 3
    inv = Inventory().load()
    items = inv.expiring_soon(days=days)
    if not items:
        print(f"Nothing expiring within {days} days.")
        return
    print(f"\n⚠️  Items expiring within {days} days:\n")
    for item in items:
        print(f"  {item.food_name:<30} {item.urgency}  [{item.position_label or '—'}]")
    print()


def cmd_select(args):
    try:
        target = MacroTarget.from_db(args.meal_type, args.profile)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    inv = Inventory().load()
    selector = Selector(inv, target)
    results = selector.run()

    if not results:
        print("No suitable items found for this target.")
        return

    selector.describe(results)

    if hasattr(args, "log") and args.log:
        pid = selector.log_to_db(results)
        print(f"  Protocol logged → ID {pid}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="pyfridge",
        description="Smart fridge inventory and meal selection",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("deck", help="Show fridge deck layout")
    sub.add_parser("inventory", help="List all inventory items")

    exp = sub.add_parser("expiring", help="Show items expiring soon")
    exp.add_argument("--days", type=int, default=3)

    sel = sub.add_parser("select", help="Run meal selection protocol")
    sel.add_argument("meal_type", choices=["breakfast", "lunch", "dinner", "snack"])
    sel.add_argument("profile", choices=["cutting", "bulking", "maintenance"])
    sel.add_argument("--log", action="store_true", help="Log run to database")

    args = parser.parse_args()

    dispatch = {
        "deck": cmd_deck,
        "inventory": cmd_inventory,
        "expiring": cmd_expiring,
        "select": cmd_select,
    }

    if args.command not in dispatch:
        parser.print_help()
        sys.exit(0)

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
