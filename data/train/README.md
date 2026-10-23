# Données d'entraînement E2/E3 (EL-012)

Fichiers produits par `scripts/build_training_data.py` et versionnés exprès (malgré `.gitignore`) : le minage des négatifs par l'encodeur initial peut varier légèrement entre CPU et GPU, donc Colab réutilise ces fichiers au lieu de les régénérer. Empreintes attendues : `splits/data_sha256.json` (`scripts/verify_data.py`).

- `e2_hard.jsonl` : négatifs difficiles (pièges annotés + négatifs extraits par e5-small pour B-SYN).
- `e3_random.jsonl` : mêmes ancres et positifs, négatif tiré au hasard (B-REAL : dans un autre groupe).
- `manifest.json` : comptes et empreintes.

Origine et licence : les exemples `source = "breal"` contiennent des extraits de transcriptions SUMM-RE (Linagora, CC BY-SA 4.0, révision `47cb4ec`) et des questions annotées par Claude (provisoires, non relues) ; ils sont diffusés sous **CC BY-SA 4.0** avec cette attribution. Les exemples `source = "bsyn"` sont synthétiques (générateur du dépôt).
