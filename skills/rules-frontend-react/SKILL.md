---
name: rules-frontend-react
description: "Règles de dev ai-team (front-end React), préchargées par les agents. À charger avant d'écrire ou de relire du code React / TypeScript du front-end."
---

# Règles front-end React

Portée : tout le code React / TypeScript du front-end. Interface visuelle : `rules-ui`. Textes : `rules-i18n`. Appels API : `rules-api-rest`.

- **AT-FE-01** Le code suit `app/` (routeur, providers, coquille, routes), `features/<f>/{api,components,hooks,types}/`, `shared/{ui,lib,i18n,styles}/` et `api/` (client généré, jamais édité à la main).
- **AT-FE-02** Les imports vont dans le sens `shared` vers `features` vers `app` : un module n'importe que d'un niveau situé avant lui. Une fonctionnalité n'importe jamais une autre fonctionnalité ; le code partagé descend dans `shared/`. Règle de lint bloquante si l'outil est présent.
- **AT-FE-03** Un `index.ts` n'exporte que l'API publique d'une fonctionnalité (composants de page, hooks publics). Pas de barrel géant ni d'`export *` en cascade, qui casse le tree-shaking et masque les cycles.
- **AT-FE-04** Si le projet utilise TanStack Query, tout appel serveur passe par un hook `useQuery` / `useMutation` placé dans `features/<f>/api/`, jamais par un `fetch` ou le client généré appelé depuis un composant. Les clés viennent d'une fabrique par fonctionnalité ; après une mutation on invalide les clés concernées, sans recopier la donnée serveur dans un état local.
- **AT-FE-05** Le client d'API généré (`api/`) vient de l'OpenAPI : on le régénère, on ne le modifie jamais. La gate locale échoue si la régénération produit un diff. Les erreurs ProblemDetails se lisent par le champ `code`.
- **AT-FE-06** Pas d'état global sans besoin, par ordre de préférence : état local du composant, état dérivé, URL (filtres, pagination, onglet), contexte React étroit (thème, langue), bibliothèque d'état seulement si un besoin réel est démontré. Aucune donnée serveur dans un store global.
- **AT-FE-07** La validation côté client sert l'ergonomie ; le serveur fait foi. Les erreurs par champ du ProblemDetails sont rattachées à leurs champs. Aucune donnée sensible dans `localStorage` ni `sessionStorage`.
- **AT-FE-08** Les composants interactifs complexes (dialogue, menu, onglets, sélecteur, infobulle, popover) s'appuient sur les primitives accessibles du projet (ex. Radix UI) enveloppées dans `shared/ui` si le projet en a, sinon éléments natifs (`<dialog>`, `popover`, `<select>`, `<details>`) ; pour les composants sans équivalent natif (onglets, infobulle, menu), motif WAI-ARIA APG, dont le focus, le clavier et l'ARIA sont implémentés complètement comme l'APG les décrit ; stylés avec les tokens, sans réimplémenter à la main le focus, le clavier ni l'ARIA que la primitive choisie ou l'élément natif fournit déjà. `jsx-a11y` bloquant si l'outil est présent. Un élément cliquable est un `<button>` ou un `<a>`, jamais un `<div onClick>`.
- **AT-FE-09** TypeScript `strict`, pas de `any` (utiliser `unknown` puis restreindre), pas de `as` pour contourner le compilateur sans commentaire. Un composant fait une chose ; la logique réutilisable passe dans un hook. Props nommées par intention : un `variant`, pas de booléens en cascade (`isPrimary isLarge isGhost`).
- **AT-FE-10** `useEffect` ne sert ni à dériver un état, ni à charger des données, ni à réagir à une action utilisateur (utiliser le gestionnaire d'événement). `useMemo` et `useCallback` seulement après mesure.
- **AT-FE-11** Mobile d'abord : les styles de base ciblent le plus petit écran, on enrichit avec `min-width` (points de rupture Tailwind `sm` 640, `md` 768, `lg` 1024, `xl` 1280, `2xl` 1536 px). Chaque écran est vérifié à 360 px (sans défilement horizontal) et à 1280 px ; pas de largeur fixe de bureau.
- **AT-FE-12** Conventions TypeScript (Google TypeScript Style Guide) : `PascalCase` composants et types, `camelCase` variables et fonctions, `UPPER_SNAKE` constantes, exports nommés (export par défaut seulement pour les pages routées si l'outil l'exige), `const` par défaut, `import type` pour les types. Prettier et ESLint bloquants s'ils sont présents.
- **AT-FE-13** Pas de nouvelle librairie pour ce que fait une dizaine de lignes ou le navigateur (dates : `Intl`). Version stable vérifiée dans le registre en ligne, licence permissive, lockfile commité, budget de bundle surveillé à l'ajout.
- **AT-FE-15** Pas d'`enum` TypeScript : unions de littéraux de chaîne (`type Role = 'admin' | 'member'`), cohérentes avec le client généré.
- **AT-FE-16** Formulaires : messages d'erreur traduits, affichés sous le champ, reliés au contrôle par `aria-describedby` et `aria-invalid`. À la soumission, le focus va au premier champ en erreur (par défaut avec react-hook-form, si le projet l'utilise). Un champ obligatoire est signalé par du texte dans le libellé, jamais par la couleur seule.

## Variante Next.js

- **AT-FE-17** Avec Next.js (App Router) : composants serveur par défaut, `"use client"` seulement pour l'interaction. `error.tsx` et `not-found.tsx` par segment. Les filtres vivent dans l'URL (la navigation relance le composant serveur). Le thème n'est jamais lu par le serveur.
