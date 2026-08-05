import unittest

from inventory.orders import picking_list


class TestPickingList(unittest.TestCase):
    def test_article_hors_stock_exclu(self):
        # BX-220 : qty=0, reserved=0 → available=0 ; doit être absent de la liste
        result = picking_list([("BX-220", 1)])
        self.assertEqual(result, [])

    def test_cx330_inclus_dans_picking_list(self):
        # CX-330 : qty=45, reserved=5 → available=40 ; doit figurer dans la liste
        result = picking_list([("CX-330", 10)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sku"], "CX-330")
        self.assertEqual(result[0]["qty"], 10)


if __name__ == "__main__":
    unittest.main()
