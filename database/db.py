import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'menu.db'


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
                is_mandatory BOOLEAN DEFAULT 0,
                PRIMARY KEY (item_id, addition_id),
                FOREIGN KEY (item_id) REFERENCES menu_items(id),
                FOREIGN KEY (addition_id) REFERENCES additions(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS neighborhoods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                delivery_fee REAL NOT NULL DEFAULT 0.0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT UNIQUE,
                street TEXT,
                number TEXT,
                neighborhood_id INTEGER,
                reference TEXT,
                FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL DEFAULT 0.0,
                status TEXT DEFAULT 'Pendente',
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item_additions (
                order_item_id INTEGER NOT NULL,
                addition_id INTEGER NOT NULL,
                PRIMARY KEY (order_item_id, addition_id),
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (addition_id) REFERENCES additions(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_specific_additions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (item_id) REFERENCES menu_items(id)
            )
        ''')

        # Migração: adicionar coluna is_mandatory se não existir
        cursor.execute("PRAGMA table_info(item_addition_link)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'is_mandatory' not in columns:
            cursor.execute('''
                ALTER TABLE item_addition_link 
                ADD COLUMN is_mandatory BOOLEAN DEFAULT 0
            ''')

        # Migração: adicionar coluna neighborhood_id se não existir
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'neighborhood_id' not in columns:
            cursor.execute('''
                ALTER TABLE customers ADD COLUMN neighborhood_id INTEGER 
                REFERENCES neighborhoods(id)
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
        cursor.execute(
            'SELECT id FROM menu_items WHERE category_id = ?', (category_id,))
        item_ids = [r[0] for r in cursor.fetchall()]
        # Exclui todos os itens vinculados
        for item_id in item_ids:
            cursor.execute(
                'DELETE FROM item_addition_link WHERE item_id = ?', (item_id,))
            cursor.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
        # Exclui a categoria
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()


def update_category(category_id, name):
    """Atualiza o nome de uma categoria mantendo o id e todos os vínculos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(
                'Erro ao atualizar categoria: nome já existe.') from e

# CRUD para adicionais


def add_addition(name, price=0.0):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO additions (name, price) VALUES (?, ?)', (name, price))
            addition_id = cursor.lastrowid
            conn.commit()
            return addition_id
        except sqlite3.IntegrityError as e:
            raise ValueError('Complemento já existe.') from e


def delete_addition(addition_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        # Remove da tabela de adicionais
        cursor.execute('DELETE FROM additions WHERE id = ?', (addition_id,))
        # Remove dos vínculos de categoria
        cursor.execute(
            'DELETE FROM category_addition_link WHERE addition_id = ?', (addition_id,))
        # Remove dos vínculos de itens do cardápio
        cursor.execute(
            'DELETE FROM item_addition_link WHERE addition_id = ?', (addition_id,))
        conn.commit()


def update_addition(addition_id, name, price):
    """Atualiza o nome e o preço de um complemento mantendo o id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE additions SET name = ?, price = ? WHERE id = ?', (name, price, addition_id))
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(
                'Erro ao atualizar complemento: nome já existe.') from e

# CRUD para itens do cardápio


def add_menu_item(name, price, category_id, description='', addition_ids=None, mandatory_ids=None):
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
                is_mandatory = 1 if mandatory_ids and add_id in mandatory_ids else 0
                cursor.execute(
                    'INSERT INTO item_addition_link (item_id, addition_id, is_mandatory) VALUES (?, ?, ?)',
                    (item_id, add_id, is_mandatory))
        conn.commit()
        return item_id


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


def update_menu_item(item_id, name, price, category_id, description, addition_ids=None, mandatory_ids=None):
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
        cursor.execute(
            'DELETE FROM item_addition_link WHERE item_id=?', (item_id,))
        # Adiciona vínculos novos
        if addition_ids:
            for add_id in addition_ids:
                is_mandatory = 1 if mandatory_ids and add_id in mandatory_ids else 0
                cursor.execute(
                    'INSERT INTO item_addition_link (item_id, addition_id, is_mandatory) VALUES (?, ?, ?)',
                    (item_id, add_id, is_mandatory))
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


# CRUD para clientes

def add_customer(name, phone, street=None, number=None, neighborhood_id=None, reference=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO customers (name, phone, street, number, neighborhood_id, reference) VALUES (?, ?, ?, ?, ?, ?)',
                (name, phone, street, number, neighborhood_id, reference)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(
                'Telefone já cadastrado para outro cliente.') from e


def get_customers():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.phone, c.street, c.number, c.neighborhood_id, c.reference, n.name as neighborhood_name
            FROM customers c
            LEFT JOIN neighborhoods n ON c.neighborhood_id = n.id
            ORDER BY c.name
        ''')
        return cursor.fetchall()


def update_customer(customer_id, name, phone, street=None, number=None, neighborhood_id=None, reference=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE customers SET name=?, phone=?, street=?, number=?, neighborhood_id=?, reference=? WHERE id=?',
                (name, phone, street, number, neighborhood_id, reference, customer_id)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(
                'Telefone já cadastrado para outro cliente.') from e


def delete_customer(customer_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        conn.commit()


def get_customer_by_phone(phone):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, phone, street, number, reference FROM customers WHERE phone = ?', (phone,))
        return cursor.fetchone()


# CRUD para pedidos

def add_order(customer_id=None, total_amount=0.0, notes=''):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO orders (customer_id, total_amount, notes) VALUES (?, ?, ?)',
            (customer_id, total_amount, notes)
        )
        order_id = cursor.lastrowid
        conn.commit()
        return order_id


def get_orders():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, o.customer_id, c.name, c.phone, o.order_date, 
                   o.total_amount, o.status, o.notes
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.order_date DESC
        ''')
        return cursor.fetchall()


def get_customer_orders(customer_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, o.order_date, o.total_amount, o.status, o.notes
            FROM orders o
            WHERE o.customer_id = ?
            ORDER BY o.order_date DESC
        ''', (customer_id,))
        return cursor.fetchall()


def add_order_item(order_id, menu_item_id, quantity, unit_price):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price) VALUES (?, ?, ?, ?)',
            (order_id, menu_item_id, quantity, unit_price)
        )
        order_item_id = cursor.lastrowid
        conn.commit()
        return order_item_id


def get_order_items(order_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oi.id, oi.menu_item_id, m.name, oi.quantity, oi.unit_price,
                   (oi.quantity * oi.unit_price) as total
            FROM order_items oi
            JOIN menu_items m ON oi.menu_item_id = m.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        return cursor.fetchall()


def update_order_total(order_id):
    """Atualiza o total do pedido baseado nos itens"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET total_amount = (
                SELECT COALESCE(SUM(quantity * unit_price), 0)
                FROM order_items 
                WHERE order_id = ?
            )
            WHERE id = ?
        ''', (order_id, order_id))
        conn.commit()


def search_customers(search_term):
    """Busca clientes por nome, telefone ou endereço (rua, número, referência)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        search_pattern = f'%{search_term}%'
        cursor.execute('''
            SELECT c.id, c.name, c.phone, c.street, c.number, c.neighborhood_id, c.reference, n.name as neighborhood_name
            FROM customers c
            LEFT JOIN neighborhoods n ON c.neighborhood_id = n.id
            WHERE c.name LIKE ? OR c.phone LIKE ? OR c.street LIKE ? 
            OR c.number LIKE ? OR c.reference LIKE ? 
            ORDER BY c.name
        ''', (
            search_pattern, search_pattern, search_pattern,
            search_pattern, search_pattern
        ))
        return cursor.fetchall()


# Funções para gerenciar bairros


def add_neighborhood(name, delivery_fee):
    """Adiciona um novo bairro"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO neighborhoods (name, delivery_fee) VALUES (?, ?)',
                (name, delivery_fee)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Erro: Bairro já existe.') from e


def get_neighborhoods():
    """Retorna todos os bairros"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, delivery_fee FROM neighborhoods ORDER BY name'
        )
        return cursor.fetchall()


def update_neighborhood(neighborhood_id, name, delivery_fee):
    """Atualiza um bairro"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE neighborhoods SET name = ?, delivery_fee = ? WHERE id = ?',
                (name, delivery_fee, neighborhood_id)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError('Erro: Nome do bairro já existe.') from e


def delete_neighborhood(neighborhood_id):
    """Exclui um bairro"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Verifica se há clientes usando este bairro
        cursor.execute(
            'SELECT COUNT(*) FROM customers WHERE neighborhood_id = ?',
            (neighborhood_id,)
        )
        if cursor.fetchone()[0] > 0:
            raise ValueError(
                'Não é possível excluir bairro: existem clientes cadastrados neste bairro.'
            )
        cursor.execute('DELETE FROM neighborhoods WHERE id = ?',
                       (neighborhood_id,))
        conn.commit()


def search_menu_items(search_text):
    """Busca itens do cardápio por nome"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.name, m.price, m.category_id,
                   c.name as category_name, m.description
            FROM menu_items m
            JOIN categories c ON m.category_id = c.id
            WHERE m.name LIKE ?
            ORDER BY m.name
        ''', (f'%{search_text}%',))
        return cursor.fetchall()


def get_additions_by_category(category_id):
    """Busca complementos disponíveis para uma categoria"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.name, a.price
            FROM additions a
            JOIN category_addition_link cal ON a.id = cal.addition_id
            WHERE cal.category_id = ?
            ORDER BY a.name
        ''', (category_id,))
        return cursor.fetchall()


def get_additions_by_item(item_id):
    """Busca complementos específicos vinculados diretamente ao item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.name, a.price
            FROM additions a
            JOIN item_addition_link ial ON a.id = ial.addition_id
            WHERE ial.item_id = ?
            ORDER BY a.name
        ''', (item_id,))
        return cursor.fetchall()


def get_all_additions_for_item(item_id, category_id):
    """Busca todos os complementos disponíveis para um item (categoria + item específico)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Busca complementos da categoria e complementos específicos do item
        cursor.execute('''
            SELECT DISTINCT a.id, a.name, a.price
            FROM additions a
            LEFT JOIN category_addition_link cal ON a.id = cal.addition_id
            LEFT JOIN item_addition_link ial ON a.id = ial.addition_id
            WHERE cal.category_id = ? OR ial.item_id = ?
            ORDER BY a.name
        ''', (category_id, item_id))
        return cursor.fetchall()


def get_all_additions_for_item_with_mandatory_info(item_id, category_id):
    """Retorna complementos com informação sobre obrigatoriedade"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Busca complementos da categoria e específicos do item com info de obrigatoriedade
        cursor.execute('''
            SELECT DISTINCT a.id, a.name, a.price, 
                   COALESCE(ial.is_mandatory, 0) as is_mandatory
            FROM additions a
            LEFT JOIN category_addition_link cal ON a.id = cal.addition_id
            LEFT JOIN item_addition_link ial ON a.id = ial.addition_id AND ial.item_id = ?
            WHERE cal.category_id = ? OR ial.item_id = ?
            ORDER BY is_mandatory DESC, a.name
        ''', (item_id, category_id, item_id))
        return cursor.fetchall()


def get_item_specific_additions(item_id):
    """Retorna os complementos específicos de um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, price FROM item_specific_additions WHERE item_id = ?',
            (item_id,)
        )
        return cursor.fetchall()


