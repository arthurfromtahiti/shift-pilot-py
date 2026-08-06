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

    def test_quantite_nulle_exclue(self):
        # qty=0 : ligne invalide, doit être exclue même si le stock est disponible
        result = picking_list([("CX-330", 0)])
        self.assertEqual(result, [])

    def test_quantite_negative_exclue(self):
        # qty<0 : ligne invalide, doit être exclue même si le stock est disponible
        result = picking_list([("CX-330", -5)])
        self.assertEqual(result, [])

    def test_plusieurs_lignes_meme_sku_depassement_exclu(self):
        # CX-330 : available=40 ; deux lignes de 30 → total 60 > 40 → la 2e doit être exclue
        result = picking_list([("CX-330", 30), ("CX-330", 30)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sku"], "CX-330")
        self.assertEqual(result[0]["qty"], 30)

    def test_plusieurs_lignes_meme_sku_dans_les_limites(self):
        # CX-330 : available=40 ; deux lignes de 20 → total 40 = available → les deux incluses
        result = picking_list([("CX-330", 20), ("CX-330", 20)])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(e["sku"] == "CX-330" for e in result))

    def test_plusieurs_lignes_meme_sku_allocation_cumulative(self):
        # CX-330 : available=40 ; lignes 15+15+15 → total 45 > 40 → la 3e exclue
        result = picking_list([("CX-330", 15), ("CX-330", 15), ("CX-330", 15)])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(e["sku"] == "CX-330" for e in result))


if __name__ == "__main__":
    unittest.main()
