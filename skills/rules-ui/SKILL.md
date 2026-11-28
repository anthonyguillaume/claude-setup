---
name: rules-ui
description: "Règles de dev ai-team (interface), préchargées par les agents. À charger avant d'écrire ou de relire du code d'interface (écrans, composants, styles)."
---

# Règles interface

Portée : tout écran et composant. Structure et code : `rules-frontend-react`. Textes : `rules-i18n`.

- **AT-UI-01** Couleurs, espacements, rayons, ombres, typographie et durées viennent des tokens (variables CSS). Aucune couleur, taille ou espacement en dur dans un composant (`bg-[#1e293b]`, `p-[13px]`, `style="padding: 13px"`) ; le lint le bloque s'il est présent.
- **AT-UI-02** Thèmes clair et sombre par `data-theme` sur `<html>` : les tokens sont redéfinis sous chaque thème, le thème est une préférence utilisateur, à défaut `prefers-color-scheme`. Un composant ne teste jamais le thème : il consomme des tokens sémantiques (`surface`, `fg`, `danger`), pas `gray-900`. Chaque écran est vérifié dans les deux thèmes.
- **AT-UI-03** Aucun texte sous 12 px (0,75 rem), légendes et badges compris ; le texte courant fait au moins 14 px. Unités `rem` pour respecter le zoom du navigateur.
- **AT-UI-04** WCAG 2.2 AA : contraste du texte au moins 4,5:1 (3:1 pour grand texte et composants d'interface), focus visible partout, navigation complète au clavier avec ordre de tabulation logique, rôles et libellés ARIA corrects. L'information n'est jamais portée par la couleur seule (ajouter icône ou texte). `prefers-reduced-motion` est respecté. Vérifier avec `jsx-a11y` et axe-core dans les E2E si les outils sont présents, et au clavier sur les nouveaux écrans.
- **AT-UI-05** Jamais d'impasse : chaque état d'erreur, vide ou refusé propose un message clair (traduit), une action possible (réessayer, retourner, contacter) et un chemin de retour. Liste vide : action de création ; 403 : page qui explique et mène ailleurs.
- **AT-UI-06** Libellé humain d'abord : pas de code d'erreur brut, d'identifiant technique ni de jargon au premier plan. Les identifiants techniques (id, `traceId`) restent accessibles en second plan et copiables, pour le support.
- **AT-UI-07** Tout composant qui charge des données gère chargement (squelette), vide, erreur et succès. Les actions destructrices demandent confirmation et sont réversibles quand c'est possible.
- **AT-UI-08** Quand le projet a des maquettes, ouvrir la maquette correspondante avant de construire un écran, en garder la structure (pixels remplacés par les tokens) et comparer la capture au résultat. Un écran sans maquette est validé par le propriétaire. Responsive vérifié à 360 et 1280 px.
- **AT-UI-09** Tout élément visuel utilisé deux fois vit dans une primitive partagée (`shared/ui`, variants par props typées). Ne pas recopier une longue chaîne de classes utilitaires dans plusieurs composants.
- **AT-UI-16** Cibles tactiles d'au moins 44 x 44 px sur mobile et 24 x 24 px sur ordinateur (ou l'espacement équivalent autour, exception de WCAG 2.5.8).
- **AT-UI-17** Une icône décorative est `aria-hidden` ; une icône seule dans un bouton ou un lien reçoit un libellé traduit. Un graphique a un titre, une description, une légende textuelle et la table de données équivalente, des textes d'axe d'au moins 12 px, et la couleur seule ne porte pas l'information. Pas d'emoji ni de police d'icônes : icônes SVG.
- **AT-UI-18** Menus et panneaux modaux : primitives accessibles du projet (ex. Radix UI) enveloppées dans `shared/ui` si le projet en a, sinon éléments natifs (`<dialog>`, `popover`, `<select>`, `<details>`) ; pour les composants sans équivalent natif (onglets, infobulle, menu), motif WAI-ARIA APG avec clavier complet. Les transitions durent 150 ms et sont coupées sous `prefers-reduced-motion`.
