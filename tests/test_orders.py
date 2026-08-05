import unittest

from inventory.orders import picking_list


class TestPickingList(unittest.TestCase):
    def test_article_disponible_inclus(self):
        result = picking_list([("AX-100", 5)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sku"], "AX-100")
        self.assertEqual(result[0]["qty"], 5)

    def test_sku_inconnu_exclu(self):
        result = picking_list([("INEXISTANT", 1)])
        self.assertEqual(result, [])

    def test_stock_epuise_exclu(self):
        # BX-220 : qty=0, reserved=0 → available=0
        result = picking_list([("BX-220", 1)])
        self.assertEqual(result, [])

    def test_stock_surreserve_exclu(self):
        # CX-330 : qty=45, reserved=50 → available=0 après clamp
        result = picking_list([("CX-330", 1)])
        self.assertEqual(result, [])

    def test_quantite_insuffisante_exclue(self):
        # AX-100 : qty=12, reserved=2 → available=10 ; demander 11 doit échouer
        result = picking_list([("AX-100", 11)])
        self.assertEqual(result, [])

    def test_tri_par_zone(self):
        # AX-100 zone A, DX-440 zone C
        result = picking_list([("DX-440", 1), ("AX-100", 1)])
        self.assertEqual([r["sku"] for r in result], ["AX-100", "DX-440"])

    def test_melange_valide_invalide(self):
        # AX-100 ok, CX-330 surréservé → seul AX-100 dans la liste
        result = picking_list([("AX-100", 2), ("CX-330", 1)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sku"], "AX-100")


if __name__ == "__main__":
    unittest.main()
