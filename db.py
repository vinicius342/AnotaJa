import json
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
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL DEFAULT 0.0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_addition_link (
                category_id INTEGER NOT NULL,
                addition_id INTEGER NOT NULL,
                PRIMARY KEY (category_id, addition_id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (addition_id) REFERENCES additions(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_addition_link (
                item_id INTEGER NOT NULL,
                addition_id INTEGER NOT NULL,
                PRIMARY KEY (item_id, addition_id),
                FOREIGN KEY (item_id) REFERENCES menu_items(id),
                FOREIGN KEY (addition_id) REFERENCES additions(id)
            )
        ''')
        conn.commit()

# CRUD para categorias


def add_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Categoria já existe.') from e


def get_categories():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories')
        return [row[0] for row in cursor.fetchall()]


def delete_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        # Busca o id da categoria
        cursor.execute('SELECT id FROM categories WHERE name = ?', (name,))
        row = cursor.fetchone()
        if not row:
            return
        category_id = row[0]
        # Busca todos os itens do cardápio vinculados a essa categoria
        cursor.execute('SELECT id FROM menu_items WHERE category_id = ?', (category_id,))
        item_ids = [r[0] for r in cursor.fetchall()]
        # Exclui todos os itens vinculados
        for item_id in item_ids:
            cursor.execute('DELETE FROM item_addition_link WHERE item_id = ?', (item_id,))
            cursor.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
        # Exclui a categoria
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()

def update_category(category_id, name):
    """Atualiza o nome de uma categoria mantendo o id e todos os vínculos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Erro ao atualizar categoria: nome já existe.') from e

# CRUD para adicionais


def add_addition(name, price=0.0):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO additions (name, price) VALUES (?, ?)', (name, price))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Adicional já existe.') from e


def delete_addition(addition_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        # Remove da tabela de adicionais
        cursor.execute('DELETE FROM additions WHERE id = ?', (addition_id,))
        # Remove dos vínculos de categoria
        cursor.execute(
            'DELETE FROM category_addition_link WHERE addition_id = ?', (addition_id,))
        # Remove dos vínculos de itens do cardápio
        cursor.execute('DELETE FROM item_addition_link WHERE addition_id = ?', (addition_id,))
        conn.commit()


def update_addition(addition_id, name, price):
    """Atualiza o nome e o preço de um adicional mantendo o id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE additions SET name = ?, price = ? WHERE id = ?', (name, price, addition_id))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Erro ao atualizar adicional: nome já existe.') from e

# CRUD para itens do cardápio


def add_menu_item(name, price, category_id, description='', addition_ids=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO menu_items (name, price, category_id, description) VALUES (?, ?, ?, ?)',
                (name, price, category_id, description)
            )
        except sqlite3.IntegrityError as e:
            raise ValueError('Já existe um item com esse nome.') from e
        item_id = cursor.lastrowid
        if addition_ids:
            for add_id in addition_ids:
                cursor.execute(
                    'INSERT INTO item_addition_link (item_id, addition_id) VALUES (?, ?)', (item_id, add_id))
        conn.commit()


def get_menu_items():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mi.id, mi.name, mi.price, c.name, mi.description
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
        ''')
        items = []
        for row in cursor.fetchall():
            item_id, name, price, category_name, description = row
            # Busca os adicionais vinculados
            cursor.execute('''
                SELECT a.id, a.name, a.price FROM item_addition_link l
                JOIN additions a ON l.addition_id = a.id
                WHERE l.item_id = ?
            ''', (item_id,))
            additions = [(add_id, add_name, add_price)
                         for add_id, add_name, add_price in cursor.fetchall()]
            items.append(
                (item_id, name, price, category_name, description, additions))
        return items


def delete_menu_item(item_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM item_addition_link WHERE item_id = ?', (item_id,))
        cursor.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
        conn.commit()


def update_menu_item(item_id, name, price, category_id, description, addition_ids=None):
    import sqlite3
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE menu_items SET name=?, price=?, category_id=?, description=? WHERE id=?',
                (name, price, category_id, description, item_id)
            )
        except sqlite3.IntegrityError as e:
            raise ValueError('Já existe um item com esse nome.') from e
        # Remove vínculos antigos
        cursor.execute('DELETE FROM item_addition_link WHERE item_id=?', (item_id,))
        # Adiciona vínculos novos
        if addition_ids:
            for add_id in addition_ids:
                cursor.execute('INSERT INTO item_addition_link (item_id, addition_id) VALUES (?, ?)', (item_id, add_id))
        conn.commit()

# CRUD para vínculos categoria-adicionais


def set_category_additions(category, additions):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM category_addition_link WHERE category_id = ?', (category,))
        for add in additions:
            cursor.execute(
                'INSERT INTO category_addition_link (category_id, addition_id) VALUES (?, ?)', (category, add))
        conn.commit()


def get_category_additions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT category_id, addition_id FROM category_addition_link')
        data = cursor.fetchall()
        result = {}
        for cat, add in data:
            result.setdefault(cat, []).append(add)
        return result


def get_category_id(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM categories WHERE name = ?', (name,))
        row = cursor.fetchone()
        return row[0] if row else None


def get_all_additions_with_id():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, price FROM additions')
        return [(row[0], row[1], row[2]) for row in cursor.fetchall()]


def get_category_addition_ids(category_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT addition_id FROM category_addition_link WHERE category_id = ?', (category_id,))
        return [row[0] for row in cursor.fetchall()]


def set_category_addition_ids(category_id, addition_ids):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM category_addition_link WHERE category_id = ?', (category_id,))
        for add_id in addition_ids:
            cursor.execute(
                'INSERT INTO category_addition_link (category_id, addition_id) VALUES (?, ?)', (category_id, add_id))
        conn.commit()
