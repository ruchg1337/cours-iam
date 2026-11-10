# -*- coding: utf-8 -*-
"""
Application cliente OIDC du labo IAM.

Rôle pédagogique : montrer ce que l'application reçoit vraiment de Keycloak
(jeton d'identité, jeton d'accès, claims) et où se prennent les décisions
d'authentification (chez l'IdP) et d'autorisation (ici).

Flux utilisé : code d'autorisation + PKCE (le seul à retenir, chapitre 7).
"""
import base64
import json
import os
import time

import requests
from authlib.integrations.flask_client import OAuth
from flask import Flask, abort, redirect, render_template, session, url_for

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "http://localhost:8080/realms/caisse")
OIDC_INTERNAL_BASE = os.environ.get("OIDC_INTERNAL_BASE", OIDC_ISSUER)
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "app-prestations")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
ROLE_REQUIS = os.environ.get("ROLE_REQUIS", "gestionnaire-prestations")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "changez-moi")

oauth = OAuth(app)
oauth.register(
    name="keycloak",
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
    # La découverte se fait par le réseau interne ; grâce à KC_HOSTNAME_BACKCHANNEL_DYNAMIC,
    # Keycloak y renvoie l'adresse interne pour token/jwks et l'adresse publique pour l'autorisation.
    server_metadata_url=f"{OIDC_INTERNAL_BASE}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email",
        "code_challenge_method": "S256",   # PKCE
    },
)


def decode_jwt_unverified(token):
    """Décode un JWT sans vérifier la signature : uniquement pour l'affichage pédagogique.
    (La vérification réelle du jeton d'identité est faite par Authlib dans authorize_access_token.)"""
    if not token or token.count(".") != 2:
        return None, None
    header, payload, _sig = token.split(".")

    def b64(part):
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part))

    try:
        return b64(header), b64(payload)
    except Exception:
        return None, None


@app.context_processor
def inject_globals():
    return {"issuer": OIDC_ISSUER, "client_id": OIDC_CLIENT_ID, "role_requis": ROLE_REQUIS,
            "user": session.get("userinfo")}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    redirect_uri = f"{APP_BASE_URL}/callback"
    return oauth.keycloak.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    # Échange du code contre les jetons (étape 4 du flux), avec vérification du jeton d'identité :
    # signature (clé publique de l'IdP), iss, aud, exp, nonce.
    token = oauth.keycloak.authorize_access_token()
    session["tokens"] = {
        "id_token": token.get("id_token"),
        "access_token": token.get("access_token"),
        "refresh_token": token.get("refresh_token"),
        "expires_at": token.get("expires_at"),
    }
    session["userinfo"] = token.get("userinfo") or {}
    return redirect(url_for("profil"))


def _require_login():
    if "tokens" not in session:
        abort(401)


@app.errorhandler(401)
def not_logged_in(_e):
    return render_template("401.html"), 401


@app.errorhandler(403)
def forbidden(_e):
    return render_template("403.html"), 403


@app.route("/profil")
def profil():
    _require_login()
    t = session["tokens"]
    id_header, id_payload = decode_jwt_unverified(t.get("id_token"))
    at_header, at_payload = decode_jwt_unverified(t.get("access_token"))
    now = int(time.time())
    return render_template(
        "profil.html",
        id_token=t.get("id_token"), id_header=id_header, id_payload=id_payload,
        access_token=t.get("access_token"), at_header=at_header, at_payload=at_payload,
        now=now,
        pretty=lambda d: json.dumps(d, indent=2, ensure_ascii=False),
    )


def _roles_from_id_token():
    _h, payload = decode_jwt_unverified(session["tokens"].get("id_token"))
    if not payload:
        return []
    return (payload.get("realm_access") or {}).get("roles", [])


@app.route("/rentes")
def rentes():
    """Page réservée : l'AUTORISATION se décide ici, dans l'application, à partir des rôles reçus."""
    _require_login()
    roles = _roles_from_id_token()
    if ROLE_REQUIS not in roles:
        abort(403)
    return render_template("rentes.html", roles=roles)


@app.route("/userinfo")
def userinfo():
    """Appel du point d'information (userinfo) avec le jeton d'accès : le jeton d'accès sert à appeler une API."""
    _require_login()
    meta = oauth.keycloak.load_server_metadata()
    r = requests.get(meta["userinfo_endpoint"],
                     headers={"Authorization": f"Bearer {session['tokens']['access_token']}"}, timeout=10)
    return render_template("userinfo.html", status=r.status_code,
                           body=json.dumps(r.json() if r.ok else {"erreur": r.text}, indent=2, ensure_ascii=False))


@app.route("/logout")
def logout():
    """Déconnexion initiée par l'application (RP-initiated logout) : on ferme la session locale ET celle de l'IdP."""
    id_token = (session.get("tokens") or {}).get("id_token")
    session.clear()
    meta = oauth.keycloak.load_server_metadata()
    end_session = meta.get("end_session_endpoint")
    if end_session and id_token:
        # L'adresse publique de Keycloak est nécessaire ici (c'est le navigateur qui y va)
        end_session = end_session.replace(OIDC_INTERNAL_BASE, OIDC_ISSUER)
        return redirect(f"{end_session}?id_token_hint={id_token}&post_logout_redirect_uri={APP_BASE_URL}/")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
