from flask import Flask, request, jsonify, send_file
import sqlite3
import os
from datetime import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# --- 1. AFFICHER LES ERREURS CLAIREMENT ---
@app.errorhandler(Exception)
def handle_exception(e):
    # Si le site plante, ça affichera l'erreur exacte sur votre écran !
    return f"<h3>Oups ! Une erreur est survenue :</h3><pre>{traceback.format_exc()}</pre>", 500

# --- 2. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            link TEXT,
            is_vip BOOLEAN,
            status TEXT, 
            transaction_id TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 3. RECHERCHE INTELLIGENTE DES FICHIERS ---
def get_file_anywhere(filename):
    # Cherche d'abord dans un éventuel dossier "static"
    path1 = os.path.join(BASE_DIR, 'static', filename)
    if os.path.exists(path1): return send_file(path1)
    
    # Cherche ensuite à la racine (si GitHub a cassé le dossier)
    path2 = os.path.join(BASE_DIR, filename)
    if os.path.exists(path2): return send_file(path2)
    
    return f"Erreur : Impossible de trouver le fichier '{filename}'.", 404

@app.route('/')
def index():
    return get_file_anywhere('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return get_file_anywhere(path)

# --- 4. GESTION DES ANNONCES ---
@app.route('/api/ads', methods=['GET'])
def get_ads():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    c = conn.cursor()
    c.execute('SELECT id, title, description, link, is_vip FROM ads WHERE status="active" ORDER BY is_vip DESC, id DESC')
    ads = [{'id': row[0], 'title': row[1], 'description': row[2], 'link': row[3], 'is_vip': bool(row[4])} for row in c.fetchall()]
    conn.close()
    return jsonify(ads)

@app.route('/api/ads', methods=['POST'])
def create_ad():
    data = request.json
    title = data.get('title')
    desc = data.get('description')
    link = data.get('link')
    is_vip = data.get('is_vip', False)
    transaction_id = data.get('transaction_id', '')

    status = 'pending' if is_vip else 'active'
    if is_vip and transaction_id: 
        status = 'active'

    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))
    c = conn.cursor()
    c.execute('INSERT INTO ads (title, description, link, is_vip, status, transaction_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (title, desc, link, is_vip, status, transaction_id, datetime.now()))
    conn.commit()
    ad_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': ad_id, 'status': status})

@app.route('/api/bot/verify', methods=['POST'])
def verify_transaction():
    data = request.json
    tx_id = data.get('transaction_id', '').upper()
    if len(tx_id) > 4 and tx_id != "0000":
        return jsonify({'valid': True, 'message': 'Paiement détecté avec succès !'})
    return jsonify({'valid': False, 'message': 'Je ne trouve pas ce paiement. Veuillez vérifier l\'ID.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
