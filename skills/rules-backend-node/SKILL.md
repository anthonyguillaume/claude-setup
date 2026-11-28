---
name: rules-backend-node
description: "Règles de dev ai-team (back-end Node), préchargées par les agents. À charger avant d'écrire ou de relire du code Node.js / TypeScript du back-end."
---

# Règles back-end Node

Portée : tout le code Node.js / TypeScript du back-end. HTTP : `rules-api-rest`. Base de données : `rules-database-postgres`.

- **AT-BN-01** Le code est rangé par fonctionnalité (un dossier par cas d'usage), pas par type technique. Une fonctionnalité n'importe pas les éléments internes d'une autre.
- **AT-BN-02** Les erreurs métier sont des erreurs typées portant un `code` stable en anglais (`domaine.cas`), jamais renommé ni réutilisé pour un autre sens ; les exceptions brutes sont réservées à l'inattendu.
- **AT-BN-03** Les entrées sont validées aux frontières avec zod, avec des erreurs par champ. Les invariants restent aussi protégés dans le domaine.
- **AT-BN-04** Une abstraction (interface, port, classe de service) n'existe que pour une vraie variation d'implémentation ou une frontière d'infrastructure à isoler.
- **AT-BN-05** Async de bout en bout : les E/S acceptent un `AbortSignal` transmis jusqu'à l'appel final, et aucune promesse n'est laissée sans `await` ni gestion d'erreur.
- **AT-BN-06** Logs structurés (objet de champs, pas d'interpolation), messages en anglais. Aucune donnée personnelle (e-mail, nom, IP en clair, jeton) : on journalise des identifiants techniques.
- **AT-BN-07** TypeScript `strict`, pas de `any` (`unknown` puis restreindre), pas de `as` pour contourner le compilateur sans commentaire. Lockfile commité, licences permissives (MIT, Apache-2.0, BSD, MPL-2.0, ISC), version stable vérifiée dans le registre et jamais de mémoire. Pas de nouvelle librairie pour ce que fait une dizaine de lignes.
