# shift-pilot-py

Pilote SHIFT en **Python** — volontairement d'une stack différente des pilotes Node
(`shift-pilot-back`, `shift-pilot-front`), pour vérifier que l'onboarding et la
production ne supposent pas un écosystème JavaScript.

## Lancer les tests

```bash
python3 -m unittest discover -s tests -t .
```

Un test est **rouge volontairement** : `available_qty` ne borne pas la disponibilité
à zéro, si bien qu'un article plus réservé que stocké remonte une quantité négative.
