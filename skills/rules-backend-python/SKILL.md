---
name: rules-backend-python
description: "Règles de dev ai-team (back-end Python), préchargées par les agents. À charger avant d'écrire ou de relire du code Python du back-end."
---

# Règles back-end Python

Portée : tout le code Python du back-end (services, CLI, bibliothèques). HTTP : `rules-api-rest`. Base de données : `rules-database-postgres`.

- **AT-BP-01** Le code est rangé par fonctionnalité (un module ou dossier par cas d'usage), pas par type technique. Une fonctionnalité n'importe pas les éléments internes d'une autre.
- **AT-BP-02** Les cas métier attendus lèvent des exceptions métier dédiées portant un `code` stable en anglais (`domaine.cas`), jamais renommé ni réutilisé pour un autre sens. Jamais d'`except` muet : on traite l'erreur, on la journalise ou on la relève.
- **AT-BP-03** Les entrées sont validées aux frontières, avec des erreurs par champ : pydantic si le projet l'utilise, sinon du code explicite.
- **AT-BP-04** L'horloge est injectée (pas d'appel direct à `datetime.now()` dans la logique) et les dates sont en UTC.
- **AT-BP-05** Le module `logging` est utilisé de façon structurée (paramètres nommés, pas d'f-string), messages en anglais. Aucune donnée personnelle (e-mail, nom, IP en clair, jeton) : on journalise des identifiants techniques.
- **AT-BP-06** Le code est typé ; `ruff` et `mypy` sont lancés si l'outil est présent. Dépendances épinglées, licences permissives (MIT, Apache-2.0, BSD, MPL-2.0, ISC), version vérifiée en ligne à l'ajout et jamais de mémoire.
