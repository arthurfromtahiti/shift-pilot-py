import unittest

from inventory.warehouse import available_qty, find_by_sku, items_in_zone


class TestWarehouse(unittest.TestCase):
    def test_find_by_sku(self):
        self.assertIsNotNone(find_by_sku("AX-100"))
        self.assertIsNone(find_by_sku("INEXISTANT"))

    def test_items_in_zone(self):
        self.assertEqual(len(items_in_zone("A")), 2)

    def test_available_qty_never_negative(self):
        # Test ROUGE volontaire : CX-330 a 45 en stock et 50 réservés.
        # La disponibilité ne doit jamais descendre sous zéro.
        item = find_by_sku("CX-330")
        self.assertEqual(available_qty(item), 0)


if __name__ == "__main__":
    unittest.main()
