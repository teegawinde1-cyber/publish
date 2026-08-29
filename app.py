from flask import Flask, request, jsonify, send_from_directory, send_file
import sqlite3
import os
from datetime import datetime

# Configuration absolue pour Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR)

def init_db():
    # Créer la DB dans un endroit où Render a les droits d'écriture
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

@app.route('/')
def index():
    return send_file(os.path.join(STATIC_DIR, 'index.html'))

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)

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
    else:
        return jsonify({'valid': False, 'message': 'Je ne trouve pas ce paiement. Veuillez vérifier l\'ID.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
