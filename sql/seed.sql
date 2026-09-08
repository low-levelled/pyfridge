-- ============================================================
-- SEED DATA — The Ultimate Fridge
-- ============================================================

-- ZONES (deck layout)
INSERT INTO fridge_zones (name, zone_type, temp_c, position_order) VALUES
  ('top_shelf',        'shelf',  2.0, 1),
  ('middle_shelf',     'shelf',  3.0, 2),
  ('bottom_shelf',     'shelf',  4.0, 3),
  ('deli_drawer',      'drawer', 2.0, 4),
  ('crisper_left',     'drawer', 5.0, 5),
  ('crisper_right',    'drawer', 5.0, 6),
  ('door_top',         'door',   7.0, 7),
  ('door_middle',      'door',   7.0, 8),
  ('door_bottom',      'door',   7.0, 9);

-- POSITIONS (slots within each zone — like Hamilton rack positions)
INSERT INTO fridge_positions (zone_id, slot, label, max_weight_g) VALUES
  -- top shelf: 4 slots
  (1, 1, 'TS-1', 3000), (1, 2, 'TS-2', 3000), (1, 3, 'TS-3', 3000), (1, 4, 'TS-4', 3000),
  -- middle shelf: 4 slots
  (2, 1, 'MS-1', 4000), (2, 2, 'MS-2', 4000), (2, 3, 'MS-3', 4000), (2, 4, 'MS-4', 4000),
  -- bottom shelf: 4 slots
  (3, 1, 'BS-1', 5000), (3, 2, 'BS-2', 5000), (3, 3, 'BS-3', 5000), (3, 4, 'BS-4', 5000),
  -- deli drawer: 3 slots
  (4, 1, 'DD-1', 2000), (4, 2, 'DD-2', 2000), (4, 3, 'DD-3', 2000),
  -- crisper left: 3 slots
  (5, 1, 'CL-1', 3000), (5, 2, 'CL-2', 3000), (5, 3, 'CL-3', 3000),
  -- crisper right: 3 slots
  (6, 1, 'CR-1', 3000), (6, 2, 'CR-2', 3000), (6, 3, 'CR-3', 3000),
  -- door top: 3 slots
  (7, 1, 'DT-1', 1500), (7, 2, 'DT-2', 1500), (7, 3, 'DT-3', 1500),
  -- door middle: 3 slots
  (8, 1, 'DM-1', 2000), (8, 2, 'DM-2', 2000), (8, 3, 'DM-3', 2000),
  -- door bottom: 2 slots
  (9, 1, 'DB-1', 4000), (9, 2, 'DB-2', 4000);

-- CATEGORIES
INSERT INTO food_categories (name, storage_type) VALUES
  ('dairy',      'refrigerated'),
  ('produce',    'refrigerated'),
  ('meat',       'refrigerated'),
  ('leftovers',  'refrigerated'),
  ('condiments', 'refrigerated'),
  ('beverages',  'refrigerated'),
  ('eggs',       'refrigerated'),
  ('deli',       'refrigerated');

-- FOOD ITEMS (master catalog with macros per 100g)
INSERT INTO food_items (name, category_id, calories_per_100g, protein_g, carbs_g, fat_g, fiber_g, unit_type) VALUES
  -- dairy
  ('Whole Milk',              1, 61,   3.2,  4.8,  3.3, 0.0, 'ml'),
  ('Greek Yogurt',            1, 97,  10.0,  3.6,  5.0, 0.0, 'g'),
  ('Cheddar Cheese',          1, 403, 25.0,  1.3, 33.0, 0.0, 'g'),
  ('Cottage Cheese',          1, 98,  11.1,  3.4,  4.3, 0.0, 'g'),
  ('Butter',                  1, 717,  0.9,  0.1, 81.0, 0.0, 'g'),
  -- produce
  ('Broccoli',                2,  34,  2.8,  6.6,  0.4, 2.6, 'g'),
  ('Spinach',                 2,  23,  2.9,  3.6,  0.4, 2.2, 'g'),
  ('Bell Pepper',             2,  31,  1.0,  6.0,  0.3, 2.1, 'g'),
  ('Cherry Tomatoes',         2,  18,  0.9,  3.9,  0.2, 1.2, 'g'),
  ('Baby Carrots',            2,  41,  0.9,  9.6,  0.2, 2.8, 'g'),
  ('Avocado',                 2, 160,  2.0,  9.0, 15.0, 6.7, 'g'),
  ('Blueberries',             2,  57,  0.7, 14.5,  0.3, 2.4, 'g'),
  -- meat
  ('Chicken Breast',          3, 165, 31.0,  0.0,  3.6, 0.0, 'g'),
  ('Ground Beef 90/10',       3, 176, 26.1,  0.0,  7.5, 0.0, 'g'),
  ('Salmon Fillet',           3, 208, 20.0,  0.0, 13.0, 0.0, 'g'),
  ('Turkey Slices',           8, 135, 17.0,  1.5,  6.0, 0.0, 'g'),
  -- leftovers
  ('Rice and Beans',          4, 140,  5.0, 26.0,  1.5, 3.0, 'g'),
  ('Pasta Bolognese',         4, 180,  9.0, 22.0,  6.0, 1.5, 'g'),
  -- condiments
  ('Hot Sauce',               5,  11,  0.5,  2.0,  0.5, 0.0, 'ml'),
  ('Mustard',                 5,  66,  3.7,  5.8,  3.7, 2.0, 'g'),
  ('Hummus',                  5, 166,  8.0, 14.0,  9.6, 6.0, 'g'),
  -- beverages
  ('Orange Juice',            6,  45,  0.7, 10.4,  0.2, 0.2, 'ml'),
  ('Cold Brew Coffee',        6,   5,  0.3,  0.6,  0.1, 0.0, 'ml'),
  -- eggs
  ('Large Eggs',              7, 143, 13.0,  0.7, 10.0, 0.0, 'each');

