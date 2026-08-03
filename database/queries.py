"""
Query helpers — turns raw database rows into the shapes the templates need.
Keeps app.py focused on routing, not SQL.
"""

from datetime import datetime, date
from database.db import get_db_connection


def get_product_list():
    """
    Returns one row per product with:
    - current_stock: computed by summing all movements across all its batches
    - expiry_status: 'Fine' / 'Expiring Soon' / 'Expired', based on the nearest batch expiry
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.category, p.dosage_form,
               COALESCE(SUM(sm.quantity), 0) AS current_stock,
               MIN(pb.expiry_date) AS nearest_expiry
        FROM product p
        LEFT JOIN product_batch pb ON pb.product_id = p.id
        LEFT JOIN stock_movement sm ON sm.product_batch_id = pb.id
        GROUP BY p.id
        ORDER BY p.name
    """)
    rows = cur.fetchall()
    conn.close()

    today = date.today()
    products = []
    for row in rows:
        expiry_status = "Fine"
        if row["nearest_expiry"]:
            expiry_date = datetime.strptime(row["nearest_expiry"], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            if days_left < 0:
                expiry_status = "Expired"
            elif days_left <= 90:
                expiry_status = "Expiring Soon"

        products.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"] or "—",
            "dosage_form": row["dosage_form"] or "—",
            "current_stock": row["current_stock"],
            "expiry_status": expiry_status,
        })
    return products