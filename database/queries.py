"""
Query helpers — turns raw database rows into the shapes the templates need.
Keeps app.py focused on routing, not SQL.
"""

from datetime import datetime, date
from database.db import get_db_connection


def get_product_list(search=None):
    """
    Returns one row per product with:
    - current_stock: computed by summing all movements across all its batches
    - expiry_status: 'Fine' / 'Expiring Soon' / 'Expired', based on the nearest batch expiry

    If search is given, only products whose name or a batch number contains
    that text (case-insensitive) are returned.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    if search:
        like_term = f"%{search}%"
        cur.execute("""
            SELECT p.id, p.name, p.category, p.dosage_form,
                   COALESCE(SUM(sm.quantity), 0) AS current_stock,
                   MIN(pb.expiry_date) AS nearest_expiry
            FROM product p
            LEFT JOIN product_batch pb ON pb.product_id = p.id
            LEFT JOIN stock_movement sm ON sm.product_batch_id = pb.id
            WHERE p.name LIKE ? OR pb.batch_number LIKE ?
            GROUP BY p.id
            ORDER BY p.name
        """, (like_term, like_term))
    else:
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

    low_stock_threshold = int(get_setting("low_stock_threshold", "100"))
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
            "is_low_stock": row["current_stock"] < low_stock_threshold,
            "expiry_status": expiry_status,
        })
    return products


def get_product_detail(product_id):
    """
    Returns full detail for one product: its info, every batch with
    computed remaining quantity + expiry status, and its 10 most recent
    stock movements. Returns None if the product doesn't exist.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product_row = cur.fetchone()
    if product_row is None:
        conn.close()
        return None

    cur.execute("""
        SELECT pb.id, pb.batch_number, pb.expiry_date, pb.received_at,
               COALESCE(SUM(sm.quantity), 0) AS quantity_remaining
        FROM product_batch pb
        LEFT JOIN stock_movement sm ON sm.product_batch_id = pb.id
        WHERE pb.product_id = ?
        GROUP BY pb.id
        ORDER BY pb.expiry_date ASC
    """, (product_id,))
    batch_rows = cur.fetchall()

    today = date.today()
    batches = []
    total_stock = 0
    for b in batch_rows:
        qty = b["quantity_remaining"]
        total_stock += qty
        status = "Healthy"
        if b["expiry_date"]:
            expiry_date = datetime.strptime(b["expiry_date"], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            if days_left < 0:
                status = "Expired"
            elif days_left <= 90:
                status = "Near Expiry"
        batches.append({
            "id": b["id"],
            "batch_number": b["batch_number"],
            "expiry_date": b["expiry_date"],
            "quantity_remaining": qty,
            "status": status,
        })

    cur.execute("""
        SELECT sm.movement_type, sm.quantity, sm.reference_number,
               sm.occurred_at, sm.counterparty_name, sm.reason
        FROM stock_movement sm
        JOIN product_batch pb ON pb.id = sm.product_batch_id
        WHERE pb.product_id = ?
        ORDER BY sm.occurred_at DESC
        LIMIT 10
    """, (product_id,))
    movements = [dict(m) for m in cur.fetchall()]

    conn.close()

    product = dict(product_row)
    product["total_stock"] = total_stock
    product["batches"] = batches
    product["movements"] = movements
    return product


def get_product_by_barcode(barcode):
    """Used when a barcode is scanned — if a product with this barcode
    already exists, return its id/name so the UI can warn instead of
    creating a duplicate product."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM product WHERE barcode = ?", (barcode,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"]}


def create_product(name, category, strength, dosage_form, barcode,
                    requires_prescription, is_controlled,
                    batch_number, expiry_date, initial_quantity,
                    performed_by_user_id=None):
    """
    Creates a product, its first batch, and the initial 'receipt' movement
    that gives it starting stock — all in one transaction, so you never end
    up with a product that has no batch, or a batch with no stock movement.
    Returns the new product's id.
    """
    import uuid

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        product_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO product
               (id, name, category, strength, dosage_form, barcode, requires_prescription, is_controlled)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, name, category, strength, dosage_form, barcode or None,
             1 if requires_prescription else 0, 1 if is_controlled else 0)
        )

        batch_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO product_batch (id, product_id, batch_number, expiry_date)
               VALUES (?, ?, ?, ?)""",
            (batch_id, product_id, batch_number, expiry_date)
        )

        if initial_quantity and int(initial_quantity) > 0:
            cur.execute(
                """INSERT INTO stock_movement
                   (id, product_batch_id, movement_type, quantity, performed_by_user_id, reason)
                   VALUES (?, ?, 'receipt', ?, ?, ?)""",
                (str(uuid.uuid4()), batch_id, int(initial_quantity), performed_by_user_id,
                 "Initial stock on product creation")
            )

        conn.commit()
        return product_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_products_for_dropdown():
    """Minimal product list for the Record Movement product selector."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, is_controlled FROM product ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"], "is_controlled": bool(r["is_controlled"])} for r in rows]


def get_batches_for_product(product_id):
    """Batches for one product, with current remaining quantity, for the
    batch dropdown that populates after a product is selected."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pb.id, pb.batch_number, pb.expiry_date,
               COALESCE(SUM(sm.quantity), 0) AS quantity_remaining
        FROM product_batch pb
        LEFT JOIN stock_movement sm ON sm.product_batch_id = pb.id
        WHERE pb.product_id = ?
        GROUP BY pb.id
        ORDER BY pb.expiry_date ASC
    """, (product_id,))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r["id"], "batch_number": r["batch_number"],
         "expiry_date": r["expiry_date"], "quantity_remaining": r["quantity_remaining"]}
        for r in rows
    ]


# Movement types where the entered quantity is stored as negative (stock going out)
_OUTBOUND_TYPES = {"sale", "transfer", "destruction", "loss"}
# Movement types where the entered quantity is stored as positive (stock coming in)
_INBOUND_TYPES = {"receipt", "return"}


def create_movement(product_batch_id, movement_type, quantity, adjustment_direction=None,
                     counterparty_name=None, counterparty_address=None,
                     reference_number=None, prescription_number=None,
                     reason=None, performed_by_user_id=None, device_id=None):
    """
    Records one stock movement. Quantity is always entered as a positive
    number by the pharmacist; this function applies the correct sign based
    on movement_type, so current stock (SUM of quantities) stays correct.

    For 'adjustment', adjustment_direction ('add' or 'remove') decides the sign,
    since an adjustment can go either way.

    For 'loss', also creates a linked loss_report row (required for the
    Loi n°97/019 unreported-loss tracking).

    Returns the new stock_movement id.
    """
    import uuid

    quantity = int(quantity)
    if movement_type in _OUTBOUND_TYPES:
        signed_quantity = -abs(quantity)
    elif movement_type in _INBOUND_TYPES:
        signed_quantity = abs(quantity)
    elif movement_type == "adjustment":
        signed_quantity = abs(quantity) if adjustment_direction == "add" else -abs(quantity)
    else:
        raise ValueError(f"Unknown movement_type: {movement_type}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        movement_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO stock_movement
               (id, product_batch_id, movement_type, quantity, counterparty_name,
                counterparty_address, reference_number, prescription_number,
                performed_by_user_id, device_id, reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (movement_id, product_batch_id, movement_type, signed_quantity,
             counterparty_name, counterparty_address, reference_number,
             prescription_number, performed_by_user_id, device_id, reason)
        )

        if movement_type == "loss":
            cur.execute(
                """INSERT INTO loss_report (id, stock_movement_id, circumstances)
                   VALUES (?, ?, ?)""",
                (str(uuid.uuid4()), movement_id, reason or "No reason provided")
            )

        conn.commit()
        return movement_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_product_id_for_batch(batch_id):
    """Used after saving a movement, to know which product page to redirect to."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id FROM product_batch WHERE id = ?", (batch_id,))
    row = cur.fetchone()
    conn.close()
    return row["product_id"] if row else None


