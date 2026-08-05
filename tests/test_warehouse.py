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


if __name__ == "__main__":
    unittest.main()
