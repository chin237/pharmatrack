-- PharmaTrack local database schema (SQLite)
-- Matches the ERD: Product -> ProductBatch -> StockMovement -> (optional) LossReport
-- IDs are UUID strings (TEXT), not auto-increment integers — required so records
-- created offline on different devices never collide when they sync later.

CREATE TABLE IF NOT EXISTS product (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    strength TEXT,
    dosage_form TEXT,
    barcode TEXT UNIQUE,
    requires_prescription INTEGER NOT NULL DEFAULT 0,  -- 0 = false, 1 = true
    is_controlled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS product_batch (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    batch_number TEXT,
    expiry_date TEXT,          -- stored as 'YYYY-MM-DD'
    received_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES product(id)
);

CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    device_id TEXT
);

CREATE TABLE IF NOT EXISTS stock_movement (
    id TEXT PRIMARY KEY,
    product_batch_id TEXT NOT NULL,
    movement_type TEXT NOT NULL,      -- receipt | sale | adjustment | transfer | return | destruction | loss
    quantity INTEGER NOT NULL,         -- signed: +in, -out
    counterparty_name TEXT,
    counterparty_address TEXT,
    reference_number TEXT,
    prescription_number TEXT,
    performed_by_user_id TEXT,
    device_id TEXT,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now')),
    recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
    reason TEXT,
    approved_by_user_id TEXT,
    synced_at TEXT,             -- NULL until pushed to the remote server
    FOREIGN KEY (product_batch_id) REFERENCES product_batch(id),
    FOREIGN KEY (performed_by_user_id) REFERENCES user(id),
    FOREIGN KEY (approved_by_user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS loss_report (
    id TEXT PRIMARY KEY,
    stock_movement_id TEXT NOT NULL,
    circumstances TEXT NOT NULL,
    reported_to_authority_at TEXT,   -- NULL = not yet reported
    authority_reference TEXT,
    FOREIGN KEY (stock_movement_id) REFERENCES stock_movement(id)
);

-- Helpful indexes for the queries the UI will actually run
CREATE INDEX IF NOT EXISTS idx_batch_product ON product_batch(product_id);
CREATE INDEX IF NOT EXISTS idx_product_barcode ON product(barcode);
CREATE INDEX IF NOT EXISTS idx_movement_batch ON stock_movement(product_batch_id);
CREATE INDEX IF NOT EXISTS idx_movement_synced ON stock_movement(synced_at);
CREATE INDEX IF NOT EXISTS idx_loss_movement ON loss_report(stock_movement_id);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR IGNORE INTO settings (key, value) VALUES ('low_stock_threshold', '100');
INSERT OR IGNORE INTO settings (key, value) VALUES ('pharmacy_name', 'PharmaTrack Pharmacy');