from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Ta clé secrète

# --- CONFIGURATION CHEMINS ---
BASE_DIR = "/home/avelosc/www/flask1"
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    """Établit une connexion avec Row_factory pour le JSON et les objets"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crée les tables si elles n'existent pas au démarrage"""
    conn = get_db_connection()
    # Table des Tâches (Objectifs)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            is_completed INTEGER DEFAULT 0
        )
    ''')
    # Table des Emprunts (si pas déjà là)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emprunts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            livre_id INTEGER,
            date_emprunt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_retour TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Lancement de l'initialisation
try:
    init_db()
except Exception as e:
    print(f"Erreur init_db: {e}")

# --- AUTHENTIFICATION ---

def est_authentifie():
    return session.get('authentifie')

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
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

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('hello_world'))

# --- ROUTES DE BASE ---

@app.route('/')
def hello_world():
    return render_template('hello.html')

# --- GESTION DES LIVRES ---

@app.route('/livres/')
def liste_livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db_connection()
    livres = conn.execute('SELECT * FROM livres').fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/ajouter', methods=['GET', 'POST'])
def ajouter_livre():
    if not est_authentifie() or session.get('role') != 'admin':
        return "Accès refusé", 403
    if request.method == 'POST':
        titre = request.form['titre']
        auteur = request.form['auteur']
        stock = int(request.form['stock'])
        conn = get_db_connection()
        conn.execute('INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)', (titre, auteur, stock))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')

@app.route('/livres/supprimer/<int:livre_id>', methods=['POST'])
def supprimer_livre(livre_id):
    if session.get('role') != 'admin':
        return "Accès refusé", 403
    conn = get_db_connection()
    conn.execute('DELETE FROM livres WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

@app.route('/livres/recherche', methods=['GET','POST'])
def recherche_livres():
    titre = request.form.get('titre') if request.method == 'POST' else request.args.get('titre')
    conn = get_db_connection()
    livres = conn.execute('SELECT * FROM livres WHERE titre LIKE ?', (f"%{titre}%",)).fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

# --- EMPRUNTS ---

@app.route('/livres/emprunter/<int:livre_id>', methods=['POST'])
def emprunter_livre(livre_id):
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db_connection()
    livre = conn.execute('SELECT stock FROM livres WHERE id = ?', (livre_id,)).fetchone()
    if not livre or livre['stock'] <= 0:
        conn.close()
        return "Livre non disponible", 400
    conn.execute('INSERT INTO emprunts (user_id, livre_id) VALUES (?, ?)', (user_id, livre_id))
    conn.execute('UPDATE livres SET stock = stock - 1 WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

@app.route('/mes_emprunts/')
def mes_emprunts():
    if not est_authentifie(): return redirect(url_for('authentification'))
    conn = get_db_connection()
    emprunts = conn.execute("""
        SELECT livres.id, livres.titre, emprunts.date_emprunt, emprunts.date_retour
        FROM emprunts JOIN livres ON emprunts.livre_id = livres.id
        WHERE emprunts.user_id = ?""", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('emprunts.html', emprunts=emprunts)

# --- GESTION DES TÂCHES (API JSON) ---

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks_api():
    try:
        conn = get_db_connection()
        tasks = conn.execute('SELECT * FROM tasks ORDER BY is_completed ASC, id DESC').fetchall()
        conn.close()
        return jsonify([dict(row) for row in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task_api():
    try:
        data = request.get_json()
        conn = get_db_connection()
        conn.execute('INSERT INTO tasks (title, description, due_date, is_completed) VALUES (?, ?, ?, 0)',
                     (data['title'], data['description'], data.get('due_date')))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks/<int:id>/toggle', methods=['POST'])
def toggle_task_api(id):
    try:
        conn = get_db_connection()
        conn.execute('UPDATE tasks SET is_completed = 1 - is_completed WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task_api(id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
