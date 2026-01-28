from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key_super_secure"


def est_authentifie():
    return session.get("authentifie") is True



@app.route("/")
def accueil():
    return render_template("hello.html")



@app.route("/authentification", methods=["GET", "POST"])
def authentification():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["authentifie"] = True
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[2]
            return redirect(url_for("liste_livres"))

        return render_template("formulaire_authentification.html", error=True)

    return render_template("formulaire_authentification.html", error=False)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("authentification"))



@app.route("/livres/")
def liste_livres():
    if not est_authentifie():
        return redirect(url_for("authentification"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livres")
    livres = cursor.fetchall()
    conn.close()

    return render_template("livres.html", livres=livres)


@app.route("/livres/ajouter", methods=["GET", "POST"])
def ajouter_livre():
    if session.get("role") != "admin":
        return "<h3>Accès refusé (admin uniquement)</h3>"

    if request.method == "POST":
        titre = request.form["titre"]
        auteur = request.form["auteur"]
        stock = int(request.form["stock"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)",
            (titre, auteur, stock),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("liste_livres"))

    return render_template("ajouter_livre.html")


@app.route("/livres/supprimer/<int:livre_id>", methods=["POST"])
def supprimer_livre(livre_id):
    if session.get("role") != "admin":
        return "<h3>Accès refusé</h3>"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM livres WHERE id=?", (livre_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("liste_livres"))


@app.route("/livres/recherche", methods=["GET", "POST"])
def recherche_livres():
    titre = request.form.get("titre", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM livres WHERE titre LIKE ? AND stock > 0",
        (f"%{titre}%",),
    )
    livres = cursor.fetchall()
    conn.close()

    return render_template("livres.html", livres=livres)



@app.route("/livres/emprunter/<int:livre_id>", methods=["POST"])
def emprunter_livre(livre_id):
    if not est_authentifie():
        return redirect(url_for("authentification"))

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT stock FROM livres WHERE id=?", (livre_id,))
    stock = cursor.fetchone()

    if not stock or stock[0] <= 0:
        conn.close()
        return "<h3>Livre non disponible</h3>"

    cursor.execute(
        "INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)",
        (user_id, livre_id),
    )
    cursor.execute(
        "UPDATE livres SET stock = stock - 1 WHERE id=?", (livre_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("liste_livres"))


@app.route("/mes_emprunts/")
def mes_emprunts():
    if not est_authentifie():
        return redirect(url_for("authentification"))

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT livres.titre, emprunts.date_emprunt, emprunts.date_retour
        FROM emprunts
        JOIN livres ON livres.id = emprunts.livre_id
        WHERE emprunts.user_id = ?
    """, (user_id,))
    emprunts = cursor.fetchall()
    conn.close()

    return render_template("emprunts.html", emprunts=emprunts)



@app.route("/admin/users")
def liste_users():
    if session.get("role") != "admin":
        return "<h3>Accès refusé</h3>"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("users.html", users=users)


@app.route("/admin/users/supprimer/<int:user_id>", methods=["POST"])
def supprimer_user(user_id):
    if session.get("role") != "admin":
        return "<h3>Accès refusé</h3>"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("liste_users"))


if __name__ == "__main__":
    app.run(debug=True)
