from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')

# Initialiser la base de données
def init_db():
    conn = sqlite3.connect('database.db')
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
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/ads', methods=['GET'])
def get_ads():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # On récupère les VIP en premier, puis les gratuits (seulement ceux validés)
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

    status = 'pending' if is_vip else 'active' # Les gratuits sont actifs de suite, les VIP attendent validation
    
    # Si le système "IA" a déjà vérifié (simulation), on l'active directement
    if is_vip and transaction_id.startswith('OM'): 
        status = 'active'

    conn = sqlite3.connect('database.db')
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
    
    # C'est ici que l'IA intelligente vérifie
    # Dans la vraie vie, elle vérifierait dans une table "sms_recus" remplie par votre téléphone
    if len(tx_id) > 4 and tx_id != "0000":
        return jsonify({'valid': True, 'message': 'Paiement détecté avec succès !'})
    else:
        return jsonify({'valid': False, 'message': 'Je ne trouve pas ce paiement. Veuillez vérifier l\'ID.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
