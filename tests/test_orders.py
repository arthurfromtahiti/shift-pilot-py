import unittest

from inventory.orders import picking_list


class TestPickingList(unittest.TestCase):
    def test_article_hors_stock_exclu_des_picks(self):
        # BX-220 : qty=0, reserved=0 → available=0 ; doit être absent des picks
        result = picking_list([("BX-220", 1)])
        self.assertEqual(result["picks"], [])

    def test_article_hors_stock_journalise_dans_skipped(self):
        # BX-220 : available=0, demandé=1 → manquant=1 ; doit figurer dans skipped
        result = picking_list([("BX-220", 1)])
        self.assertEqual(len(result["skipped"]), 1)
        s = result["skipped"][0]
        self.assertEqual(s["order_id"], 0)
        self.assertEqual(s["sku"], "BX-220")
        self.assertEqual(s["qty_requested"], 1)
        self.assertEqual(s["qty_missing"], 1)

    def test_cx330_inclus_dans_picks(self):
        # CX-330 : qty=45, reserved=5 → available=40 ; doit figurer dans picks
        result = picking_list([("CX-330", 10)])
        self.assertEqual(len(result["picks"]), 1)
        self.assertEqual(result["picks"][0]["sku"], "CX-330")
        self.assertEqual(result["picks"][0]["qty"], 10)
        self.assertEqual(result["skipped"], [])

    def test_quantite_nulle_exclue_sans_trace(self):
        # qty=0 : ligne invalide, exclue sans entrée dans skipped
        result = picking_list([("CX-330", 0)])
        self.assertEqual(result["picks"], [])
        self.assertEqual(result["skipped"], [])

    def test_quantite_negative_exclue_sans_trace(self):
        # qty<0 : ligne invalide, exclue sans entrée dans skipped
        result = picking_list([("CX-330", -5)])
        self.assertEqual(result["picks"], [])
        self.assertEqual(result["skipped"], [])

    def test_plusieurs_lignes_meme_sku_depassement_exclu_des_picks(self):
        # CX-330 : available=40 ; deux lignes de 30 → 2e exclue des picks
        result = picking_list([("CX-330", 30), ("CX-330", 30)])
        self.assertEqual(len(result["picks"]), 1)
        self.assertEqual(result["picks"][0]["sku"], "CX-330")
        self.assertEqual(result["picks"][0]["qty"], 30)

    def test_plusieurs_lignes_meme_sku_depassement_journalise_dans_skipped(self):
        # CX-330 : available=40 ; 30 alloué → remaining=10 ; 2e ligne de 30 → manquant=20
        result = picking_list([("CX-330", 30), ("CX-330", 30)])
        self.assertEqual(len(result["skipped"]), 1)
        s = result["skipped"][0]
        self.assertEqual(s["order_id"], 1)
        self.assertEqual(s["sku"], "CX-330")
        self.assertEqual(s["qty_requested"], 30)
        self.assertEqual(s["qty_missing"], 20)

    def test_plusieurs_lignes_meme_sku_dans_les_limites(self):
        # CX-330 : available=40 ; deux lignes de 20 → les deux incluses, aucun skipped
        result = picking_list([("CX-330", 20), ("CX-330", 20)])
        self.assertEqual(len(result["picks"]), 2)
        self.assertTrue(all(e["sku"] == "CX-330" for e in result["picks"]))
        self.assertEqual(result["skipped"], [])

    def test_plusieurs_lignes_meme_sku_allocation_cumulative(self):
        # CX-330 : available=40 ; lignes 15+15+15 → 3e exclue (remaining=10, manquant=5)
        result = picking_list([("CX-330", 15), ("CX-330", 15), ("CX-330", 15)])
        self.assertEqual(len(result["picks"]), 2)
        self.assertTrue(all(e["sku"] == "CX-330" for e in result["picks"]))
        self.assertEqual(len(result["skipped"]), 1)
        s = result["skipped"][0]
        self.assertEqual(s["order_id"], 2)
        self.assertEqual(s["qty_missing"], 5)


    def test_meme_article_casse_differente_cumul_respecte(self):
        # AX-100 : available=10 ; "AX-100" (6) puis "ax-100" (6) → même article
        # cumul 6+6=12 > 10 → 2e ligne exclue avec qty_missing=2 (remaining=4, demandé=6)
        result = picking_list([("AX-100", 6), ("ax-100", 6)])
        self.assertEqual(len(result["picks"]), 1)
        self.assertEqual(result["picks"][0]["qty"], 6)
        self.assertEqual(len(result["skipped"]), 1)
        s = result["skipped"][0]
        self.assertEqual(s["order_id"], 1)
        self.assertEqual(s["sku"], "ax-100")
        self.assertEqual(s["qty_requested"], 6)
        self.assertEqual(s["qty_missing"], 2)


if __name__ == "__main__":
    unittest.main()
