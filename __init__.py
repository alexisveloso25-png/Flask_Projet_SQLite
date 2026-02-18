from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# --- CONFIGURATION CHEMIN ---
# On s'assure que Flask trouve la base au bon endroit sur Alwaysdata
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db():
    """Ouvre une connexion propre à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crée les tables manquantes automatiquement"""
    conn = get_db()
    # Création de la table tasks avec la colonne is_completed
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

# On lance la vérification de la base au démarrage
init_db()

# --------------------------
# Fonctions d'authentification
# --------------------------

def est_authentifie():
    return session.get('authentifie')

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
            session['username'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']
            return redirect(url_for('liste_livres'))
        return render_template('formulaire_authentification.html', error=True)
    return render_template('formulaire_authentification.html', error=False)

# --------------------------
# Gestion des livres
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
    if not livre or livre['stock'] <= 0:
        conn.close()
        return "<h3>Livre non disponible</h3>"
    conn.execute('INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)', (user_id, livre_id))
    conn.execute('UPDATE livres SET stock = stock - 1 WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

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

# --------------------------
# Gestion des Tâches (API)
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
        conn.execute(
            'INSERT INTO tasks (title, description, due_date, is_completed) VALUES (?, ?, ?, 0)',
            (data['title'], data.get('description', ''), data.get('due_date', ''))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
