"""Domaine « entrepôt » — stock en mémoire, à but de démonstration."""

ITEMS = [
    {"sku": "AX-100", "label": "Ancre 10kg", "qty": 12, "reserved": 2, "zone": "A"},
    {"sku": "BX-220", "label": "Bouée gonflable", "qty": 0, "reserved": 0, "zone": "B"},
    {"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 50, "zone": "A"},
    {"sku": "DX-440", "label": "Dérive alu", "qty": 7, "reserved": 1, "zone": "C"},
]


def list_items():
    return ITEMS


def find_by_sku(sku):
    for item in ITEMS:
        if item["sku"] == sku:
            return item
    return None


def available_qty(item):
    """Quantité réellement disponible à la vente.

    Bug volontaire : ne borne pas à zéro. CX-330 a 45 en stock mais 50 réservés,
    ce qui donne -5 — une quantité négative remonte jusqu'à l'appelant au lieu
    d'être ramenée à 0.
    """
    return item["qty"] - item["reserved"]


def items_in_zone(zone):
    return [i for i in ITEMS if i["zone"] == zone]
