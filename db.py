import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'menu.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS additions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                additions TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_additions (
                category TEXT NOT NULL,
                addition TEXT NOT NULL,
                PRIMARY KEY (category, addition)
            )
        ''')
        conn.commit()

# CRUD para categorias
def add_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (name,))
        conn.commit()

def get_categories():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories')
        return [row[0] for row in cursor.fetchall()]

def delete_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE name = ?', (name,))
        conn.commit()

# CRUD para adicionais
def add_addition(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO additions (name) VALUES (?)', (name,))
        conn.commit()

def get_additions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM additions')
        return [row[0] for row in cursor.fetchall()]

def delete_addition(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM additions WHERE name = ?', (name,))
        conn.commit()

# CRUD para itens do cardápio
def add_menu_item(name, price, category, description='', additions=None):
    additions_str = ','.join(additions) if additions else ''
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO menu_items (name, price, category, description, additions) VALUES (?, ?, ?, ?, ?)',
            (name, price, category, description, additions_str)
        )
        conn.commit()

def get_menu_items():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name, price, category, description, additions FROM menu_items')
        return cursor.fetchall()

def delete_menu_item(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM menu_items WHERE name = ?', (name,))
        conn.commit()

# CRUD para vínculos categoria-adicionais
def set_category_additions(category, additions):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM category_additions WHERE category = ?', (category,))
        for add in additions:
            cursor.execute('INSERT INTO category_additions (category, addition) VALUES (?, ?)', (category, add))
        conn.commit()

def get_category_additions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT category, addition FROM category_additions')
        data = cursor.fetchall()
        result = {}
        for cat, add in data:
            result.setdefault(cat, []).append(add)
        return result
