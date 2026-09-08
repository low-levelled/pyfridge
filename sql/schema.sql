-- ============================================================
-- THE ULTIMATE FRIDGE
-- Modeled as a Hamilton-style deck: zones > positions > items
-- ============================================================

-- Drop in reverse dependency order if re-running
DROP TABLE IF EXISTS protocol_selections CASCADE;
DROP TABLE IF EXISTS protocols CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS food_categories CASCADE;
DROP TABLE IF EXISTS fridge_positions CASCADE;
DROP TABLE IF EXISTS fridge_zones CASCADE;
DROP TABLE IF EXISTS meal_preferences CASCADE;
DROP TABLE IF EXISTS meal_types CASCADE;

-- ============================================================
-- DECK LAYOUT
-- ============================================================

CREATE TABLE fridge_zones (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,   -- 'top_shelf', 'crisper_drawer', etc.
    zone_type   VARCHAR(20) NOT NULL,          -- 'shelf', 'drawer', 'door'
    temp_c      NUMERIC(4,1),                  -- typical temp in celsius
    position_order INT NOT NULL               -- 1 = top, higher = lower in fridge
);

CREATE TABLE fridge_positions (
    id          SERIAL PRIMARY KEY,
    zone_id     INT NOT NULL REFERENCES fridge_zones(id),
    slot        INT NOT NULL,                  -- slot number within zone (like deck position)
    label       VARCHAR(30),                   -- human-readable e.g. 'A1', 'B3'
    max_weight_g NUMERIC(7,1),
    is_occupied BOOLEAN DEFAULT FALSE,
    UNIQUE (zone_id, slot)
);

-- ============================================================
-- FOOD CATALOG
-- ============================================================

CREATE TABLE food_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,   -- 'dairy', 'produce', 'meat', 'leftovers'
    storage_type VARCHAR(20)                   -- 'refrigerated', 'frozen', 'either'
);

CREATE TABLE food_items (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    category_id     INT NOT NULL REFERENCES food_categories(id),
    calories_per_100g NUMERIC(6,1),
    protein_g       NUMERIC(5,1),             -- per 100g
    carbs_g         NUMERIC(5,1),             -- per 100g
    fat_g           NUMERIC(5,1),             -- per 100g
    fiber_g         NUMERIC(5,1),             -- per 100g
    unit_type       VARCHAR(10) NOT NULL      -- 'g', 'ml', 'each'
);

-- ============================================================
-- INVENTORY (items actually in the fridge right now)
-- ============================================================

CREATE TABLE inventory (
    id              SERIAL PRIMARY KEY,
    food_item_id    INT NOT NULL REFERENCES food_items(id),
    position_id     INT REFERENCES fridge_positions(id),
    quantity        NUMERIC(7,1) NOT NULL,     -- amount in unit_type units
    purchase_date   DATE NOT NULL,
    expiry_date     DATE,
    opened          BOOLEAN DEFAULT FALSE,
    opened_date     DATE,
    brand           VARCHAR(100),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- MEAL PREFERENCES / SELECTION PROTOCOL
-- ============================================================

CREATE TABLE meal_types (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(30) NOT NULL UNIQUE        -- 'breakfast', 'lunch', 'dinner', 'snack'
);

CREATE TABLE meal_preferences (
    id                  SERIAL PRIMARY KEY,
    meal_type_id        INT NOT NULL REFERENCES meal_types(id),
    profile_name        VARCHAR(50) NOT NULL,  -- 'cutting', 'bulking', 'maintenance'
    target_calories     INT,
    min_protein_g       NUMERIC(5,1),
    max_carbs_g         NUMERIC(5,1),
    max_fat_g           NUMERIC(5,1),
    exclude_categories  INT[]                  -- array of category IDs to exclude
);

-- Protocol run log (what the Python script selected and why)
CREATE TABLE protocols (
    id              SERIAL PRIMARY KEY,
    run_at          TIMESTAMP DEFAULT NOW(),
    meal_type_id    INT REFERENCES meal_types(id),
    profile_name    VARCHAR(50),
    notes           TEXT
);

CREATE TABLE protocol_selections (
    id              SERIAL PRIMARY KEY,
    protocol_id     INT NOT NULL REFERENCES protocols(id),
    inventory_id    INT NOT NULL REFERENCES inventory(id),
    quantity_used   NUMERIC(7,1),
    reason          TEXT                       -- why this item was selected
);