def set_item_specific_additions(item_id, additions_data):
    """Define os complementos específicos de um item
    additions_data: lista de dicionários com 'name' e 'price'
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Remove complementos específicos anteriores
        cursor.execute(
            'DELETE FROM item_specific_additions WHERE item_id = ?', (item_id,)
        )
        # Adiciona os novos complementos específicos
        for addition in additions_data:
            cursor.execute(
                'INSERT INTO item_specific_additions (item_id, name, price) VALUES (?, ?, ?)',
                (item_id, addition['name'], addition['price'])
            )
        conn.commit()


def save_order(customer_id, items_data, total_amount, notes=""):
    """Salva um pedido no banco de dados"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Cria o pedido
        cursor.execute('''
            INSERT INTO orders (customer_id, total_amount, notes)
            VALUES (?, ?, ?)
        ''', (customer_id, total_amount, notes))

        order_id = cursor.lastrowid

        # Adiciona os itens do pedido
        for item_data in items_data:
            cursor.execute('''
                INSERT INTO order_items
                (order_id, menu_item_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item_data['menu_item_id'],
                  item_data['quantity'], item_data['unit_price']))

            order_item_id = cursor.lastrowid

            # Adiciona os adicionais do item
            for addition_id in item_data.get('additions', []):
                cursor.execute('''
                    INSERT INTO order_item_additions
                    (order_item_id, addition_id)
                    VALUES (?, ?)
                ''', (order_item_id, addition_id))

        conn.commit()
        return order_id


def set_item_mandatory_additions(item_id, addition_ids):
    """Define quais complementos são obrigatórios para um item específico"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Atualiza o campo is_mandatory para todos os complementos do item
        cursor.execute(
            'UPDATE item_addition_link SET is_mandatory = 0 WHERE item_id = ?', (item_id,))
        # Marca os complementos selecionados como obrigatórios
        if addition_ids:
            placeholders = ','.join(['?' for _ in addition_ids])
            cursor.execute(
                f'UPDATE item_addition_link SET is_mandatory = 1 WHERE item_id = ? AND addition_id IN ({placeholders})',
                [item_id] + addition_ids)
        conn.commit()


def get_item_mandatory_additions(item_id):
    """Retorna os IDs dos complementos obrigatórios para um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT addition_id FROM item_addition_link WHERE item_id = ? AND is_mandatory = 1', (item_id,))
        return [row[0] for row in cursor.fetchall()]


def get_item_mandatory_additions_details(item_id):
    """Retorna detalhes dos complementos obrigatórios para um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.name, a.price
            FROM additions a
            JOIN item_addition_link ial ON a.id = ial.addition_id
            WHERE ial.item_id = ? AND ial.is_mandatory = 1
        ''', (item_id,))
        return cursor.fetchall()


