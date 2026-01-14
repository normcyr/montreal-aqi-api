# COPILOT.md

## 🎯 But

Fournir des instructions précises à GitHub Copilot / assistants automatisés pour contribuer au dépôt `montreal-aqi_api` de façon fiable, cohérente et sûre.

---

## 🔧 Principes opératoires (règles pour l'agent)

- Toujours proposer des changements petits et ciblés : une PR = un objectif clair. ✅
- **Ne pas commit/push automatiquement** sans instruction explicite de l'humain responsable. ⚠️
- Avant toute PR, exécuter localement les vérifications listées dans la section "Validation locale".
- Ne jamais ajouter de secrets, tokens ou identifiants en clair.
- Poser des questions si l'impact est incertain (tests, CI, breaking changes).

---

## 🧩 Règles spécifiques au dépôt

- Linter / Formatter : **Ruff**
  - Vérifier format : `ruff format --check .`
  - Vérifier lint : `ruff check .`
  - Appliquer le format : `ruff format .` (ne pas l'exécuter/pusher automatiquement).
- Tests : `pytest`
  - Exécuter : `pytest -q`
  - Exécuter un test précis : `pytest tests/test_file.py::test_name -q`
- Installation / dev env :
  - Créer un environnement : `python -m venv .venv` puis `source .venv/bin/activate`
  - Installer deps : `pip install -r requirements.txt` ou `pip install -e .[dev]` si disponible
- Configuration : `pyproject.toml` est la source de vérité pour les outils et dépendances.
- CI : `.github/workflows/ci.yml` — contient les étapes **Ruff** + **pytest** (vérifier toute modification de la CI avant PR).

---

## 📁 Arborescence clé & responsabilités

- `montreal_aqi_api/` — package principal : logique d'API, parsing, services, station, pollutants, CLI
  - `api.py` : wrapper pour appels API et parsers
  - `service.py` : logique métier pour récupération/agrégation
  - `station.py`, `pollutants.py` : modèles & utilitaires
  - `cli.py` : interface en ligne de commande
  - `_internal/` : utilitaires et parsing internes
- `tests/` — suite de tests pytest (unit et integration légère)
  - `test_*` couvrent parsing, service, CLI, etc.
  - `_schemas.py` : fixtures / schémas de test
- `pyproject.toml` — dépendances & configuration d'outils
- `.github/workflows/ci.yml` — pipeline CI
- `README.md` — instructions pour développeurs
- `commit_notes.md` — notes locales, **ne doit pas** être automatiquement commit/push (usage humain)

---

## 🧪 Validation locale avant proposition (Checklist)

Avant de proposer un PR ou une modification importante, l'agent doit vérifier :

- [ ] `ruff check .` passe
- [ ] `ruff format --check .` ne signale pas d'écart
- [ ] `pytest -q` et tous les tests passent
- [ ] Les nouvelles fonctions sont couvertes par des tests si applicables
- [ ] Les changements CI (si présents) sont documentés et expliqués

Si une des vérifications échoue, l'agent doit proposer une correction détaillée ou demander confirmation avant de modifier plus loin.

---

## 📋 Workflow recommandé pour une PR

1. Créer une branche descriptive (`feat/xxx`, `fix/yyy`, `chore/lint`)
2. Faire des commits atomiques avec messages Conventional Commits (ex. `chore(linting): ...`)
3. Vérifier localement la checklist ci‑dessus
4. Proposer la PR avec :
   - Titre clair et court
   - Description résumant la raison, les changements et le plan de validation
   - Checklist PR incluant `ruff check` et `pytest`
   - Mentionner si la CI a été modifiée
5. Ajouter une note dans `commit_notes.md` (localement) pour changements organisationnels (ne pas commit/push automatiquement)

---

## 🧰 Commandes usuelles (copier-coller)

- Linter : `ruff check .` / `ruff format --check .` / `ruff format .`
- Tests : `pytest -q`
- Exécuter CLI localement : `python -m montreal_aqi_api.cli --help` (ou la commande dédiée documentée dans README)
- Installer en mode dev : `pip install -e .[dev]` (si défini dans `pyproject.toml`)

---

## 🧾 CI & qualité

- CI exécute : `ruff format --check .`, `ruff check .`, puis `pytest`.
- Si une PR touche la CI, l'agent doit l'indiquer explicitement et proposer un plan de rollback ou test additionnel si nécessaire.

---

## 🛡️ Sécurité & limites

- Ne pas inclure de modifications qui exposent secrets ou access tokens.
- Éviter les modifications globales non testées (ex : refactor massif) sans plan, tests et approbation humaine.

---

## 🧾 Templates & exemples

### Exemple message de commit
`chore(linting): passer à Ruff pour le linting et le formatage`

### Exemple template PR (à coller dans la description)

```
Titre court : [Sujet concis]

Description :
- Pourquoi : bref justificatif
- Changements : liste des fichiers/clés modifiés

Checklist :
- [ ] `ruff check .` passe
- [ ] `pytest -q` passe
- [ ] Documentation mise à jour si nécessaire
```

---

## ✍️ Comportement attendu de l'agent

- Proposer toujours un plan court (1‑3 étapes) avant d'appliquer des changements majeurs.
- Pour tout changement impliquant CI/tests ou refactor, demander confirmation explicite.
- Si demandé, l'agent peut appliquer des modifications locales (fichiers) mais **attendra l'ordre** pour commit/push.

---

*Rédigé pour être exécutable par un assistant/agent — modifiez au besoin pour coller à vos conventions.*
