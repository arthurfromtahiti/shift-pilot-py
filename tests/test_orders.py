import unittest

from inventory.orders import picking_list


class TestPickingList(unittest.TestCase):
    def test_article_hors_stock_exclu(self):
        # BX-220 : qty=0, reserved=0 → available=0 ; doit être absent de la liste
        result = picking_list([("BX-220", 1)])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
