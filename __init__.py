from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# --- CONFIGURATION BASE DE DONNÉES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise les tables indispensables si elles n'existent pas"""
    conn = get_db()
    # Table des Tâches (Objectifs) - CRITIQUE POUR TES ERREURS
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            is_completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --------------------------
# Fonctions d'authentification
# --------------------------

def est_authentifie():
    return session.get('authentifie')

def require_user_auth():
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

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", 
                            (username, password)).fetchone()
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
# Gestion des livres (Toutes tes routes)
# --------------------------

@app.route('/livres/')
def liste_livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db()
    livres = conn.execute('SELECT * FROM livres').fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/ajouter', methods=['GET', 'POST'])
def ajouter_livre():
    if not est_authentifie() or session.get('role') != 'admin':
        return "<h3>Accès refusé : admin uniquement</h3>"
    if request.method == 'POST':
        conn = get_db()
        conn.execute('INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)', 
                     (request.form['titre'], request.form['auteur'], int(request.form['stock'])))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')

@app.route('/livres/emprunter/<int:livre_id>', methods=['POST'])
def emprunter_livre(livre_id):
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db()
    livre = conn.execute('SELECT stock FROM livres WHERE id = ?', (livre_id,)).fetchone()
    if not livre or livre[0] <= 0:
        conn.close()
        return "<h3>Livre non disponible</h3>"
    conn.execute('INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)', (user_id, livre_id))
    conn.execute('UPDATE livres SET stock = stock - 1 WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

@app.route('/livres/retourner/<int:livre_id>', methods=['POST'])
def retourner_livre(livre_id):
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db()
    emprunt = conn.execute("SELECT id FROM emprunts WHERE user_id = ? AND livre_id = ? AND date_retour IS NULL", 
                           (user_id, livre_id)).fetchone()
    if not emprunt:
        conn.close()
        return "<h3>Erreur : vous n'avez pas emprunté ce livre ou il est déjà retourné.</h3>"
    conn.execute("UPDATE emprunts SET date_retour = CURRENT_TIMESTAMP WHERE id = ?", (emprunt[0],))
    conn.execute("UPDATE livres SET stock = stock + 1 WHERE id = ?", (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("mes_emprunts"))

@app.route('/mes_emprunts/')
def mes_emprunts():
    if not est_authentifie(): return redirect(url_for('authentification'))
    conn = get_db()
    emprunts = conn.execute("""
        SELECT livres.id, livres.titre, emprunts.date_emprunt, emprunts.date_retour
        FROM emprunts JOIN livres ON emprunts.livre_id = livres.id
        WHERE emprunts.user_id = ?""", (session.get('user_id'),)).fetchall()
    conn.close()
    return render_template('emprunts.html', emprunts=emprunts)

@app.route('/livres/recherche', methods=['GET','POST'])
def recherche_livres():
    titre = request.form.get('titre') if request.method == 'POST' else request.args.get('titre')
    conn = get_db()
    livres = conn.execute('SELECT * FROM livres WHERE titre LIKE ?', (f"%{titre}%",)).fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/supprimer/<int:livre_id>', methods=['POST'])
def supprimer_livre(livre_id):
    if session.get('role') != 'admin': return "<h3>Accès refusé</h3>"
    conn = get_db()
    conn.execute('DELETE FROM livres WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

# --------------------------
# Gestion des Utilisateurs
# --------------------------

@app.route('/users/ajouter', methods=['GET', 'POST'])
def ajouter_user():
    if not est_authentifie() or session.get('role') != 'admin':
        return "<h3>Accès refusé : admin uniquement</h3>"

    conn = get_db()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     (username, password, role))
        conn.commit()
        # On ne redirige pas forcément, on peut rester sur la page pour voir le nouveau membre
        return redirect(url_for('ajouter_user'))

    # RÉCUPÉRATION DES MEMBRES : On récupère tous les utilisateurs pour les afficher
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()

    return render_template('ajouter_user.html', users=users)

# --------------------------
# GESTION DES TÂCHES (OBJECTIFS)
# --------------------------

@app.route('/tasks-page')
def tasks_page():
    return render_template('tasks.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks_api():
    conn = get_db()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY is_completed ASC, due_date ASC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task_api():
    try:
        data = request.json
        conn = get_db()
        conn.execute('INSERT INTO tasks (title, description, due_date, is_completed) VALUES (?, ?, ?, 0)',
                     (data['title'], data.get('description', ''), data.get('due_date', '')))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/tasks/<int:id>/toggle', methods=['POST'])
def toggle_task_api(id):
    conn = get_db()
    conn.execute('UPDATE tasks SET is_completed = 1 - is_completed WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task_api(id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

if __name__ == "__main__":
    app.run(debug=True)
