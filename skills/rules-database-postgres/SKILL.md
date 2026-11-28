---
name: rules-database-postgres
description: "Règles de dev ai-team (base PostgreSQL), préchargées par les agents. À charger avant d'écrire ou de relire du code de schéma, de migrations, de requêtes SQL ou d'accès aux données."
---

# Règles base de données PostgreSQL

Portée : schéma, migrations, requêtes, rôles. Skills associés : `optimizing-ef-core-queries`, `postgresql-optimization`. L'isolation des données par client relève du pack multitenant-postgres.

- **AT-DB-01** `snake_case` partout : tables au pluriel, colonnes, clés étrangères `<table_singulier>_id`. Préfixes `pk_`, `fk_`, `uq_`, `ck_`, `ix_` (`ix_<table>_<colonnes>`). Aucun identifiant entre guillemets, la convention de l'ORM fait la correspondance.
- **AT-DB-02** Toute date-heure est `timestamptz`, écrite en UTC ; jamais `timestamp without time zone`. Une date seule est `date`.
- **AT-DB-03** Clés primaires `uuid` v7 (ordonnées dans le temps), générées par l'application, avec l'horloge injectée. Jamais `serial`, `identity` ni `gen_random_uuid()` (v4, fragmente l'index). Les identifiants exposés par l'API sont ces UUID.
- **AT-DB-04** Un invariant est une contrainte de base (`not null`, `unique`, `check`, clé étrangère), pas seulement un test applicatif. Énumérations en `text` plus `check`, pas d'entiers magiques. Concurrence optimiste par colonne `version` (ou `xmin`).
- **AT-DB-05** Deux rôles : `<app>_migrator` (migrations, propriétaire du schéma, DDL) et `<app>_app` (l'API : `SELECT/INSERT/UPDATE/DELETE` sur les tables métier, ni propriétaire ni `BYPASSRLS`). Une table d'audit n'accorde que `SELECT/INSERT` à `<app>_app`. L'application ne se connecte jamais avec `<app>_migrator` : deux chaînes de connexion, deux secrets. Les `GRANT` sont explicites dans la migration ; une table sans `GRANT` est inaccessible.
- **AT-DB-06** Une PR contient au plus une migration, avec un `Down` fonctionnel (ou une justification explicite dans la PR). Elle inclut les `GRANT` de ses tables, et s'exécute dans une étape dédiée, jamais au démarrage de l'API. Une migration fusionnée n'est jamais modifiée : on en ajoute une nouvelle.
- **AT-DB-07** Toute requête de liste a l'index qui la sert : les colonnes de filtre et de tri viennent en tête. La PR colle le résultat d'`EXPLAIN (ANALYZE, BUFFERS)` montrant un parcours d'index sur un jeu de données représentatif. Pas d'index « au cas où ».
- **AT-DB-08** Les lectures projettent vers un DTO, sans suivi des entités (`AsNoTracking` en EF Core), et ne chargent que les colonnes utiles. Pas d'`Include` en cascade pour afficher deux champs. Pagination par curseur, jamais `Skip/Take` profond.
- **AT-DB-09** Pas de N+1 : jamais de requête dans une boucle, chargement en lot. Le SQL brut est paramétré, jamais interpolé.
- **AT-DB-10** Une transaction par requête, ouverte par le pipeline (option A .NET) ou explicitement au début du traitement ailleurs. Les verrous consultatifs sont transactionnels (`pg_advisory_xact_lock`), jamais de verrou de session.
- **AT-DB-11** Toute nouvelle colonne de donnée personnelle est inscrite au registre de données du projet avec sa durée de conservation. Aucun secret en clair en base : empreinte (mots de passe, tickets) ou chiffrement.
- **AT-DB-12** Une requête HTTP émet 30 requêtes SQL au plus. Si la stack le permet, un test d'intégration le vérifie (compteur sur l'intercepteur de commandes) pour toute liste et tout endpoint qui charge des relations. Un dépassement est un N+1 à corriger, pas un seuil à relever.
