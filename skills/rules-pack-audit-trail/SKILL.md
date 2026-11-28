---
name: rules-pack-audit-trail
description: "Pack de règles ai-team, à charger seulement si le CLAUDE.md du projet contient « Packs ai-team : audit-trail ». Piste d'audit probante : écriture transactionnelle, événements de sécurité, table en ajout seul, chaînage par empreinte."
---

# Règles pack audit-trail

Portée : toute action qui doit être retrouvée après un incident ou lors d'un audit externe. L'audit est une preuve, pas un log de débogage ; la journalisation applicative est distincte.

- **AT-AUD-02** Les secrets et empreintes de mot de passe ne figurent jamais dans les valeurs avant/après : masqués par un attribut d'exclusion ou remplacés par `***`. L'IP et le user-agent sont des données personnelles : seulement dans l'audit (protégé, conservation limitée), jamais dans les logs applicatifs.
- **AT-AUD-03** L'entrée d'audit est écrite dans la même transaction que l'action : action annulée, trace annulée ; action validée, trace présente. Intercepteur de l'ORM pour les modifications de données, appel explicite pour les événements de sécurité, jamais une seconde connexion ni un `try/catch` qui avale l'erreur après coup.
- **AT-AUD-04** Événements de sécurité à tracer, liste minimale : connexion réussie et échouée, verrouillage, déconnexion, changement et réinitialisation de mot de passe, invitation (émise, renvoyée, révoquée, acceptée), ajout et retrait d'appartenance, modification des droits, bascule de contexte, accès refusé (403, au plus une entrée par acteur, route et minute), toute action d'administration plateforme, consultation et export de l'audit lui-même. Ajouter un événement de sécurité sans le tracer est un défaut bloquant en revue.
- **AT-AUD-05** L'audit des modifications de données est un choix explicite sur chaque commande ou entité : marqueur « audité » ou « non audité », jamais un audit de toute entité par défaut (bruit, coût, données sensibles). Les propriétés sensibles ou techniques sont exclues ; les champs techniques d'identité (tampons de sécurité, compteurs d'échecs) ne sont jamais tracés comme modifications, seuls leurs événements de sécurité le sont.
- **AT-AUD-07** La table d'audit est en ajout seul, garantie au niveau base et non par le seul code applicatif. Un trigger refuse toujours `UPDATE`, et `DELETE` sauf pour le rôle `<app>_migrator` via la fonction de purge. `<app>_app` n'a que `SELECT` et `INSERT`. La table est sous RLS forcée, avec `WITH CHECK` sur l'insertion, et `TRUNCATE` est refusé.
- **AT-AUD-08** Chaque entrée contient l'empreinte de la précédente : `hash = SHA256(prev_hash || contenu canonique)`, une chaîne par clé de chaîne (par exemple une par locataire, plus une chaîne plateforme). Le calcul est synchrone, sous verrou consultatif transactionnel par chaîne (`pg_advisory_xact_lock`) : sans verrou, deux écritures concurrentes prennent le même `prev_hash` et la chaîne fourche. Une commande `verify` parcourt la chaîne et détecte toute entrée modifiée ou supprimée.
