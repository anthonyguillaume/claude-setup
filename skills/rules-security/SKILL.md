---
name: rules-security
description: "Règles de dev ai-team (sécurité), préchargées par les agents. À charger avant d'écrire ou de relire du code d'authentification, d'autorisation, d'entrées utilisateur, de secrets ou de CI."
---

# Règles sécurité

Cible : OWASP ASVS 5.0 niveau 2 et API Security Top 10. Chaque règle est cochée en revue.

- **AT-SEC-01** Cookie de session `HttpOnly`, `Secure`, `SameSite=Lax`, host-only avec préfixe `__Host-`. Protection antiforgery sur toute écriture (POST, PUT, PATCH, DELETE), anonyme comprise. Les endpoints JSON répondent 415 aux autres types de contenu.
- **AT-SEC-02** Mots de passe : hachage lent (PBKDF2 ou mieux), 12 caractères minimum, refus des mots de passe courants, verrouillage après 5 échecs pendant 15 min. Réinitialisation par lien à usage unique valable 1 h. Jamais de mot de passe dans un log ou une réponse.
- **AT-SEC-03** Retirer, désactiver ou rétrograder le dernier administrateur actif est refusé, sous verrou transactionnel (verrou consultatif ou `SELECT ... FOR UPDATE`) : sans lui, deux requêtes concurrentes passent chacune la vérification.
- **AT-SEC-04** Rien de sensible dans le stockage du navigateur (jeton, mot de passe, donnée personnelle) hors cookie. Aucun secret dans le bundle front : les variables exposées au front sont publiques.
- **AT-SEC-05** Pas d'injection : SQL toujours paramétré (jamais concaténé), pas de HTML brut sans assainissement revu, aucune commande shell construite depuis une entrée utilisateur, URLs sortantes validées par liste blanche (SSRF).
- **AT-SEC-06** Limitation de débit stricte sur l'authentification (connexion, réinitialisation) et globale sur l'API. Dépassement : 429 avec `Retry-After`.
- **AT-SEC-07** Anti-énumération : connexion et réinitialisation donnent la même réponse (message, code, durée approximative) que le compte existe ou non. Une ressource inexistante ou hors périmètre répond 404.
- **AT-SEC-08** Refus par défaut : chaque endpoint déclare explicitement son accès, et un test échoue sur un endpoint sans marqueur. Chaque accès par identifiant contrôle l'appartenance de l'objet (BOLA). Les réponses passent par des DTO, jamais l'entité. Les droits sont relus à chaque requête, jamais stockés dans le cookie.
- **AT-SEC-09** En-têtes : CSP stricte (ni `unsafe-inline` ni `unsafe-eval`), HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors 'none'`. CORS fermé par défaut (même origine) ; toute ouverture est une exception revue.
- **AT-SEC-10** Secrets hors du code : variables d'environnement, `.env` hors git, `.env.example` sans valeur réelle. Les agents ne lisent jamais `.env`. Un secret divulgué est compromis : rotation immédiate. Si gitleaks est présent, il tourne en hook de commit et en CI.
- **AT-SEC-11** Chaîne d'approvisionnement : versions épinglées, lockfiles commités, licences permissives seulement. Scans des dépendances, des images et du code si les outils sont présents.
- **AT-SEC-12** Aucune donnée personnelle dans les logs (ni e-mail, nom, mot de passe, jeton, cookie, IP complète) : des identifiants techniques seulement.
- **AT-SEC-13** Chemins sensibles (authentification, session, autorisation, isolation des données, cryptographie, secrets, upload, CI) : passe de l'agent `security` avec `owasp-security` puis `differential-review`, en plus de la revue. Jamais délégué à DeepSeek.
- **AT-SEC-14** Fichiers envoyés : type vérifié par signature (pas par l'en-tête seul), taille maximale, `X-Content-Type-Options: nosniff` au service.
- **AT-SEC-15** Un jeton machine est comparé en temps constant. L'application refuse de démarrer si un secret a encore sa valeur d'exemple.

## Checklist par changement

À cocher dans la PR, le reviewer la revérifie :

- [ ] Chaque nouvel endpoint a une politique d'autorisation et un contrôle d'objet (AT-SEC-08).
- [ ] Entrées validées côté serveur, SQL paramétré (AT-SEC-05).
- [ ] Aucune donnée personnelle dans les logs, aucun secret versionné (AT-SEC-10, AT-SEC-12).
- [ ] Réponses par DTO, aucune propriété interne, erreurs sans fuite d'information.
- [ ] Nouvelle dépendance : version vérifiée en ligne, licence, CVE connues (AT-SEC-11).
- [ ] Nouvelle donnée personnelle : registre de données du projet à jour.

## Correspondance OWASP

| Exigence | ASVS 5.0 (niveau 2) | API Top 10 2023 | Règles |
|---|---|---|---|
| Session et cookie | V7 Sessions | API2 | AT-SEC-01 |
| Mots de passe, anti-énumération | V6 Authentification | API2 | AT-SEC-02, AT-SEC-07 |
| Autorisation, objets, propriétés | V8 Autorisation | API1, API3, API5 | AT-SEC-08 |
| Validation, injection | V1 Encodage, V2 Validation | hors Top 10 API | AT-SEC-05 |
| Débit | V2 Anti-automatisation | API4 | AT-SEC-06 |
| En-têtes, configuration | V3 Frontend web, V13 Configuration | API8 | AT-SEC-09 |
| Secrets, logs | V13, V16 Journalisation | API8 | AT-SEC-10, AT-SEC-12 |
| Chaîne d'approvisionnement | V15 Code sécurisé | API10 | AT-SEC-11 |
