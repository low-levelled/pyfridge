# pyfridge 🧊

**A Hamilton-inspired smart fridge automation library — from inventory tracking to robotic ingredient retrieval.**

Think airport coffee machine, but for your fridge. You order a sandwich on a touchscreen. The fridge reads its own inventory, plans the retrieval sequence, and a robotic arm stages your ingredients at the door.

---

## Vision

Modern liquid handling robots like the Hamilton STAR operate on a simple model: a **deck** of known positions, a **sample manifest**, and a **protocol** that moves things from A to B with precision. pyfridge applies that same model to a refrigerator.

```
User Order (UI)
     ↓
Inventory Query (PostgreSQL)
     ↓
Motion Plan (selector protocol)
     ↓
Arm Execution (hardware integration layer)
     ↓
Ingredients staged at delivery zone
```

---

## Hardware Integration Layer

The physical integration is a **thin frame insert** that mounts between the refrigerator door gasket and the cabinet face — no modification to the fridge unit itself.

```
┌─────────────────────────────────────┐
│  INTEGRATION FRAME (fits in opening)│
│  ┌─────────────────────────────┐    │
│  │  Camera Array (depth + RGB) │    │
│  │  X-axis linear rail ────────┤    │
│  │  Y-axis rail (vertical)     │    │
│  │  Z-axis arm (reach in)      │    │
│  │  Gripper end effector       │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
         ↕ mounts here ↕
   [door gasket] ←→ [cabinet face]
```

**Reference unit:** LG French Door (34"W × 42"H usable interior opening)

**Sensors:**
- Intel RealSense D435 depth camera — interior 3D mapping and item identification
- Weight sensors on delivery shelf — confirms retrieval success

**Actuation:**
- 3-axis gantry (X: 860mm, Y: 1066mm, Z: 400mm reach)
- Soft gripper end effector (handles bottles, bags, containers)

---

## Software Architecture

### Layer 1 — Deck Model (`pyfridge.deck`)
The fridge interior modeled as a coordinate grid. Every zone and position has absolute X/Y/Z coordinates in millimeters, calibrated to the reference fridge dimensions.

### Layer 2 — Inventory (`pyfridge.inventory`)
PostgreSQL-backed inventory with:
- Physical position (zone, slot, X/Y/Z coordinates)
- Nutritional data (macros per 100g)
- Expiry tracking with urgency classification
- Computer vision update hooks (camera scan → inventory state)

### Layer 3 — Selector Protocol (`pyfridge.selector`)
The core planning engine:
- Takes a user order (meal type + macro targets)
- Queries available inventory
- Generates an ordered retrieval sequence (expiry-first, weight-optimized)
- Outputs arm waypoints for execution

### Layer 4 — Kiosk UI (`pyfridge.ui`) *(v0.2)*
Terminal-first (Rich/Textual), web-ready (FastAPI):
- Browse available items from live inventory
- Build a sandwich or select a macro profile
- Confirm → triggers selector protocol
- Live feedback during arm execution

### Layer 5 — Hardware Bridge (`pyfridge.arm`) *(v0.3)*
- Translates waypoints into motor commands
- Serial/USB interface to the gantry controller
- Simulated mode for development without hardware

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/low-levelled/pyfridge
cd pyfridge
pip install -e .

# 2. Configure database
cp .env.example .env     # fill in your Postgres credentials

# 3. Set up the DB
./scripts/setup_db.sh

# 4. Run it
pyfridge deck            # visualize fridge layout
pyfridge inventory       # list all items
pyfridge expiring        # what needs to be used today
pyfridge select lunch cutting --log   # run meal selection protocol
```

---

## Sandwich Protocol (first real use case)

```python
from pyfridge import Inventory, Selector
from pyfridge.selector import MacroTarget

# What's available?
inv = Inventory().load()

# Run the sandwich protocol for lunch/cutting
target = MacroTarget.from_db("lunch", "cutting")
selector = Selector(inv, target)
results = selector.run()
selector.describe(results)
# → prints table of selected items with positions and macros
# → arm waypoints generated for each item
```

---

## Roadmap

| Version | Milestone |
|---------|-----------|
| v0.1 | Core DB schema, Deck, Inventory, Selector, CLI |
| v0.2 | Terminal UI (Rich/Textual), add-item CLI, barcode lookup |
| v0.3 | Hardware arm bridge, simulated execution mode |
| v0.4 | Computer vision inventory update (RealSense integration) |
| v0.5 | Full sandwich protocol end-to-end in simulation |
| v1.0 | Physical hardware integration on reference LG unit |

---

## Why pyfridge?

Nothing in the open source ecosystem models:
- **Physical location hierarchy** (zone → position → coordinate) as a first-class concept
- **Macro-aware selection** that matches food to calorie/protein targets
- **Expiry-first retrieval** that minimizes food waste
- **A path to physical actuation** via a Hamilton-style protocol layer

pyfridge is the software half of a real product. The hardware half is a retrofit frame that turns any standard French door refrigerator into an automated ingredient dispenser.

---

## License

MIT © Drake Sadosky