-- INVENTORY (what is actually in the fridge today: 2026-09-07)
INSERT INTO inventory (food_item_id, position_id, quantity, purchase_date, expiry_date, opened, opened_date, brand, notes) VALUES
  -- top shelf
  (2,  1, 500,  '2026-09-05', '2026-09-14', true,  '2026-09-05', 'Fage',       'Protein-packed'),
  (4,  2, 400,  '2026-09-04', '2026-09-11', false, NULL,         'Daisy',      NULL),
  (23, 3, 500,  '2026-09-06', '2026-09-13', true,  '2026-09-06', 'Chameleon',  'Cold brew concentrate'),
  (17, 4, 300,  '2026-09-03', '2026-09-08', true,  '2026-09-03', NULL,         'Homemade, fridge day 4'),
  -- middle shelf
  (13, 5, 600,  '2026-09-06', '2026-09-10', false, NULL,         'Organic',    'Marinated'),
  (15, 6, 400,  '2026-09-05', '2026-09-09', false, NULL,         'Wild-caught',NULL),
  (18, 7, 450,  '2026-09-02', '2026-09-07', true,  '2026-09-02', NULL,         'Eat today!'),
  (21, 8, 200,  '2026-09-01', '2026-09-15', true,  '2026-09-01', 'Sabra',      NULL),
  -- bottom shelf
  (14, 9,  500, '2026-09-05', '2026-09-09', false, NULL,         'Grass-fed',  NULL),
  (1,  10, 1000,'2026-09-04', '2026-09-18', true,  '2026-09-04', 'Organic Valley', NULL),
  (3,  11, 200, '2026-09-01', '2026-09-30', false, NULL,         'Tillamook',  'Block'),
  (5,  12, 250, '2026-09-01', '2026-10-01', false, NULL,         'Kerrygold',  NULL),
  -- deli drawer
  (16, 13, 300, '2026-09-05', '2026-09-12', false, NULL,         'Boars Head', NULL),
  -- crisper left (produce)
  (6,  14, 300, '2026-09-05', '2026-09-14', false, NULL,         'Organic',    NULL),
  (7,  15, 150, '2026-09-06', '2026-09-13', false, NULL,         'Baby spinach bag', NULL),
  (11, 16, 250, '2026-09-04', '2026-09-08', false, NULL,         NULL,         '2 avocados'),
  -- crisper right (produce)
  (8,  17, 200, '2026-09-03', '2026-09-10', false, NULL,         NULL,         '2 peppers'),
  (9,  18, 300, '2026-09-05', '2026-09-12', false, NULL,         NULL,         NULL),
  (12, 19, 200, '2026-09-06', '2026-09-12', false, NULL,         NULL,         'Pint'),
  -- door top (condiments/small)
  (19, 20, 150, '2026-08-01', '2027-01-01', true,  '2026-08-01', 'Cholula',    NULL),
  (20, 21, 200, '2026-08-15', '2027-03-01', true,  '2026-08-15', 'Grey Poupon',NULL),
  -- door middle (beverages)
  (22, 22, 800, '2026-09-05', '2026-09-19', true,  '2026-09-05', 'Tropicana',  NULL),
  -- door bottom (eggs, milk)
  (24, 23, 12,  '2026-09-04', '2026-10-04', false, NULL,         'Local farm', '12-pack, used 0'),
  (10, 24, 400, '2026-09-05', '2026-09-19', false, NULL,         'Organic',    'Baby carrot bag');

-- Mark occupied positions
UPDATE fridge_positions SET is_occupied = TRUE
WHERE id IN (
  SELECT DISTINCT position_id FROM inventory WHERE position_id IS NOT NULL
);

-- MEAL TYPES
INSERT INTO meal_types (name) VALUES
  ('breakfast'), ('lunch'), ('dinner'), ('snack');

-- MEAL PREFERENCES (profiles)
INSERT INTO meal_preferences (meal_type_id, profile_name, target_calories, min_protein_g, max_carbs_g, max_fat_g, exclude_categories) VALUES
  (1, 'cutting',     400, 30.0, 40.0, 15.0, NULL),
  (1, 'bulking',     700, 40.0, 80.0, 25.0, NULL),
  (2, 'cutting',     500, 40.0, 40.0, 15.0, NULL),
  (2, 'bulking',     800, 50.0, 90.0, 30.0, NULL),
  (3, 'cutting',     600, 45.0, 50.0, 20.0, NULL),
  (3, 'bulking',    1000, 60.0,110.0, 35.0, NULL),
  (4, 'cutting',     200, 15.0, 20.0, 10.0, NULL),
  (4, 'bulking',     400, 20.0, 50.0, 15.0, NULL);
