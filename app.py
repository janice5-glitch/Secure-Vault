"""app.py - Flask web interface for the Secure Password Manager."""
import os
import secrets
import time

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)

from vault import Vault, VaultError, check_strength, generate_password

app = Flask(__name__)
app.secret_key = os.urandom(32)
VAULT_PATH = os.environ.get("VAULT_PATH", "vault.dat")
AUTO_LOCK_SECONDS = 300          # auto-lock after 5 minutes of inactivity
MAX_ATTEMPTS = 5                 # lock-out after 5 wrong master passwords
LOCKOUT_SECONDS = 60

vault = Vault(VAULT_PATH)        # decrypted data lives only in memory
state = {"token": None, "last": 0.0, "fails": 0, "locked_until": 0.0}


def unlocked():
    ok = (vault.key is not None and session.get("token") == state["token"]
          and time.time() - state["last"] < AUTO_LOCK_SECONDS)
    if ok:
        state["last"] = time.time()
    elif vault.key is not None:
        vault.lock()
    return ok


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapper(*a, **kw):
        if not unlocked():
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapper


@app.route("/", methods=["GET", "POST"])
def login():
    setup = not vault.exists()
    if request.method == "POST":
        pw = request.form.get("master", "")
        if setup:
            if pw != request.form.get("confirm", ""):
                flash("Passwords do not match.", "error")
            elif check_strength(pw)[0] < 2 or len(pw) < 8:
                flash("Master password is too weak (min 8 chars, mix types).", "error")
            else:
                vault.create(pw)
                flash("Vault created. Please log in.", "ok")
                vault.lock()
                return redirect(url_for("login"))
        else:
            if time.time() < state["locked_until"]:
                flash("Too many attempts. Try again later.", "error")
            else:
                try:
                    vault.unlock(pw)
                    state.update(token=secrets.token_hex(16), last=time.time(), fails=0)
                    session["token"] = state["token"]
                    return redirect(url_for("dashboard"))
                except VaultError as exc:
                    state["fails"] += 1
                    if state["fails"] >= MAX_ATTEMPTS:
                        state.update(locked_until=time.time() + LOCKOUT_SECONDS, fails=0)
                    flash(str(exc), "error")
    return render_template("login.html", setup=setup)


@app.route("/logout")
def logout():
    vault.lock()
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get("q", "")
    entries = vault.search(q)
    weak = sum(1 for e in vault.entries if check_strength(e["password"])[0] < 2)
    return render_template("dashboard.html", entries=entries, q=q,
                           total=len(vault.entries), weak=weak)


@app.route("/add", methods=["GET", "POST"])
@app.route("/edit/<entry_id>", methods=["GET", "POST"])
@login_required
def edit(entry_id=None):
    entry = vault.get(entry_id) if entry_id else None
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip()
                for k in ("site", "username", "password", "notes")}
        if not data["site"] or not data["password"]:
            flash("Site and password are required.", "error")
        else:
            if entry:
                vault.update(entry_id, **data)
            else:
                vault.add(**data)
            flash("Entry saved (encrypted).", "ok")
            return redirect(url_for("dashboard"))
    return render_template("edit.html", entry=entry)


@app.route("/delete/<entry_id>", methods=["POST"])
@login_required
def delete(entry_id):
    vault.delete(entry_id)
    flash("Entry deleted.", "ok")
    return redirect(url_for("dashboard"))


@app.route("/generator")
@login_required
def generator():
    return render_template("generator.html")


@app.route("/api/generate")
@login_required
def api_generate():
    pw = generate_password(int(request.args.get("length", 16)),
                           request.args.get("upper", "1") == "1",
                           request.args.get("digits", "1") == "1",
                           request.args.get("symbols", "1") == "1")
    score, label, entropy, tips = check_strength(pw)
    return jsonify(password=pw, score=score, label=label, entropy=entropy, tips=tips)


@app.route("/api/strength", methods=["POST"])
def api_strength():
    score, label, entropy, tips = check_strength(request.json.get("password", ""))
    return jsonify(score=score, label=label, entropy=entropy, tips=tips)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
