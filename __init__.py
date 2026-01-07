from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
from flask import render_template
from flask import json
from urllib.request import urlopen
from werkzeug.utils import secure_filename
import sqlite3
from flask import request, Response

USER_LOGIN = "user"
USER_PASSWORD = "12345"

def require_user_auth():
    # Vérifie une authentification Basic Auth user/12345.
    auth = request.authorization
    if not auth or not (auth.username == USER_LOGIN and auth.password == USER_PASSWORD):
        return Response(
            "Accès refusé (auth user requise)",
            401,
            {"WWW-Authenticate": 'Basic realm="User Area"'}
        )
    return None

app = Flask(__name__)                                                                                                                  
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

# Fonction pour créer une clé "authentifie" dans la session utilisateur
def est_authentifie():
    return session.get('authentifie')

@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))

  # Si l'utilisateur est authentifié
    return "<h2>Bravo, vous êtes authentifié</h2>"

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        # Vérifier les identifiants
        if request.form['username'] == 'admin' and request.form['password'] == 'password': # password à cacher par la suite
            session['authentifie'] = True
            # Rediriger vers la route lecture après une authentification réussie
            return redirect(url_for('lecture'))
        else:
            # Afficher un message d'erreur si les identifiants sont incorrects
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)

@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    # Rendre le template HTML et transmettre les données
    return render_template('read_data.html', data=data)

@app.route('/consultation/')
def ReadBDD():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)

@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    return render_template('formulaire.html')  # afficher le formulaire

@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    nom = request.form['nom']
    prenom = request.form['prenom']

   
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()


    cursor.execute('INSERT INTO clients (created, nom, prenom, adresse) VALUES (?, ?, ?, ?)', (1002938, nom, prenom, "ICI"))
    conn.commit()
    conn.close()
    return redirect('/consultation/')  # Rediriger vers la page d'accueil après l'enregistrement

@app.route('/fiche_nom/', methods=['GET', 'POST'])
def fiche_nom():
    # Protection user/12345 (Basic Auth)
    deny = require_user_auth()
    if deny:
        return deny

  
    nom = ""
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
    else:
        nom = request.args.get('nom', '').strip()

    # Si aucun nom fourni, afficher un petit formulaire
    if not nom:
        return """
        <h2>Recherche client par nom</h2>
        <form method="POST">
            <label>Nom :</label>
            <input name="nom" placeholder="Ex: DUPONT" required>
            <button type="submit">Rechercher</button>
        </form>
        <p>Astuce: tu peux aussi utiliser /fiche_nom/?nom=DUPONT</p>
        """

  
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE nom LIKE ?', (f"%{nom}%",))
    data = cursor.fetchall()
    conn.close()

    
    return render_template('read_data.html', data=data)


@app.route('/livres/')
def liste_livres():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livres')
    livres = cursor.fetchall()
    conn.close()
    return render_template('livres.html', livres=livres)

@app.route('/livres/ajouter', methods=['GET', 'POST'])
def ajouter_livre():
    if not est_authentifie() or session.get('role') != 'admin':
        return redirect(url_for('authentification'))
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

    user_id = session.get('user_id')  # on doit stocker l'id user dans la session
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

if __name__ == "__main__":
  app.run(debug=True)
