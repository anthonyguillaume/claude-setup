---
name: rules-backend-rust
description: "Règles de dev ai-team (back-end Rust), préchargées par les agents. À charger avant d'écrire ou de relire du code Rust du back-end."
---

# Règles back-end Rust

Portée : tout le code Rust du back-end (services, CLI, bibliothèques). HTTP : `rules-api-rest`. Base de données : `rules-database-postgres`.

- **AT-BR-01** Le code est rangé par module de fonctionnalité (un module par cas d'usage), pas par type technique. Un module n'utilise pas les éléments internes d'un autre.
- **AT-BR-02** Les fonctions faillibles renvoient `Result` avec des erreurs `thiserror` portant un code stable en anglais (`domaine.cas`), jamais renommé ni réutilisé pour un autre sens. Pas d'`unwrap` ni d'`expect` hors tests.
- **AT-BR-03** L'horloge est injectée (pas d'appel direct à `SystemTime::now()` ni `Utc::now()` dans la logique) et les dates sont en UTC.
- **AT-BR-04** Les logs passent par `tracing` (champs nommés), messages en anglais. Aucune donnée personnelle (e-mail, nom, IP en clair, jeton) : on journalise des identifiants techniques.
- **AT-BR-05** `cargo clippy -- -D warnings` et `cargo fmt --check` passent si l'outil est présent. Licences permissives (MIT, Apache-2.0, BSD, MPL-2.0, ISC) vérifiées, avec `cargo deny` si l'outil est présent ; version d'une crate vérifiée en ligne, jamais de mémoire.
