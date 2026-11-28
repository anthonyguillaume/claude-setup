---
name: rules-testing
description: "Règles de dev ai-team (tests), préchargées par les agents. À charger avant d'écrire ou de relire du code de test ou du code testé."
---

# Règles tests

Quoi tester, comment, et ce qui est interdit. Pas de tests pour faire des tests.

- **AT-TST-01** Un test protège un comportement ou une règle. Avant de l'écrire, on doit pouvoir finir la phrase « ce test échoue si on casse ... ». Sinon il n'est pas écrit. Moins de tests, mais chacun justifié, rapide et lisible.
- **AT-TST-02** TDD partout : test rouge pour la bonne raison, puis code, puis vert. Un bug corrigé a un test qui échouait avant le correctif.
- **AT-TST-04** Pour chaque endpoint, chaque réponse applicable parmi nominal, 422 (erreurs par champ), 401, 403, 404 ; isolation (pack multitenant-postgres) si ce pack est actif, audit si le pack audit-trail est actif.
- **AT-TST-07** Seuil de couverture bloquant sur la couche domaine seulement (90 %). Ailleurs la couverture est mesurée sans seuil : elle sert à repérer un trou, pas à viser un chiffre.
- **AT-TST-08** Tests interdits : getters, setters et DTO, mappings triviaux, le framework lui-même, un mock qui ne teste que lui-même, le même cas testé à deux niveaux, les snapshots de composants entiers.
- **AT-TST-09** Tests déterministes et indépendants : pas de `sleep`, pas d'horloge réelle (horloge injectée), pas d'ordre imposé entre tests, pas de donnée mutable partagée. Chaque test d'intégration crée ses données.
- **AT-TST-10** Arrange / Act / Assert lisible, un test pour un comportement, peu de lignes. Les builders de données vivent dans le projet de test, pas dans le code de production. Côté front, `getByRole` avant `getByTestId`.
- **AT-TST-12** Un test instable est corrigé ou supprimé sous 48 h, jamais ignoré en silence. Un test ignoré (`Skip`, `it.skip`) pointe vers une dette notée dans le suivi du projet.
- **AT-TST-13** Un appel HTTP externe est toujours simulé (handler de test), jamais de réseau réel. Les tests de base utilisent la vraie base du projet, jamais une base en mémoire qui cacherait les défauts.
- **AT-TST-14** La sortie des tests est propre : aucun avertissement parasite.
- **AT-TST-15** Outils par stack : .NET xUnit et Shouldly (plus Testcontainers si Docker est présent), Node Vitest et Testing Library, Python pytest sinon unittest, Rust `cargo test`. E2E Playwright et axe si l'outil est présent. Les noms de tests sont en anglais et décrivent le comportement.
