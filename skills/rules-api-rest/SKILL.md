---
name: rules-api-rest
description: "Règles de dev ai-team (API REST), préchargées par les agents. À charger avant d'écrire ou de relire du code d'endpoints HTTP, de contrats d'erreur, de pagination ou d'OpenAPI."
---

# Règles API REST

Portée : tous les endpoints HTTP du projet, sous le préfixe `/api/v1`. L'OpenAPI est générée, jamais écrite à la main.

- **AT-API-01** Toute URL commence par `/api/v1`. Ressources au pluriel en kebab-case (`/api/v1/user-accounts`), JSON en camelCase, aucun verbe dans l'URL sauf une action non-CRUD modélisée comme sous-ressource (`POST /api/v1/<ressource>-switches`).
- **AT-API-02** Les identifiants exposés sont des UUID opaques : ni séquentiels, ni porteurs d'information. Un contrôle d'objet est fait à chaque accès par identifiant.
- **AT-API-03** Verbes et codes justes : lire GET 200 ; créer POST 201 avec `Location` ; remplacer PUT 200 ou 204 ; modifier PATCH 200 ou 204 ; supprimer DELETE 204 ; action sans création POST 200 ou 202. Erreurs : 400 requête mal formée, 401 non authentifié, 403 interdit, 404 introuvable, 409 conflit d'état (doublon), 412 `If-Match` périmé, 422 règle métier violée, 429 débit atteint. Un GET ne modifie jamais d'état. Jamais 200 avec une erreur dans le corps.
- **AT-API-04** PUT et DELETE sont idempotents.
- **AT-API-05** Toute erreur est un `application/problem+json` (RFC 9457) avec `type`, `title`, `status`, `code` (stable, en anglais) et `traceId`, plus `detail` si utile (en anglais, sans donnée interne ni personnelle). Le texte affiché à l'utilisateur est produit par le front à partir de `code`.
- **AT-API-06** Un 500 n'expose ni pile, ni requête SQL, ni nom interne. Un 401, 403 ou 404 ne permet pas de distinguer « n'existe pas » de « interdit » quand cela révélerait une information.
- **AT-API-07** Une validation échouée renvoie 422 (400 si la forme est invalide) avec l'extension `errors: [{field, code}]`, par exemple `{"field": "email", "code": "validation.email_invalid"}`. Le front rattache chaque erreur à son champ.
- **AT-API-08** Toute liste accepte `limit` (20 par défaut, 100 au plus) et `cursor` (opaque), et répond `items` et `nextCursor` (`null` en fin). Pas de pagination par `offset`. Chaque liste a un index justifié par `EXPLAIN`.
- **AT-API-09** Filtres en paramètres nommés (`?status=active`), tri en `?sort=createdAt:desc` sur une liste blanche de champs. Un paramètre inconnu donne 400, jamais ignoré en silence.
- **AT-API-10** Un GET d'une ressource modifiable renvoie un `ETag` dérivé de la version de la ligne. Un PUT, PATCH ou DELETE avec un `If-Match` périmé reçoit 412 : aucune écriture perdue.
- **AT-API-11** Chaque réponse porte le `traceId`. `Content-Type` explicite, JSON en UTF-8, dates en ISO 8601 UTC (`2026-10-17T10:00:00Z`). Un 429 porte `Retry-After`.
- **AT-API-12** Chaque endpoint déclare ses réponses, ses codes et ses schémas. L'OpenAPI est générée à la compilation et comparée par la gate locale ; le client est régénéré et un diff non commité fait échouer la gate. Un changement cassant passe en `/api/v2`, jamais en modification silencieuse.
- **AT-API-14** PUT, PATCH et DELETE sur une ressource modifiable exigent `If-Match` : absent, 428 Precondition Required (`code = precondition.required`) ; périmé, 412. Aucune écriture sans la version lue.
