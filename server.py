import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

DB_NAME = "scheduler.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL)''')
    # Tasks Table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  description TEXT, 
                  due_date TEXT, 
                  priority TEXT, 
                  status TEXT, 
                  user_id INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
        
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({'id': user_id, 'username': username}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    
    if user:
        return jsonify({'id': user['id'], 'username': user['username']}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
        
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    
    tasks_list = [dict(task) for task in tasks]
    # Convert keys to camelCase for frontend compatibility if needed, or handle in frontend.
    # For simplicity, we'll keep snake_case in DB and map in frontend or here.
    # Let's map here to match existing frontend expectations
    mapped_tasks = []
    for t in tasks_list:
        mapped_tasks.append({
            'id': t['id'],
            'title': t['title'],
            'description': t['description'],
            'dueDate': t['due_date'],
            'priority': t['priority'],
            'status': t['status'],
            'userId': t['user_id']
        })
        
    return jsonify(mapped_tasks), 200

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json
    conn = get_db_connection()
    cursor = conn.execute(
        'INSERT INTO tasks (title, description, due_date, priority, status, user_id) VALUES (?, ?, ?, ?, ?, ?)',
        (data['title'], data['description'], data['dueDate'], data['priority'], data['status'], data['userId'])
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': new_id, **data}), 201

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.json
    conn = get_db_connection()
    conn.execute(
        'UPDATE tasks SET title = ?, description = ?, due_date = ?, priority = ?, status = ? WHERE id = ?',
        (data['title'], data['description'], data['dueDate'], data['priority'], data['status'], id)
    )
    conn.commit()
    conn.close()
    return jsonify(data), 200

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'}), 200

if __name__ == '__main__':
    init_db()
    print("Database initialized. Server running on port 5000...")
    app.run(debug=True, port=5000)
