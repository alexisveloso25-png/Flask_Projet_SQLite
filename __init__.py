from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import sqlite3
import mysql.connector

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

# --------------------------
# CONFIGURATION DES BASES
# --------------------------

# Base 1 : SQLite (Bibliothèque - Ton système actuel)
def get_db_library():
    # Assure-toi que le fichier database.db est bien à la racine
    return sqlite3.connect('database.db')

# Base 2 : MySQL Alwaysdata (Gestionnaire de Tâches - Nouvelle base)
def get_db_tasks():
    return mysql.connector.connect(
        host="mysql-aveloso.alwaysdata.net",
        user="aveloso",
        password="Favanola250505..",
        database="aveloso_db"
    )

# --------------------------
# FONCTIONS D'AUTHENTIFICATION (Bibliothèque)
# --------------------------
def est_authentifie():
    return session.get('authentifie')

# --------------------------
# ROUTES BIBLIOTHÈQUE (BASE SQLITE)
# --------------------------
@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_library()
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

@app.route('/livres/')
def liste_livres():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = get_db_library()
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
        titre, auteur, stock = request.form['titre'], request.form['auteur'], int(request.form['stock'])
        conn = get_db_library()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)', (titre, auteur, stock))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')

@app.route('/livres/emprunter/<int:livre_id>', methods=['POST'])
def emprunter_livre(livre_id):
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db_library()
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
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db_library()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM emprunts WHERE user_id=? AND livre_id=? AND date_retour IS NULL", (user_id, livre_id))
    emprunt = cursor.fetchone()
    if not emprunt:
        conn.close()
        return "<h3>Erreur de retour</h3>"
    cursor.execute("UPDATE emprunts SET date_retour=CURRENT_TIMESTAMP WHERE id=?", (emprunt[0],))
    cursor.execute("UPDATE livres SET stock=stock+1 WHERE id=?", (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("mes_emprunts"))

@app.route('/mes_emprunts/')
def mes_emprunts():
    if not est_authentifie(): return redirect(url_for('authentification'))
    user_id = session.get('user_id')
    conn = get_db_library()
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
    conn = get_db_library()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livres WHERE titre LIKE ?', (f"%{titre}%",))
    livres = cursor.fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/supprimer/<int:livre_id>', methods=['POST'])
def supprimer_livre(livre_id):
    if session.get('role') != 'admin': return "<h3>Accès refusé</h3>"
    conn = get_db_library()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM livres WHERE id = ?', (livre_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))

@app.route('/users/ajouter', methods=['GET', 'POST'])
def ajouter_user():
    if not est_authentifie() or session.get('role') != 'admin': return "<h3>Accès refusé</h3>"
    if request.method == 'POST':
        u, p, r = request.form['username'], request.form['password'], request.form['role']
        conn = get_db_library()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (u, p, r))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_user.html')

# --------------------------
# GESTIONNAIRE DE TÂCHES (MYSQL + API JS)
# --------------------------

@app.route('/tasks-page')
def tasks_page():
    return render_template('tasks.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks_api():
    conn = get_db_tasks()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks ORDER BY due_date ASC")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task_api():
    data = request.json
    conn = get_db_tasks()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, due_date) VALUES (%s, %s, %s)",
        (data['title'], data['description'], data['due_date'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task_api(id):
    conn = get_db_tasks()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "deleted"})

# --------------------------
# LANCEMENT
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