def get_all_available_additions_for_item(item_id, category_id):
    """Retorna todos os complementos disponíveis para um item (categoria + específicos)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Busca complementos da categoria
        cursor.execute('''
            SELECT a.id, a.name, a.price, 'category' as source
            FROM additions a
            JOIN category_addition_link cal ON a.id = cal.addition_id
            WHERE cal.category_id = ?
        ''', (category_id,))
        category_additions = cursor.fetchall()

        # Busca complementos específicos do item
        cursor.execute('''
            SELECT a.id, a.name, a.price, 'item_specific' as source
            FROM additions a
            JOIN item_addition_link ial ON a.id = ial.addition_id
            WHERE ial.item_id = ?
        ''', (item_id,))
        item_additions = cursor.fetchall()

        # Combina os resultados
        all_additions = category_additions + item_additions
        return all_additions


def add_item_specific_addition(item_id, name, price):
    """Adiciona um complemento específico para um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO item_specific_additions (item_id, name, price) VALUES (?, ?, ?)',
                (item_id, name, price)
            )
            addition_id = cursor.lastrowid
            conn.commit()
            return addition_id
        except sqlite3.IntegrityError as e:
            raise ValueError(
                f'Erro ao adicionar complemento específico: {e}') from e


def get_all_additions_for_item_with_mandatory_and_specific_info(item_id, category_id):
    """Retorna todos os complementos disponíveis para um item com informações de obrigatório e específico"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Busca complementos da categoria
        cursor.execute('''
            SELECT a.id, a.name, a.price, 
                   COALESCE(ial.is_mandatory, 0) as is_mandatory,
                   'category' as source
            FROM additions a
            JOIN category_addition_link cal ON a.id = cal.addition_id
            LEFT JOIN item_addition_link ial ON a.id = ial.addition_id AND ial.item_id = ?
            WHERE cal.category_id = ?
        ''', (item_id, category_id))
        category_additions = cursor.fetchall()

        # Busca complementos específicos do item
        cursor.execute('''
            SELECT isa.id, isa.name, isa.price, 0 as is_mandatory, 'item_specific' as source
            FROM item_specific_additions isa
            WHERE isa.item_id = ?
        ''', (item_id,))
        item_specific_additions = cursor.fetchall()

        # Combina os resultados
        all_additions = list(category_additions) + \
            list(item_specific_additions)
        return all_additions
        return all_additions
