-- ============================================================
-- PYFRIDGE — PostgreSQL Schema
-- Hamilton-inspired smart fridge automation library
--
-- Physical reference: LG French Door (34"W x 42"H interior)
-- Coordinate system: origin = bottom-left-back corner
--   X = left → right (mm), max ~864mm
--   Y = bottom → top (mm), max ~1066mm
--   Z = back → front (mm), max ~660mm
-- ============================================================

DROP TABLE IF EXISTS protocol_selections CASCADE;
DROP TABLE IF EXISTS protocols CASCADE;
DROP TABLE IF EXISTS sandwich_components CASCADE;
DROP TABLE IF EXISTS sandwich_recipes CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS food_items CASCADE;
DROP TABLE IF EXISTS food_categories CASCADE;
DROP TABLE IF EXISTS fridge_positions CASCADE;
DROP TABLE IF EXISTS fridge_zones CASCADE;
DROP TABLE IF EXISTS meal_preferences CASCADE;
DROP TABLE IF EXISTS meal_types CASCADE;

-- ============================================================
-- DECK LAYOUT — Zone > Position > Coordinates
-- ============================================================

CREATE TABLE fridge_zones (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL UNIQUE,
    zone_type       VARCHAR(20) NOT NULL,       -- 'shelf', 'drawer', 'door', 'delivery'
    temp_c          NUMERIC(4,1),
    position_order  INT NOT NULL,               -- 1=top, higher=lower
    x_min_mm        NUMERIC(7,1),
    x_max_mm        NUMERIC(7,1),
    y_min_mm        NUMERIC(7,1),
    y_max_mm        NUMERIC(7,1),
    z_min_mm        NUMERIC(7,1),
    z_max_mm        NUMERIC(7,1)
);

CREATE TABLE fridge_positions (
    id              SERIAL PRIMARY KEY,
    zone_id         INT NOT NULL REFERENCES fridge_zones(id),
    slot            INT NOT NULL,
    label           VARCHAR(10),
    x_mm            NUMERIC(7,1),
    y_mm            NUMERIC(7,1),
    z_mm            NUMERIC(7,1),
    max_weight_g    NUMERIC(7,1),
    is_occupied     BOOLEAN DEFAULT FALSE,
    UNIQUE (zone_id, slot)
);

-- ============================================================
-- FOOD CATALOG
-- ============================================================

CREATE TABLE food_categories (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL UNIQUE,
    storage_type    VARCHAR(20)
);

CREATE TABLE food_items (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    category_id         INT NOT NULL REFERENCES food_categories(id),
    calories_per_100g   NUMERIC(6,1),
    protein_g           NUMERIC(5,1),
    carbs_g             NUMERIC(5,1),
    fat_g               NUMERIC(5,1),
    fiber_g             NUMERIC(5,1),
    unit_type           VARCHAR(10) NOT NULL,
    avg_weight_g        NUMERIC(7,1),
    avg_height_mm       NUMERIC(5,1),
    grippable           BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- INVENTORY
-- ============================================================

CREATE TABLE inventory (
    id              SERIAL PRIMARY KEY,
    food_item_id    INT NOT NULL REFERENCES food_items(id),
    position_id     INT REFERENCES fridge_positions(id),
    quantity        NUMERIC(7,1) NOT NULL,
    purchase_date   DATE NOT NULL,
    expiry_date     DATE,
    opened          BOOLEAN DEFAULT FALSE,
    opened_date     DATE,
    brand           VARCHAR(100),
    notes           TEXT,
    container_type  VARCHAR(30),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SANDWICH RECIPES
-- ============================================================

CREATE TABLE sandwich_recipes (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    description         TEXT,
    target_calories     INT,
    target_protein_g    NUMERIC(5,1)
);

CREATE TABLE sandwich_components (
    id              SERIAL PRIMARY KEY,
    recipe_id       INT NOT NULL REFERENCES sandwich_recipes(id),
    food_item_id    INT NOT NULL REFERENCES food_items(id),
    quantity_g      NUMERIC(6,1) NOT NULL,
    component_role  VARCHAR(20) NOT NULL,       -- 'bread', 'protein', 'topping', 'condiment'
    retrieval_order INT NOT NULL
);

-- ============================================================
-- MEAL PREFERENCES / PROTOCOLS
-- ============================================================

CREATE TABLE meal_types (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE meal_preferences (
    id                  SERIAL PRIMARY KEY,
    meal_type_id        INT NOT NULL REFERENCES meal_types(id),
    profile_name        VARCHAR(50) NOT NULL,
    target_calories     INT,
    min_protein_g       NUMERIC(5,1),
    max_carbs_g         NUMERIC(5,1),
    max_fat_g           NUMERIC(5,1),
    exclude_categories  INT[]
);

CREATE TABLE protocols (
    id              SERIAL PRIMARY KEY,
    run_at          TIMESTAMP DEFAULT NOW(),
    meal_type_id    INT REFERENCES meal_types(id),
    profile_name    VARCHAR(50),
    recipe_id       INT REFERENCES sandwich_recipes(id),
    notes           TEXT
);

CREATE TABLE protocol_selections (
    id              SERIAL PRIMARY KEY,
    protocol_id     INT NOT NULL REFERENCES protocols(id),
    inventory_id    INT NOT NULL REFERENCES inventory(id),
    quantity_used   NUMERIC(7,1),
    retrieval_order INT,
    target_x_mm     NUMERIC(7,1),
    target_y_mm     NUMERIC(7,1),
    target_z_mm     NUMERIC(7,1),
    reason          TEXT
);
