---
name: rules-i18n
description: "Règles de dev ai-team (internationalisation), préchargées par les agents. À charger avant d'écrire ou de relire du code qui produit du texte visible par un humain."
---

# Règles i18n

Portée : toute chaîne visible par un humain. Interface visuelle : `rules-ui`. Codes d'erreur côté serveur : `rules-api-rest`.

- **AT-I18N-01** Les langues du projet sont une variable de configuration, le français est la langue par défaut et de repli. La langue vient de la préférence de l'utilisateur, à défaut du navigateur, et `<html lang>` est mis à jour.
- **AT-I18N-02** Aucun texte visible en dur dans un composant : libellés, titres, `aria-label`, placeholders, textes alternatifs, messages d'erreur, titres de page. Lint bloquant (ex. plugin i18next) si l'outil est présent. Exception : identifiants techniques et noms propres de produit.
- **AT-I18N-03** Une clé par sens, clés hiérarchiques en `camelCase` suivant la fonctionnalité (`accounts.create.submit`), chaînes communes dans `shared/i18n`. Jamais de concaténation de morceaux de phrase (l'ordre des mots change selon la langue) : une phrase complète avec variable nommée, ex. `t('accounts.deleted', { name })`.
- **AT-I18N-04** Pluriels et genres en syntaxe ICU (`{count, plural, one {# compte} other {# comptes}}`). Dates, heures, nombres, devises et listes via `Intl.*` avec la langue active, jamais de format codé pour une seule langue. L'API envoie les dates en ISO 8601 UTC, converties à l'affichage (fuseau explicite si nécessaire). Pas de librairie de dates pour cela.
- **AT-I18N-05** Une erreur d'API est traduite depuis son `code` stable (clé `errors.<code>`, ex. `errors.account.email_taken`), jamais en affichant le `detail` brut de l'API. Un `code` sans traduction retombe sur `errors.unknown` avec le `traceId`, jamais sur une chaîne brute. Même principe pour les erreurs de champ (`validation.email_invalid`).
- **AT-I18N-06** Côté serveur : logs et codes d'erreur en anglais, pas de texte localisé. Seuls les e-mails, qu'aucun navigateur ne rend, sont traduits (modèles par langue selon la préférence de l'utilisateur).
- **AT-I18N-07** Un test de parité échoue si une clé existe dans une langue sans l'autre, si une variable `{x}` diffère entre langues, ou si une clé utilisée dans le code n'existe pas. Toute clé est ajoutée dans toutes les langues dans la même PR.
- **AT-I18N-08** Ajouter une langue = ajouter des fichiers et l'enregistrer, jamais de logique `lang === 'fr' ? ... : ...`. Aucune logique ne suppose un nombre de langues.
