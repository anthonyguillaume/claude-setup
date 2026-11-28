---
name: rules-backend-dotnet
description: "Règles de dev ai-team (back-end .NET), préchargées par les agents. À charger avant d'écrire ou de relire du code C# / ASP.NET Core du back-end."
---

# Règles back-end .NET

Portée : tout le code C# du back-end (domaine, application, infrastructure, API). HTTP : `rules-api-rest`. Base de données : `rules-database-postgres`.

- **AT-BE-02** Le code d'application est rangé par fonctionnalité, un dossier par cas d'usage (`<Feature>/<UseCase>/` avec commande ou requête, handler, validateur), jamais par type technique. Une fonctionnalité n'importe pas les types internes d'une autre.
- **AT-BE-03** Handlers, validateurs et comportements du pipeline sont `internal sealed`. Seuls les types utilisés par l'API (commande, requête, DTO de réponse, `Result<T>`, `Error`) sont `public` ; les tests accèdent aux internes via `InternalsVisibleTo`.
- **AT-BE-05** Un handler renvoie `Result<T>` : succès, ou `Error` avec un `Code` stable en anglais (`domaine.cas`, ex. `account.email_taken`). Pas d'exception pour un cas métier attendu (introuvable, conflit, règle violée) ; les exceptions sont réservées à l'inattendu (panne, bug) et deviennent un 500 sans détail interne.
- **AT-BE-06** Un `Code` d'erreur est un contrat : jamais renommé ni réutilisé pour un autre sens, car le front le traduit. Tout nouveau code ajoute ses traductions dans la même PR.
- **AT-BE-07** Les commandes sont validées (FluentValidation) dans le comportement de pipeline de validation, avant le handler, avec des erreurs par champ. Les invariants du domaine sont aussi protégés dans les entités, pas seulement dans le validateur.
- **AT-BE-10** Une interface n'existe que s'il y a une vraie variation d'implémentation ou une frontière d'infrastructure à isoler (e-mail, stockage, horloge de test). Une interface à une seule implémentation sans frontière est du bruit : ne pas la créer.
- **AT-BE-11** Le temps passe par `TimeProvider` injecté (pas d'interface maison), jamais `DateTime.Now`, `DateTime.UtcNow` ni `DateTimeOffset.UtcNow` ; les tests utilisent `FakeTimeProvider`. Toutes les dates sont en UTC.
- **AT-BE-12** Toute méthode qui fait des E/S est `async`, retourne `Task` ou `ValueTask` et accepte un `CancellationToken` transmis jusqu'à l'appel final. Jamais `.Result`, `.Wait()`, `GetAwaiter().GetResult()` ni `async void` (hors gestionnaire d'événement).
- **AT-BE-13** Les logs utilisent `[LoggerMessage]` (pas d'interpolation, paramètres nommés), messages et codes en anglais. Aucune donnée personnelle (e-mail, nom, IP en clair, jeton) : on journalise des identifiants techniques.
- **AT-BE-14** Compilation stricte : `TreatWarningsAsErrors`, `Nullable` activé, analyseurs `latest-recommended`, versions centralisées (Central Package Management), lockfiles NuGet. Un `#pragma warning disable` ou un `!` est justifié par un commentaire. Version d'un paquet vérifiée en ligne à l'ajout, jamais de mémoire ; licences MIT, Apache-2.0, BSD, MPL-2.0, ISC ou PostgreSQL License seulement (pas de GPL, AGPL, BUSL ni de « gratuit sous seuil »).
- **AT-BE-15** Conventions C# Microsoft : PascalCase, `_camelCase` pour les champs privés, espaces de noms à portée de fichier, `var` quand le type est évident, membres d'une ligne en expression, `record` pour messages et DTO immuables. `dotnet format --verify-no-changes` doit passer si l'outil est présent.
- **AT-BE-16** Code en anglais. Un commentaire explique le pourquoi, jamais le quoi, dans la langue du projet. Pas de code commenté, pas de `TODO` sans dette notée.
- **AT-BE-17** Option si le projet a déjà un Mediator : Clean Architecture (Api, Application, Domain, Infrastructure), dépendances `Api -> Application -> Domain` et `Infrastructure -> Application`, Domain sans paquet de framework. Endpoints fins (requête vers commande, envoi au Mediator, `Result<T>` vers réponse HTTP, sans logique métier). Pipeline ordonné : validation, transaction, handler, chacun ne faisant qu'une chose. Les handlers utilisent le `DbContext` via une interface étroite des `DbSet` utiles ; ni `IRepository<T>` ni `IUnitOfWork`.
- **AT-BE-18** Option par défaut quand le projet n'a pas de Mediator : endpoints par fonctionnalité (`Features/<Feature>/<Feature>Endpoints.cs` avec une méthode `Map(IEndpointRouteBuilder)`) et handlers en méthodes statiques, sans Mediator ni CQRS.

## SOLID

- S, responsabilité unique : un handler = un cas d'usage ; un comportement de pipeline = une préoccupation transverse.
- O, ouvert/fermé : on ajoute un cas d'usage en ajoutant un dossier, pas en modifiant un `switch` central.
- L, substitution : toute implémentation d'un port respecte son contrat (mêmes erreurs, mêmes annulations).
- I, ségrégation : l'interface de contexte expose les `DbSet` utiles, pas tout le `DbContext` ; les ports sont petits.
- D, inversion : l'application déclare les ports, l'infrastructure les implémente.
- À éviter : un « service » fourre-tout (`Create`, `Delete`, `SendReset`, `Export`) qui viole S et O.