def get_loss_reports():
    """
    Real loss history for the Loss Reports screen: joins loss_report back to
    the movement, batch, and product that generated it. Also returns summary
    stats actually computable from real data (no fabricated numbers).
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT lr.id AS loss_report_id, lr.circumstances, lr.reported_to_authority_at,
               lr.authority_reference,
               sm.occurred_at, sm.quantity, sm.reference_number,
               pb.batch_number,
               p.name AS product_name, p.is_controlled
        FROM loss_report lr
        JOIN stock_movement sm ON sm.id = lr.stock_movement_id
        JOIN product_batch pb ON pb.id = sm.product_batch_id
        JOIN product p ON p.id = pb.product_id
        ORDER BY sm.occurred_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    losses = []
    for r in rows:
        losses.append({
            "loss_report_id": r["loss_report_id"],
            "date": r["occurred_at"],
            "product_name": r["product_name"],
            "batch_number": r["batch_number"],
            "quantity": abs(r["quantity"]),
            "reason": r["circumstances"],
            "is_controlled": bool(r["is_controlled"]),
            "reported": r["reported_to_authority_at"] is not None,
            "reported_at": r["reported_to_authority_at"],
        })

    total_losses = len(losses)
    unreported_count = sum(1 for l in losses if not l["reported"])
    total_units_lost = sum(l["quantity"] for l in losses)

    # Most common reason - simple exact-text match count, honest given free-text reasons
    reason_counts = {}
    for l in losses:
        reason_counts[l["reason"]] = reason_counts.get(l["reason"], 0) + 1
    most_common_reason = max(reason_counts, key=reason_counts.get) if reason_counts else "—"

    return {
        "losses": losses,
        "total_losses": total_losses,
        "unreported_count": unreported_count,
        "total_units_lost": total_units_lost,
        "most_common_reason": most_common_reason,
    }


def mark_loss_reported(loss_report_id, authority_reference=None):
    """Marks a loss as reported to the authorities (Loi n°97/019 requirement)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE loss_report
           SET reported_to_authority_at = datetime('now'), authority_reference = ?
           WHERE id = ?""",
        (authority_reference, loss_report_id)
    )
    conn.commit()
    conn.close()


LOW_STOCK_THRESHOLD = 100  # same threshold used for the red-highlight in product_list


def get_dashboard_data():
    """
    Real numbers for the dashboard: counts for the stat cards, the actual
    low-stock products, actual expiring/expired batches, and the most
    recent stock movements across all products.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    low_stock_threshold = int(get_setting("low_stock_threshold", "100"))

    # Total products
    cur.execute("SELECT COUNT(*) AS c FROM product")
    total_products = cur.fetchone()["c"]

    # Per-product current stock, to find low-stock ones
    cur.execute("""
        SELECT p.id, p.name, COALESCE(SUM(sm.quantity), 0) AS current_stock
        FROM product p
        LEFT JOIN product_batch pb ON pb.product_id = p.id
        LEFT JOIN stock_movement sm ON sm.product_batch_id = pb.id
        GROUP BY p.id
    """)
    stock_rows = cur.fetchall()
    low_stock_items = [
        {"id": r["id"], "name": r["name"], "current_stock": r["current_stock"],
         "threshold": low_stock_threshold}
        for r in stock_rows if r["current_stock"] < low_stock_threshold
    ]
    low_stock_items.sort(key=lambda x: x["current_stock"])

    # Batches that are expired or expiring within 90 days
    cur.execute("""
        SELECT pb.batch_number, pb.expiry_date, p.name AS product_name
        FROM product_batch pb
        JOIN product p ON p.id = pb.product_id
        WHERE pb.expiry_date IS NOT NULL
        ORDER BY pb.expiry_date ASC
    """)
    batch_rows = cur.fetchall()

    today = date.today()
    expiry_watch = []
    for b in batch_rows:
        expiry_date = datetime.strptime(b["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry_date - today).days
        if days_left <= 90:
            expiry_watch.append({
                "product_name": b["product_name"],
                "batch_number": b["batch_number"],
                "expiry_date": b["expiry_date"],
                "days_left": days_left,
                "status": "Expired" if days_left < 0 else "Warning",
            })

    # Most recent 5 movements across all products
    cur.execute("""
        SELECT sm.movement_type, sm.quantity, sm.reference_number, sm.occurred_at,
               sm.counterparty_name, p.name AS product_name
        FROM stock_movement sm
        JOIN product_batch pb ON pb.id = sm.product_batch_id
        JOIN product p ON p.id = pb.product_id
        ORDER BY sm.occurred_at DESC
        LIMIT 5
    """)
    recent_movements = [dict(r) for r in cur.fetchall()]

    conn.close()

    unreported_losses_count = get_loss_reports()["unreported_count"]

    return {
        "total_products": total_products,
        "low_stock_items": low_stock_items,
        "low_stock_count": len(low_stock_items),
        "expiry_watch": expiry_watch,
        "expiring_soon_count": len(expiry_watch),
        "unreported_losses_count": unreported_losses_count,
        "recent_movements": recent_movements,
    }


def update_product(product_id, name, category, strength, dosage_form, barcode,
                    requires_prescription, is_controlled):
    """Updates a product's own fields. Does NOT touch batches or stock -
    those only ever change through Record Movement, by design."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE product
           SET name = ?, category = ?, strength = ?, dosage_form = ?, barcode = ?,
               requires_prescription = ?, is_controlled = ?
           WHERE id = ?""",
        (name, category, strength, dosage_form, barcode or None,
         1 if requires_prescription else 0, 1 if is_controlled else 0, product_id)
    )
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO settings (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def get_alert_count():
    """Lightweight combined count for the header notification badge -
    reuses the same real numbers as the dashboard (low stock + expiring +
    unreported losses), without building the full detail lists."""
    data = get_dashboard_data()
    return data["low_stock_count"] + data["expiring_soon_count"] + data["unreported_losses_count"]


def get_users():
    """All users, for the admin's account management page (no password data)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, role FROM user ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"], "role": r["role"]} for r in rows]


def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, role FROM user WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "role": row["role"]}


def admin_exists():
    """Used to enforce a single admin account system-wide: the 'admin'
    role option is only offered at registration (and in Manage Accounts)
    when this returns False."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user WHERE role = 'admin' LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row is not None


def user_name_exists(name):
    """Used during self-registration to prevent two accounts sharing a name
    - login looks users up by name, so names must be unique."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def create_user(name, role, password):
    """role should be 'admin' or 'pharmacist'. Password is hashed before
    storage - the plaintext password is never saved anywhere."""
    import uuid
    from werkzeug.security import generate_password_hash

    conn = get_db_connection()
    cur = conn.cursor()
    user_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO user (id, name, role, password_hash) VALUES (?, ?, ?, ?)",
        (user_id, name, role, generate_password_hash(password))
    )
    conn.commit()
    conn.close()
    return user_id


def authenticate_user(name, password):
    """
    Checks a login attempt against the stored password hash.
    Returns the user dict on success, or None on failure - the caller
    should show the same generic error either way (wrong name, or right
    name/wrong password), so a login attempt can't be used to discover
    which usernames exist.
    """
    from werkzeug.security import check_password_hash

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, role, password_hash FROM user WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()

    if row is None or not row["password_hash"]:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return {"id": row["id"], "name": row["name"], "role": row["role"]}


def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_movements_for_export():
    """All stock movements with product/batch context, for CSV export."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT sm.occurred_at, p.name AS product_name, pb.batch_number,
               sm.movement_type, sm.quantity, sm.reference_number,
               sm.counterparty_name, sm.reason
        FROM stock_movement sm
        JOIN product_batch pb ON pb.id = sm.product_batch_id
        JOIN product p ON p.id = pb.product_id
        ORDER BY sm.occurred_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows