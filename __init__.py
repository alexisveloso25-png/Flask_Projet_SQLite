from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_flask_bibliotheque"

DB_PATH = "database.db"

# ---------------------------
# OUTILS
# ---------------------------

def get_db():
    return sqlite3.connect(DB_PATH)

def est_authentifie():
    return "user_id" in session

def est_admin():
    return session.get("role") == "admin"

# ---------------------------
# PAGE ACCUEIL
# ---------------------------

@app.route("/")
def accueil():
    return render_template("hello.html")

# ---------------------------
# AUTHENTIFICATION
# ---------------------------

@app.route("/authentification", methods=["GET", "POST"])
def authentification():
    error = False

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[1]
            return redirect(url_for("liste_livres"))
        else:
            error = True

    return render_template("formulaire_authentification.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("authentification"))

# ---------------------------
# LIVRES
# ---------------------------

@app.route("/livres/")
def liste_livres():
    if not est_authentifie():
        return redirect(url_for("authentification"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livres")
    livres = cursor.fetchall()
    conn.close()

    return render_template("livres.html", livres=livres)

@app.route("/livres/ajouter", methods=["GET", "POST"])
def ajouter_livre():
    if not est_authentifie() or not est_admin():
        return "<h3>Accès refusé (admin uniquement)</h3>"

    if request.method == "POST":
        titre = request.form["titre"]
        auteur = request.form["auteur"]
        stock = int(request.form["stock"])

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)",
            (titre, auteur, stock)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("liste_livres"))

    return render_template("ajouter_livre.html")

@app.route("/livres/supprimer/<int:livre_id>", methods=["POST"])
def supprimer_livre(livre_id):
    if not est_admin():
        return "<h3>Accès refusé</h3>"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM livres WHERE id = ?", (livre_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("liste_livres"))

# ---------------------------
# EMPRUNTS
# ---------------------------

@app.route("/livres/emprunter/<int:livre_id>", methods=["POST"])
def emprunter_livre(livre_id):
    if not est_authentifie():
        return redirect(url_for("authentification"))

    conn = get_db()
    cursor = conn.cursor()

    # Vérifier stock
    cursor.execute("SELECT stock FROM livres WHERE id = ?", (livre_id,))
    livre = cursor.fetchone()

    if not livre or livre[0] <= 0:
        conn.close()
        return "<h3>Livre indisponible</h3>"

    # Emprunt
    cursor.execute(
        "INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)",
        (session["user_id"], livre_id)
    )
    cursor.execute(
        "UPDATE livres SET stock = stock - 1 WHERE id = ?",
        (livre_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("liste_livres"))

@app.route("/mes_emprunts/")
def mes_emprunts():
    if not est_authentifie():
        return redirect(url_for("authentification"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT livres.titre, emprunts.date_emprunt, emprunts.date_retour
        FROM emprunts
        JOIN livres ON emprunts.livre_id = livres.id
        WHERE emprunts.user_id = ?
    """, (session["user_id"],))

    emprunts = cursor.fetchall()
    conn.close()

    return render_template("emprunts.html", emprunts=emprunts)

# ---------------------------
# RECHERCHE LIVRES
# ---------------------------

@app.route("/livres/recherche", methods=["GET", "POST"])
def recherche_livres():
    if not est_authentifie():
        return redirect(url_for("authentification"))

    titre = request.form.get("titre", "")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM livres WHERE titre LIKE ?",
        (f"%{titre}%",)
    )
    livres = cursor.fetchall()
    conn.close()

    return render_template("livres.html", livres=livres)

# ---------------------------
# LANCEMENT LOCAL
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
