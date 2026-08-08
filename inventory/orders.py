"""Domaine « préparation de commande »."""

from inventory.warehouse import find_by_sku, available_qty


def can_fulfil(sku, requested):
    if requested <= 0:
        return False
    item = find_by_sku(sku)
    if item is None:
        return False
    return available_qty(item) >= requested


def picking_list(lines):
    """Transforme des lignes de commande en liste de prélèvement.

    Retourne {"picks": [...], "skipped": [...]}.
    - picks : lignes servies, triées par zone.
    - skipped : lignes non servies par stock insuffisant,
      chaque entrée contient order_id (index dans lines), sku,
      qty_requested et qty_missing.
    Les lignes invalides (qty <= 0, SKU inconnu) sont ignorées sans trace.
    """
    picks = []
    skipped = []
    allocated = {}
    for idx, (sku, qty) in enumerate(lines):
        if qty <= 0:
            continue
        item = find_by_sku(sku)
        if item is None:
            continue
        canonical = item["sku"]
        remaining = available_qty(item) - allocated.get(canonical, 0)
        if qty > remaining:
            skipped.append({
                "order_id": idx,
                "sku": sku,
                "qty_requested": qty,
                "qty_missing": qty - remaining,
            })
            continue
        allocated[canonical] = allocated.get(canonical, 0) + qty
        picks.append({"sku": sku, "zone": item["zone"], "qty": qty})
    return {"picks": sorted(picks, key=lambda entry: entry["zone"]), "skipped": skipped}
