from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

# --------------------------
# Fonctions d'authentification
# --------------------------
def est_authentifie():
    return session.get('authentifie')

def require_user_auth():
    """Protection Basic Auth user/12345 (ancienne fonction)"""
    USER_LOGIN = "user"
    USER_PASSWORD = "12345"
    auth = request.authorization
    if not auth or not (auth.username == USER_LOGIN and auth.password == USER_PASSWORD):
        return Response(
            "Accès refusé (auth user requise)",
            401,
            {"WWW-Authenticate": 'Basic realm="User Area"'}
        )
    return None

# --------------------------
# Routes de base
# --------------------------
@app.route('/')
def hello_world():
    return render_template('hello.html')

# --------------------------
# Authentification avec rôle
# --------------------------
@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['authentifie'] = True
            session['username'] = user[1]
            session['role'] = user[2]
            session['user_id'] = user[0]
            return redirect(url_for('liste_livres'))
        else:
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)

# --------------------------
# Gestion des livres
# --------------------------
@app.route('/livres/')
def liste_livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livres')
    livres = cursor.fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/ajouter', methods=['GET', 'POST'])
def ajouter_livre():
    if not est_authentifie() or session.get('role') != 'admin':
        return "<h3>Accès refusé : admin uniquement</h3>"

    if request.method == 'POST':
        titre = request.form['titre']
        auteur = request.form['auteur']
        stock = int(request.form['stock'])
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)', (titre, auteur, stock))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))

    return render_template('ajouter_livre.html')

@app.route('/livres/emprunter/<int:livre_id>', methods=['POST'])
def emprunter_livre(livre_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))

    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT stock FROM livres WHERE id = ?', (livre_id,))
    livre = cursor.fetchone()
    if not livre or livre[0] <= 0:
        conn.close()
        return "<h3>Livre non disponible</h3>"

    cursor.execute('INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)', (user_id, livre_id))
    cursor.execute('UPDATE livres SET stock = stock - 1 WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

@app.route('/livres/retourner/<int:livre_id>', methods=['POST'])
def retourner_livre(livre_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))

    user_id = session.get('user_id')
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM emprunts
        WHERE user_id = ? AND livre_id = ? AND date_retour IS NULL
    """, (user_id, livre_id))
    emprunt = cursor.fetchone()

    if not emprunt:
        conn.close()
        return "<h3>Erreur : vous n'avez pas emprunté ce livre ou il est déjà retourné.</h3>"

    cursor.execute("""
        UPDATE emprunts
        SET date_retour = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (emprunt[0],))

    cursor.execute("""
        UPDATE livres
        SET stock = stock + 1
        WHERE id = ?
    """, (livre_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("mes_emprunts"))

@app.route('/mes_emprunts/')
def mes_emprunts():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT livres.id, livres.titre, emprunts.date_emprunt, emprunts.date_retour
        FROM emprunts
        JOIN livres ON emprunts.livre_id = livres.id
        WHERE emprunts.user_id = ?
    """, (user_id,))
    emprunts = cursor.fetchall()
    conn.close()
    return render_template('emprunts.html', emprunts=emprunts)

@app.route('/livres/recherche', methods=['GET','POST'])
def recherche_livres():
    titre = request.form.get('titre') if request.method == 'POST' else request.args.get('titre')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livres WHERE titre LIKE ?', (f"%{titre}%",))
    livres = cursor.fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/supprimer/<int:livre_id>', methods=['POST'])
def supprimer_livre(livre_id):
    if session.get('role') != 'admin':
        return "<h3>Accès refusé : admin uniquement</h3>"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM livres WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

# --------------------------
# Lancer l'application
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
