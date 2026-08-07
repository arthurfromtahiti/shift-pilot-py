import unittest

from inventory.warehouse import available_qty, find_by_sku, items_in_zone


class TestWarehouse(unittest.TestCase):
    def test_find_by_sku(self):
        self.assertIsNotNone(find_by_sku("AX-100"))
        self.assertIsNone(find_by_sku("INEXISTANT"))

    def test_items_in_zone(self):
        self.assertEqual(len(items_in_zone("A")), 2)

    def test_available_qty_cx330(self):
        # CX-330 : qty=45, reserved=5 → doit afficher 40 unités disponibles.
        # Anomalie corrigée : reserved était à 50 (> qty), rendant l'article indisponible.
        item = find_by_sku("CX-330")
        self.assertEqual(available_qty(item), 40)

    def test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty(self):
        # Garde : si reserved > qty (donnée corrompue), available_qty doit retourner 0, jamais négatif.
        item = {"sku": "TEST", "qty": 10, "reserved": 15, "zone": "X"}
        self.assertEqual(available_qty(item), 0)

    def test_invariant_reserved_ne_depasse_pas_qty_dans_items(self):
        from inventory.warehouse import ITEMS
        for item in ITEMS:
            self.assertLessEqual(
                item["reserved"], item["qty"],
                f"SKU {item['sku']} : reserved={item['reserved']} > qty={item['qty']}",
            )

    def test_find_by_sku_insensible_casse(self):
        # 'ax-100' doit retrouver l'article 'AX-100'
        self.assertIsNotNone(find_by_sku("ax-100"))
        self.assertIsNotNone(find_by_sku("Ax-100"))
        self.assertIsNone(find_by_sku("INEXISTANT"))


if __name__ == "__main__":
    unittest.main()
