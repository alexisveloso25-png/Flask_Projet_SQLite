import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# -------- Clients --------
clients = [
    ('DUPONT', 'Emilie', '123, Rue des Lilas, 75001 Paris'),
    ('LEROUX', 'Lucas', '456, Avenue du Soleil, 31000 Toulouse'),
    ('MARTIN', 'Amandine', '789, Rue des Érables, 69002 Lyon'),
    ('TREMBLAY', 'Antoine', '1010, Boulevard de la Mer, 13008 Marseille'),
    ('LAMBERT', 'Sarah', '222, Avenue de la Liberté, 59000 Lille'),
    ('GAGNON', 'Nicolas', '456, Boulevard des Cerisiers, 69003 Lyon'),
    ('DUBOIS', 'Charlotte', '789, Rue des Roses, 13005 Marseille'),
    ('LEFEVRE', 'Thomas', '333, Rue de la Paix, 75002 Paris')
]
for nom, prenom, adresse in clients:
    cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)", (nom, prenom, adresse))

# -------- Users --------
users = [
    ('admin', 'admin123', 'admin'),
    ('user', '12345', 'user')
]
for username, password, role in users:
    cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))

# -------- Livres --------
livres = [
    ('Le Petit Prince', 'Antoine de Saint-Exupéry', 5),
    ('1984', 'George Orwell', 4),
    ('Les Misérables', 'Victor Hugo', 3),
    ("Harry Potter à l'école des sorciers", 'J.K. Rowling', 5),
    ('Le Seigneur des Anneaux', 'J.R.R. Tolkien', 5)
]
for titre, auteur, stock in livres:
    cur.execute("INSERT INTO livres (titre, auteur, stock) VALUES (?, ?, ?)", (titre, auteur, stock))

# -------- NE PAS INSERER D'EMPRUNTS ICI --------
# car il faudrait des user_id et livre_id corrects

connection.commit()
connection.close()
print("Base de données bibliothèque initialisée !")
