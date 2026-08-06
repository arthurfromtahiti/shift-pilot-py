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

    Exclut silencieusement les lignes dont la disponibilité est insuffisante.
    Les allocations cumulées du même SKU dans la même commande sont prises en compte
    pour éviter de dépasser le stock disponible.
    """
    out = []
    allocated = {}
    for sku, qty in lines:
        if qty <= 0:
            continue
        item = find_by_sku(sku)
        if item is None:
            continue
        remaining = available_qty(item) - allocated.get(sku, 0)
        if qty > remaining:
            continue
        allocated[sku] = allocated.get(sku, 0) + qty
        out.append({"sku": sku, "zone": item["zone"], "qty": qty})
    return sorted(out, key=lambda entry: entry["zone"])
