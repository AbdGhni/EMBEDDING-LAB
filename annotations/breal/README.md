# Annotations B-REAL (SUMM-RE)

- **Statut** : annotations **provisoires** produites par des sous-agents Claude (`llm_provisional`) selon `docs/mandates/EL-007b-annotation.md`. Seules les réunions listées dans `splits/summre_v1_test_human_review.txt` seront relues par l'étudiant.
- **Source** : corpus SUMM-RE (LINAGORA, projet ANR-20-CE23-0017), révision `47cb4ec3437ef5497b6092b8c6d1e0b5b1d86dc0`, https://huggingface.co/datasets/linagora/SUMM-RE.
- **Licence** : ces fichiers contiennent des extraits des transcriptions ; ce sont des œuvres dérivées publiées sous **CC BY-SA 4.0**, comme le corpus d'origine.
- **Format** : `raw/<groupe>.json`, validé par `scripts/check_breal_raw.py`, assemblé par `embedding_lab.ingest.breal.assemble`.
- Ces fichiers ne sont pas régénérables (annotation non déterministe) : ils sont donc versionnés, contrairement aux données dérivées automatiquement.
