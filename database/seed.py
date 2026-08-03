"""
Seed data for PharmaTrack — inserts a handful of real products, batches,
and stock movements so the UI has actual numbers to display instead of
Stitch's hardcoded mock rows.

Run this once, after init_db() has already created the tables:
    python database/seed.py

Safe to re-run: it clears existing data first so you don't get duplicates.
"""

import uuid
from datetime import datetime, timedelta
from db import get_db_connection


def new_id():
    return str(uuid.uuid4())


def seed():
    conn = get_db_connection()
    cur = conn.cursor()

    # Clear existing data so this script can be run more than once safely
    cur.execute("DELETE FROM loss_report")
    cur.execute("DELETE FROM stock_movement")
    cur.execute("DELETE FROM product_batch")
    cur.execute("DELETE FROM product")
    cur.execute("DELETE FROM user")

    # --- User ---
    user_id = new_id()
    cur.execute(
        "INSERT INTO user (id, name, role, device_id) VALUES (?, ?, ?, ?)",
        (user_id, "Jean Dupont", "Lead Pharmacist", "device-001")
    )

    # --- Products (matches names used across the UI screens) ---
    products = [
        {"name": "Amoxicillin 500mg", "category": "Antibiotics", "strength": "500mg", "dosage_form": "Capsule",
         "requires_prescription": 1, "is_controlled": 0},
        {"name": "Paracetamol 500mg", "category": "Analgesics", "strength": "500mg", "dosage_form": "Tablet",
         "requires_prescription": 0, "is_controlled": 0},
        {"name": "Insulin Glargine 100u/ml", "category": "Diabetic Care", "strength": "100u/ml", "dosage_form": "Injection",
         "requires_prescription": 1, "is_controlled": 0},
        {"name": "Diazepam 5mg", "category": "Controlled - Sedative", "strength": "5mg", "dosage_form": "Tablet",
         "requires_prescription": 1, "is_controlled": 1},
        {"name": "Morphine Sulfate 10mg", "category": "Controlled - Analgesic", "strength": "10mg", "dosage_form": "Tablet",
         "requires_prescription": 1, "is_controlled": 1},
    ]

    today = datetime.now()

    for p in products:
        product_id = new_id()
        cur.execute(
            """INSERT INTO product (id, name, category, strength, dosage_form, requires_prescription, is_controlled)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, p["name"], p["category"], p["strength"], p["dosage_form"],
             p["requires_prescription"], p["is_controlled"])
        )

        # One batch per product, expiry a few months out (except one deliberately near-expiry)
        batch_id = new_id()
        expiry = today + timedelta(days=180)
        if p["name"] == "Insulin Glargine 100u/ml":
            expiry = today + timedelta(days=20)  # near-expiry, to test the "expiring soon" UI state

        cur.execute(
            """INSERT INTO product_batch (id, product_id, batch_number, expiry_date, received_at)
               VALUES (?, ?, ?, ?, ?)""",
            (batch_id, product_id, f"BN-{today.year}-{new_id()[:6].upper()}",
             expiry.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d %H:%M:%S'))
        )

        # A receipt movement (stock coming in) so current stock isn't zero
        starting_qty = 1500 if p["name"] != "Insulin Glargine 100u/ml" else 45  # low, to test low-stock UI state
        cur.execute(
            """INSERT INTO stock_movement
               (id, product_batch_id, movement_type, quantity, reference_number, performed_by_user_id, device_id)
               VALUES (?, ?, 'receipt', ?, ?, ?, ?)""",
            (new_id(), batch_id, starting_qty, f"GRN-{new_id()[:6].upper()}", user_id, "device-001")
        )

        # A small sale movement for realism (skip for the controlled/low-stock ones)
        if p["name"] not in ("Insulin Glargine 100u/ml", "Diazepam 5mg", "Morphine Sulfate 10mg"):
            cur.execute(
                """INSERT INTO stock_movement
                   (id, product_batch_id, movement_type, quantity, performed_by_user_id, device_id)
                   VALUES (?, ?, 'sale', ?, ?, ?)""",
                (new_id(), batch_id, -80, user_id, "device-001")
            )

    conn.commit()
    conn.close()
    print("Seed data inserted: 5 products, 5 batches, movements included.")


if __name__ == '__main__':
    seed()