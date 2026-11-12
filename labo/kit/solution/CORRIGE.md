# Corrigé et notes pour l'enseignant

## Déroulé conseillé

| Partie | Durée | Mode |
|---|---|---|
| 0 : démarrage | 5 min | individuel, à faire avant la séance si possible (téléchargement des images) |
| 1 : client OIDC avec les comptes Keycloak | 25 min | binômes |
| 2 : fédération GitHub | 15 min | binômes (un compte GitHub par binôme suffit) |
| 3 : rôles et autorisation | 15 min | binômes |
| 4 : facultatif | à la maison | individuel |

Le realm complet (sans les secrets GitHub) est dans `caisse-realm.json`. Comptes : `mdupont` / `Marie2026!`
(rôle gestionnaire-prestations), `pmartin` / `Paul2026!` (sans le rôle). Secret du client : `secret-du-labo-a-changer`.
Le fournisseur d'identité GitHub y est déclaré mais désactivé : il faut y mettre le Client ID et le secret
d'une OAuth App GitHub, puis l'activer (Identity providers → GitHub → Enabled).

Le kit a été testé avec Keycloak 26.7.2 : flux complet (PKCE, nonce, vérification du jeton d'identité,
rôles dans le jeton d'identité, userinfo, déconnexion globale, 403 sans rôle), import du realm, bouton GitHub.

## Pièges rencontrés en classe

- **Deux adresses pour Keycloak.** Le navigateur va sur `localhost:8080`, le conteneur de l'application sur
  `keycloak:8080`. `KC_HOSTNAME=http://localhost:8080` fixe l'émetteur (`iss`) et l'adresse d'autorisation ;
  `KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true` fait que les adresses token / jwks / userinfo sont renvoyées avec le nom
  par lequel l'application appelle. Sans cela : « iss mismatch » ou « connection refused » selon le cas.
- **Attributs non gérés.** Depuis Keycloak 24, le profil utilisateur est déclaratif : sans « Unmanaged attributes :
  Enabled », les attributs libres (service, numeroRH, source) sont refusés et le mapper « Hardcoded attribute » du
  fournisseur GitHub ne produit rien.
- **Rôles absents du jeton d'identité.** Par défaut le mapper « realm roles » n'écrit que dans le jeton d'accès.
  C'est voulu dans le labo : l'étudiant doit ajouter le mapper. Ne pas « corriger » avant.
- **PKCE a changé de place.** Dans Keycloak 26.7 le réglage est dans Settings → Capability config (« Require PKCE »,
  « PKCE Method »), plus dans l'onglet Advanced. Les tutoriels en ligne décrivent presque tous l'ancien emplacement.
- **Oubli de redémarrer l'application** après modification de `.env`.
- **Port 5000 / 8000 occupé** sur macOS (AirPlay) : l'application est sur 8000 pour cette raison ; changer dans le compose si besoin.
- **GitHub : adresse de retour.** Elle doit être exactement `http://localhost:8080/realms/caisse/broker/github/endpoint`.
  GitHub accepte `http://localhost` sans TLS, c'est un cas prévu par leur documentation.
- **Réseau d'entreprise** : les images viennent de quay.io et de Docker Hub ; prévoir un téléchargement avant la séance.

## Réponses

**Q0.** Le navigateur de l'utilisateur et le serveur de l'application ne sont pas au même endroit : le premier voit Keycloak
sur `localhost:8080`, le second sur `keycloak:8080` (réseau Docker). `iss` vaut toujours `http://localhost:8080/realms/caisse`
(l'adresse publique, fixée par `KC_HOSTNAME`), sinon l'application refuserait le jeton (émetteur inattendu).

**Q1.** Le mot de passe n'existe que dans Keycloak, sous forme d'empreinte (Argon2id par défaut dans Keycloak 26, avec sel).
Lors d'une connexion, seul le navigateur et Keycloak le voient. L'application ne le voit jamais : elle reçoit un code, puis des jetons.

**Q2.** « Direct access grants » (ROPC) ferait transiter le mot de passe par l'application, ce qui annule tout l'intérêt de la
fédération et est abandonné par OAuth 2.1. Une URI de redirection avec joker permet à un attaquant de faire livrer le code
d'autorisation sur une adresse qu'il contrôle (slide « Ce qui a été abandonné »), d'où la comparaison exacte.

**Q3.** `aud` = `app-prestations` : le jeton d'identité est destiné à l'application, qui doit vérifier qu'elle en est bien le
destinataire. Le jeton d'accès est destiné aux API (ici `userinfo`) ; l'application ne devrait pas s'en servir pour identifier
l'utilisateur.

**Q4.** 300 secondes (5 minutes, réglage du realm). Oui : un jeton signé reste valable jusqu'à son expiration ; désactiver Marie
ne révoque pas la session locale de l'application ni le jeton déjà émis. C'est pour cela que les durées sont courtes et que les
API sensibles vérifient côté serveur (introspection) ; voir aussi le départ de Marie, chapitre 3.

**Q5.** `acr` = `1` : niveau d'authentification « 1 », c'est-à-dire un facteur (mot de passe). Keycloak n'émet `amr` que si on
configure des mappers ; les niveaux d'`acr` se définissent par « Authentication → Flows → Level of Authentication ».

**Q6.** C'est l'équivalent de la « Valid redirect URI » du client app-prestations. Ici Keycloak est le client OAuth et GitHub le
serveur d'autorisation : Keycloak joue les deux rôles à la fois, fournisseur d'identité pour l'application et client pour GitHub.

**Q7.** Non et non. Le mot de passe GitHub ne circule qu'entre le navigateur et GitHub. GitHub renvoie un code à Keycloak,
qui l'échange contre un jeton d'accès GitHub et lit le profil (API `/user`). Keycloak crée un utilisateur local lié
(« Identity provider links ») et émet ses propres jetons pour l'application, signés avec ses propres clés. Quatre acteurs :
utilisateur (navigateur), application, Keycloak, GitHub. Ce qui ne circule jamais : le mot de passe au-delà de l'IdP concerné,
le secret client (sauf entre application et Keycloak sur le canal arrière, et entre Keycloak et GitHub).

**Q8.** Personne, par défaut. La fédération sait créer un compte à la première connexion, jamais le fermer : c'est le problème
des comptes orphelins (chapitre 3, cycle de vie, et chapitre 7, SCIM / la règle des deux canaux). Il faut une source de référence
pour les externes (date de fin) et un processus qui désactive le compte Keycloak.

**Q9.** Avec « Trust email », Keycloak croirait l'adresse déclarée par GitHub sans vérification ; le flux de premier
login proposerait alors de **lier** le compte GitHub au compte existant de Marie (même e-mail), et l'attaquant pourrait se
connecter à l'application en tant que Marie. C'est une variante de prise de contrôle de compte par fédération ; on ne fait confiance
à l'e-mail que si le fournisseur le vérifie, et on garde la liaison manuelle avec réauthentification.

**Q10.** Keycloak a répondu « qui est-ce ? » (authentification) et a transporté un attribut (le rôle). L'application a décidé
seule « a-t-elle le droit ? » (autorisation) en lisant le claim et en appliquant sa règle. Deux décisions, deux systèmes
(chapitre 1, les quatre questions).

**Q11.** Dans Keycloak (ou, en vraie vie, dans l'outil IGA qui alimente Keycloak). Marie garde l'accès jusqu'à l'expiration de
son jeton d'identité et de sa session dans l'application : l'application ne redemande pas à Keycloak à chaque page. Pour un
retrait immédiat : révoquer la session (Keycloak → Sessions) et faire vérifier la session côté application à chaque requête sensible.

**Q12.** Le jeton d'accès est destiné à l'API, pas à l'application cliente ; son format n'est pas garanti (opaque chez d'autres
fournisseurs), son contenu peut changer sans que l'application soit prévenue, et c'est la confusion qui mène à « OAuth n'est pas
un protocole d'authentification » (slide « OAuth 2.0 : le malentendu de départ »).

## Grille d'évaluation suggérée (sur 12)

- Questions 0 à 5 (partie 1) : 4 points, dont 1 pour la distinction jeton d'identité / jeton d'accès.
- Questions 6 à 9 (fédération) : 4 points, dont 2 pour le schéma des acteurs et ce qui ne circule pas.
- Questions 10 à 12 (autorisation) : 3 points.
- Qualité du schéma et clarté : 1 point.
