---
name: rules-pack-multitenant-postgres
description: "Pack de règles ai-team, à charger seulement si le CLAUDE.md du projet contient « Packs ai-team : multitenant-postgres ». Isolation des données entre locataires sur PostgreSQL : filtre ORM, RLS forcée, contexte transactionnel, tests."
---

# Règles pack multitenant-postgres

Portée : applications où plusieurs locataires partagent une même base PostgreSQL. Deux verrous indépendants isolent les données : le filtre global de l'ORM et la RLS (row level security). Rôles et types SQL : `rules-database-postgres`.

- **AT-MT-04** Verrou 1 : toute entité de locataire porte `TenantId` et un filtre global de requête `e.TenantId == currentTenant`, appliqué par convention à toute entité exposant cette propriété (pas d'opt-in à oublier). Sans locataire courant, la requête ne renvoie rien (échec fermé). Le contournement du filtre (`IgnoreQueryFilters`) n'est permis que dans du code plateforme explicitement revu et commenté ; les exclusions sont listées et justifiées en un seul endroit. Un test échoue pour toute entité de locataire sans filtre.
- **AT-MT-05** Verrou 2 : chaque table de locataire a `ENABLE` et `FORCE ROW LEVEL SECURITY`, et une politique comparant `tenant_id` à `nullif(current_setting('app.tenant_id', true), '')::uuid`, avec `USING` et `WITH CHECK`. Une RLS sans `FORCE` est contournée par le propriétaire de la table, une politique sans `WITH CHECK` laisse écrire chez autrui. `<app>_app` n'a jamais `BYPASSRLS` et aucun rôle applicatif ne contourne la RLS ; `<app>_migrator` exécute les migrations.
- **AT-MT-06** Au début de la transaction de chaque requête, le pipeline exécute `select set_config('app.tenant_id', <uuid>, true)` et `set_config('app.scope', 'tenant' | 'platform', true)`, plus `app.user_id` si la requête est authentifiée. Le troisième argument `true` rend la valeur locale à la transaction : elle ne survit pas dans le pool de connexions. Un `SET` de session est interdit (fuite d'une requête à l'autre). `app.scope` n'est `platform` que pour les requêtes marquées plateforme. Sans contexte posé, la politique ne renvoie rien.
- **AT-MT-08** Un identifiant valide mais appartenant à un autre locataire répond 404, jamais 403 : on ne révèle pas son existence.
- **AT-MT-11** Un test de schéma, écrit une fois, échoue si une table portant `tenant_id` n'a pas la RLS activée et forcée, ainsi qu'une politique (requête sur `pg_class`, `pg_attribute`, `pg_policy`). Une nouvelle table sans politique casse donc la suite avant la revue.
- **AT-TST-06** Un test d'intégration par endpoint prouve qu'un locataire ne voit jamais les données d'un autre : création dans A, requête en tant que B, résultat 404 ou liste vide. S'ajoute au test de schéma RLS de `AT-MT-11`.
