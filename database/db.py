
import sqlite3
import sys
from pathlib import Path

# Importa apenas quando necessário para evitar dependência circular
try:
    from utils.log_utils import get_logger
    LOGGER = get_logger(__name__)
except ImportError:
    # Fallback simples caso não consiga importar
    class DummyLogger:
        def error(self, msg): print(f"ERROR: {msg}")
    LOGGER = DummyLogger()

# Corrige o caminho do banco para ser sempre ao lado do executável, mesmo empacotado
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'database.db'
# Garante que a pasta data/ exista antes de criar o banco
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
print(f"Caminho do banco: {DB_PATH}")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item_specific_additions (
                order_item_id INTEGER NOT NULL,
                item_specific_addition_id INTEGER NOT NULL,
                PRIMARY KEY (order_item_id, item_specific_addition_id),
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (item_specific_addition_id) REFERENCES item_specific_additions(id)
            )
        ''')
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
                mandatory_selected TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item_additions (
                order_item_id INTEGER NOT NULL,
                addition_id INTEGER NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
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
                is_mandatory BOOLEAN DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES menu_items(id)
            )
        ''')

        # Tabela de configurações do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # Migração: adicionar coluna is_mandatory aos complementos específicos se não existir
        cursor.execute("PRAGMA table_info(item_specific_additions)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'is_mandatory' not in columns:
            cursor.execute('''
                ALTER TABLE item_specific_additions 
                ADD COLUMN is_mandatory BOOLEAN DEFAULT 0
            ''')

        # Migração: adicionar coluna mandatory_selected se não existir
        cursor.execute("PRAGMA table_info(order_items)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'mandatory_selected' not in columns:
            cursor.execute('''
                ALTER TABLE order_items ADD COLUMN mandatory_selected TEXT
            ''')
        # Migração: adicionar coluna observations se não existir
        cursor.execute("PRAGMA table_info(order_items)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'observations' not in columns:
            cursor.execute('''
                ALTER TABLE order_items ADD COLUMN observations TEXT
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
    """
    Adiciona um item ao menu com complementos obrigatórios

    Args:
        mandatory_ids: Lista de IDs únicos (int para categoria, "specific_N" para específicos)
    """
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
            # Processa complementos de categoria
            for add_id in addition_ids:
                # Determina se é obrigatório baseado nos IDs únicos
                is_mandatory = 0
                if mandatory_ids:
                    # Verifica se o ID da categoria está nos obrigatórios
                    if add_id in mandatory_ids:
                        is_mandatory = 1

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


def update_menu_item_basic(item_id, name, price, category_id, description):
    """Atualiza apenas os campos básicos do item sem mexer nos vínculos"""
    import sqlite3

    from utils.log_utils import get_logger
    logger = get_logger(__name__)

    logger.info(
        f"🔧 DB_UPDATE_BASIC: Iniciando atualização básica para item {item_id}")
    logger.info(
        f"🔧 DB_UPDATE_BASIC: Valores - Nome: {name}, Preço: {price}, Categoria ID: {category_id}, Descrição: {description}")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE menu_items SET name=?, price=?, category_id=?, description=? WHERE id=?',
                (name, price, category_id, description, item_id)
            )
            affected_rows = cursor.rowcount
            logger.info(
                f"🔧 DB_UPDATE_BASIC: {affected_rows} linhas afetadas na tabela menu_items")
        except sqlite3.IntegrityError as e:
            logger.error(f"🔧 DB_UPDATE_BASIC: Erro de integridade: {e}")
            raise ValueError('Já existe um item com esse nome.') from e
        conn.commit()
        logger.info(
            f"🔧 DB_UPDATE_BASIC: Commit executado com sucesso para item {item_id}")
        logger.info(
            f"🔧 DB_UPDATE_BASIC: Atualização básica concluída - NENHUM vínculo foi alterado")


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
    """Atualiza os vínculos de categoria-adicionais de forma otimizada"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Busca vínculos atuais
        cursor.execute(
            'SELECT addition_id FROM category_addition_link WHERE category_id = ?',
            (category,)
        )
        current_additions = {row[0] for row in cursor.fetchall()}
        new_additions = set(additions)

        # Remove vínculos que não estão na nova lista
        to_remove = current_additions - new_additions
        if to_remove:
            placeholders = ','.join('?' * len(to_remove))
            cursor.execute(
                f'DELETE FROM category_addition_link WHERE category_id = ? AND addition_id IN ({placeholders})',
                (category,) + tuple(to_remove)
            )

        # Adiciona novos vínculos que não existem
        to_add = new_additions - current_additions
        if to_add:
            for add_id in to_add:
                cursor.execute(
                    'INSERT INTO category_addition_link (category_id, addition_id) VALUES (?, ?)',
                    (category, add_id)
                )

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
    """Atualiza os vínculos categoria-adicionais de forma otimizada"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Busca vínculos atuais
        cursor.execute(
            'SELECT addition_id FROM category_addition_link WHERE category_id = ?',
            (category_id,)
        )
        current_additions = {row[0] for row in cursor.fetchall()}
        new_additions = set(addition_ids)

        # Remove vínculos que não estão na nova lista
        to_remove = current_additions - new_additions
        if to_remove:
            placeholders = ','.join('?' * len(to_remove))
            cursor.execute(
                f'DELETE FROM category_addition_link WHERE category_id = ? '
                f'AND addition_id IN ({placeholders})',
                (category_id,) + tuple(to_remove)
            )

        # Adiciona novos vínculos que não existem
        to_add = new_additions - current_additions
        if to_add:
            for add_id in to_add:
                cursor.execute(
                    'INSERT INTO category_addition_link (category_id, addition_id) '
                    'VALUES (?, ?)',
                    (category_id, add_id)
                )

        conn.commit()


# CRUD para clientes

def add_customer(name, phone, street=None, number=None, neighborhood_id=None, reference=None):
    # Se phone for string vazia, converte para None para evitar violar UNIQUE
    phone_db = phone if phone else None
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO customers (name, phone, street, number, neighborhood_id, reference) VALUES (?, ?, ?, ?, ?, ?)',
                (name, phone_db, street, number, neighborhood_id, reference)
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
        cursor.execute('''
            SELECT c.id, c.name, c.phone, c.street, c.number, c.neighborhood_id, c.reference, n.name as neighborhood_name
            FROM customers c
            LEFT JOIN neighborhoods n ON c.neighborhood_id = n.id
            WHERE c.phone = ?
        ''', (phone,))
        return cursor.fetchone()


# CRUD para pedidos

def get_orders_today():
    """Retorna os pedidos feitos hoje, com customer_id, total e itens."""
    import datetime
    from datetime import datetime as dt

    # Usa horário local para garantir pedidos do dia
    today = dt.now().date()
    today_str = today.strftime('%Y-%m-%d')
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, customer_id, total_amount
            FROM orders
            WHERE DATE(order_date) = ?
            ORDER BY datetime(order_date, 'localtime') DESC
        ''', (today_str,))
        orders = []
        for order_id, customer_id, total in cursor.fetchall():
            # Busca itens do pedido com todos os detalhes
            cursor.execute('''
                SELECT oi.id, oi.menu_item_id, oi.quantity, oi.unit_price, m.name, m.category_id, c.name as category_name, oi.mandatory_selected, oi.observations
                FROM order_items oi
                JOIN menu_items m ON oi.menu_item_id = m.id
                JOIN categories c ON m.category_id = c.id
                WHERE oi.order_id = ?
            ''', (order_id,))
            items = []
            for row in cursor.fetchall():
                order_item_id, menu_item_id, quantity, unit_price, item_name, category_id, category_name, mandatory_selected_str, observations = row
                # Buscar descrição do item
                cursor.execute(
                    'SELECT description FROM menu_items WHERE id = ?', (menu_item_id,))
                desc_row = cursor.fetchone()
                item_description = desc_row[0] if desc_row and desc_row[0] else ''
                # Observações do item (se existir coluna, buscar; senão, vazio)
                cursor.execute('''
                    PRAGMA table_info(order_items)
                ''')
                columns = [col[1] for col in cursor.fetchall()]
                if 'observations' in columns:
                    cursor.execute(
                        'SELECT observations FROM order_items WHERE id = ?', (order_item_id,))
                    obs_row = cursor.fetchone()
                    observations = obs_row[0] if obs_row and obs_row[0] else ''
                else:
                    observations = ''

                # DEBUG: Verificar o conteúdo da tabela order_item_additions
                cursor.execute(
                    'SELECT * FROM order_item_additions WHERE order_item_id = ?', (order_item_id,))
                debug_additions = cursor.fetchall()
                print(
                    f"\033[96m[DB] DEBUG - order_item_additions para item {order_item_id}: {debug_additions}\033[0m")

                # DEBUG: Verificar se a tabela tem dados em geral
                cursor.execute('SELECT COUNT(*) FROM order_item_additions')
                total_count = cursor.fetchone()[0]
                print(
                    f"\033[96m[DB] DEBUG - Total de registros em order_item_additions: {total_count}\033[0m")

                # Adicionais com quantidade correta do banco
                # Busca complementos da tabela additions (IDs numéricos)
                cursor.execute('''
                    SELECT a.id, a.name, a.price, oia.qty FROM order_item_additions oia
                    JOIN additions a ON oia.addition_id = a.id
                    WHERE oia.order_item_id = ? AND oia.addition_id NOT LIKE 'specific_%'
                ''', (order_item_id,))
                additions_result = cursor.fetchall()

                # Busca complementos específicos do item (IDs com 'specific_')
                cursor.execute('''
                    SELECT isa.id, isa.name, isa.price, oia.qty FROM order_item_additions oia
                    JOIN item_specific_additions isa ON CAST(REPLACE(oia.addition_id, 'specific_', '') AS INTEGER) = isa.id
                    WHERE oia.order_item_id = ? AND oia.addition_id LIKE 'specific_%'
                ''', (order_item_id,))
                specific_additions_result = cursor.fetchall()

                # Combina os dois resultados
                all_additions_result = additions_result + specific_additions_result

                print(
                    f"\033[91m[DB] Consultando complementos para order_item_id {order_item_id}: {len(all_additions_result)} encontrados\033[0m")
                print(
                    f"\033[91m[DB] Complementos normais: {len(additions_result)}, Específicos: {len(specific_additions_result)}\033[0m")
                print(
                    f"\033[91m[DB] Complementos raw: {all_additions_result}\033[0m")

                additions = []
                for add_id, add_name, add_price, add_qty in all_additions_result:
                    print(
                        f"\033[91m[DB] Processando complemento: id={add_id}, name={add_name}, price={add_price}, qty={add_qty}\033[0m")
                    additions.append(
                        {'id': add_id, 'name': add_name, 'price': add_price, 'qty': add_qty, 'total': add_price * add_qty})

                # Todos obrigatórios do cardápio
                cursor.execute('''
                    SELECT id, name, price FROM item_specific_additions WHERE item_id = ? AND is_mandatory = 1
                ''', (menu_item_id,))
                all_mandatory_additions = []
                for mand_id, mand_name, mand_price in cursor.fetchall():
                    all_mandatory_additions.append(
                        {'id': mand_id, 'name': mand_name, 'price': mand_price})

                # Apenas obrigatórios selecionados para o item do pedido
                mandatory_additions = []
                mandatory_selected = []
                cursor.execute('''
                    SELECT isa.id, isa.name, isa.price
                    FROM order_item_specific_additions oisa
                    JOIN item_specific_additions isa ON oisa.item_specific_addition_id = isa.id
                    WHERE oisa.order_item_id = ?
                ''', (order_item_id,))
                for mand_id, mand_name, mand_price in cursor.fetchall():
                    mandatory_additions.append(
                        {'id': mand_id, 'name': mand_name, 'price': mand_price})
                    mandatory_selected.append(mand_id)

                # Monta item_data igual ao usado na tela
                item_data = [menu_item_id, item_name, unit_price,
                             category_id, category_name, item_description]
                # Lista de IDs dos obrigatórios selecionados (preferencialmente da coluna mandatory_selected)
                if mandatory_selected_str:
                    mandatory_selected = []
                    for mid in mandatory_selected_str.split(','):
                        mid = mid.strip()
                        if mid:
                            # Tenta converter para int se for numérico, senão mantém como string
                            try:
                                mandatory_selected.append(int(mid))
                            except ValueError:
                                # Para IDs com prefixo como "specific_23"
                                mandatory_selected.append(mid)
                else:
                    mandatory_selected = [m['id'] for m in mandatory_additions]
                print(
                    f"\033[92mItem: {item_name}, Mandatory: {mandatory_selected}\033[0m")
                items.append({
                    'menu_item_id': menu_item_id,
                    'qty': quantity,
                    'unit_price': unit_price,
                    'item_data': item_data,
                    'additions': additions,
                    'mandatory_additions': mandatory_additions,
                    'mandatory_selected': mandatory_selected,
                    'all_mandatory_additions': all_mandatory_additions,
                    'observations': observations
                })
            orders.append({
                'customer_id': customer_id,
                'total': total,
                'items': items
            })
        return orders


def get_customer_by_id(customer_id):
    """Retorna um dict com nome e telefone do cliente pelo id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, phone FROM customers WHERE id = ?
        ''', (customer_id,))
        row = cursor.fetchone()
        if row:
            return {'name': row[0], 'phone': row[1], 'id': customer_id}
        return None


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
    """Retorna complementos com informação sobre obrigatoriedade

    Retorna tuplas no formato: (id_unico, name, price, is_mandatory, source_type)
    - Para complementos de categoria: id_unico = id (int)
    - Para complementos específicos: id_unico = f"specific_{id}"
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            result_additions = []

            # Complementos de categoria e vinculados ao item
            cursor.execute('''
                SELECT DISTINCT a.id, a.name, a.price, 
                       COALESCE(ial.is_mandatory, 0) as is_mandatory
                FROM additions a
                LEFT JOIN category_addition_link cal ON a.id = cal.addition_id
                LEFT JOIN item_addition_link ial ON a.id = ial.addition_id AND ial.item_id = ?
                WHERE cal.category_id = ? OR ial.item_id = ?
                ORDER BY is_mandatory DESC, a.name
            ''', (item_id, category_id, item_id))
            additions = cursor.fetchall()

            # Adiciona complementos de categoria com ID original (int)
            for add_id, name, price, is_mandatory in additions:
                result_additions.append(
                    (add_id, name, price, is_mandatory, 'category'))

            # Complementos específicos do item
            cursor.execute('''
                SELECT id, name, price, is_mandatory
                FROM item_specific_additions
                WHERE item_id = ?
                ORDER BY is_mandatory DESC, name
            ''', (item_id,))
            specific_additions = cursor.fetchall()

            # Adiciona complementos específicos com ID prefixado
            for spec_id, name, price, is_mandatory in specific_additions:
                unique_id = f"specific_{spec_id}"
                result_additions.append(
                    (unique_id, name, price, is_mandatory, 'specific'))

        return result_additions
    except Exception as e:
        LOGGER.error(f"Erro na consulta de complementos: {e}")
        return []  # Retorna lista vazia em caso de erro


def parse_addition_id(unique_id):
    """
    Converte ID único para (real_id, source_type)

    Args:
        unique_id: int para categoria, "specific_N" para específicos

    Returns:
        tuple: (real_id, source_type) onde source_type é 'category' ou 'specific'
    """
    if isinstance(unique_id, str) and unique_id.startswith('specific_'):
        try:
            real_id = int(unique_id.split('_')[1])
            return real_id, 'specific'
        except (ValueError, IndexError):
            raise ValueError(f"ID específico inválido: {unique_id}")
    elif isinstance(unique_id, int):
        return unique_id, 'category'
    else:
        raise ValueError(f"Formato de ID inválido: {unique_id}")


def format_addition_id(real_id, source_type):
    """
    Converte (real_id, source_type) para ID único

    Args:
        real_id: ID real na tabela
        source_type: 'category' ou 'specific'

    Returns:
        ID único (int para categoria, "specific_N" para específicos)
    """
    if source_type == 'specific':
        return f"specific_{real_id}"
    elif source_type == 'category':
        return real_id
    else:
        raise ValueError(f"Tipo de fonte inválido: {source_type}")


def get_item_specific_additions(item_id):
    """Retorna os complementos específicos de um item com informação de obrigatoriedade"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, price, COALESCE(is_mandatory, 0) FROM item_specific_additions WHERE item_id = ?',
            (item_id,)
        )
        return cursor.fetchall()


def update_item_specific_addition(addition_id, name, price, is_mandatory=None):
    """Atualiza um complemento específico mantendo o ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if is_mandatory is not None:
            cursor.execute(
                'UPDATE item_specific_additions SET name = ?, price = ?, is_mandatory = ? WHERE id = ?',
                (name, price, int(is_mandatory), addition_id)
            )
        else:
            cursor.execute(
                'UPDATE item_specific_additions SET name = ?, price = ? WHERE id = ?',
                (name, price, addition_id)
            )
        conn.commit()


def delete_item_specific_addition(addition_id):
    """Remove um complemento específico por ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM item_specific_additions WHERE id = ?', (addition_id,)
        )
        conn.commit()


def add_item_specific_addition_single(item_id, name, price, is_mandatory=False):
    """Adiciona um único complemento específico para um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO item_specific_additions (item_id, name, price, is_mandatory) VALUES (?, ?, ?, ?)',
            (item_id, name, price, int(is_mandatory))
        )
        addition_id = cursor.lastrowid
        conn.commit()
        return addition_id


def set_item_specific_additions(item_id, additions_data):
    """Define os complementos específicos de um item
    additions_data: lista de dicionários com 'name', 'price', 'is_mandatory' e opcionalmente 'id'
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Busca IDs existentes
        cursor.execute(
            'SELECT id FROM item_specific_additions WHERE item_id = ?', (
                item_id,)
        )
        existing_ids = {row[0] for row in cursor.fetchall()}

        # IDs que serão mantidos/atualizados
        updated_ids = set()

        for addition in additions_data:
            if 'id' in addition and addition['id'] and addition['id'] in existing_ids:
                # Atualiza existente
                cursor.execute(
                    'UPDATE item_specific_additions SET name = ?, price = ?, is_mandatory = ? WHERE id = ?',
                    (addition['name'], addition['price'], int(
                        addition.get('is_mandatory', False)), addition['id'])
                )
                updated_ids.add(addition['id'])
            else:
                # Adiciona novo
                cursor.execute(
                    'INSERT INTO item_specific_additions (item_id, name, price, is_mandatory) VALUES (?, ?, ?, ?)',
                    (item_id, addition['name'], addition['price'], int(
                        addition.get('is_mandatory', False)))
                )

        # Remove os que não estão na lista
        ids_to_remove = existing_ids - updated_ids
        for id_to_remove in ids_to_remove:
            cursor.execute(
                'DELETE FROM item_specific_additions WHERE id = ?', (
                    id_to_remove,)
            )

        conn.commit()


def save_order(customer_id, items_data, total_amount, notes=""):
    """Salva um pedido no banco de dados"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Cria o pedido
        import datetime
        order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO orders (customer_id, order_date, total_amount, notes)
            VALUES (?, ?, ?, ?)
        ''', (customer_id, order_date, total_amount, notes))

        order_id = cursor.lastrowid

        # Adiciona os itens do pedido
        for item_data in items_data:
            mandatory_selected_str = None
            if 'mandatory_selected' in item_data and item_data['mandatory_selected']:
                mandatory_selected_str = ','.join(
                    str(mid) for mid in item_data['mandatory_selected'])
            observations = item_data.get('observations', '')
            cursor.execute('''
                INSERT INTO order_items
                (order_id, menu_item_id, quantity, unit_price, mandatory_selected, observations)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, item_data['menu_item_id'],
                  item_data['quantity'], item_data['unit_price'], mandatory_selected_str, observations))

            order_item_id = cursor.lastrowid

            # Adiciona os adicionais do item, agora com quantidade
            additions = item_data.get('additions', [])
            for add in additions:
                addition_id = add.get('id') if isinstance(add, dict) else add
                qty = add.get('qty', 1) if isinstance(add, dict) else 1
                cursor.execute('''
                        INSERT INTO order_item_additions
                        (order_item_id, addition_id, qty)
                        VALUES (?, ?, ?)
                    ''', (order_item_id, addition_id, qty))

        conn.commit()
        return order_id


def set_item_mandatory_additions(item_id, addition_ids):
    """Define quais complementos são obrigatórios para um item específico"""
    from utils.log_utils import get_logger
    logger = get_logger(__name__)

    logger.info(
        f"🔧 DB_SET_MANDATORY: Iniciando para item {item_id}, IDs: {addition_ids}")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Log estado ANTES das alterações
        cursor.execute(
            'SELECT addition_id, is_mandatory FROM item_addition_link WHERE item_id = ?', (item_id,))
        before_links = cursor.fetchall()
        logger.info(f"🔧 DB_SET_MANDATORY: Links ANTES: {before_links}")

        # PRIMEIRO: Garante que todos os addition_ids tenham vínculos criados
        if addition_ids:
            for add_id in addition_ids:
                cursor.execute(
                    'INSERT OR IGNORE INTO item_addition_link (item_id, addition_id, is_mandatory) VALUES (?, ?, ?)',
                    (item_id, add_id, 0))
            logger.info(
                f"🔧 DB_SET_MANDATORY: Vínculos garantidos para IDs: {addition_ids}")

        # Atualiza o campo is_mandatory para todos os complementos do item
        logger.info(
            f"🔧 DB_SET_MANDATORY: Zerando is_mandatory para todos os links do item {item_id}")
        cursor.execute(
            'UPDATE item_addition_link SET is_mandatory = 0 WHERE item_id = ?', (item_id,))
        affected_rows = cursor.rowcount
        logger.info(
            f"🔧 DB_SET_MANDATORY: {affected_rows} linhas afetadas pelo zerando")

        # Marca os complementos selecionados como obrigatórios
        if addition_ids:
            logger.info(
                f"🔧 DB_SET_MANDATORY: Marcando {len(addition_ids)} complementos como obrigatórios")
            placeholders = ','.join(['?' for _ in addition_ids])
            query = f'UPDATE item_addition_link SET is_mandatory = 1 WHERE item_id = ? AND addition_id IN ({placeholders})'
            params = [item_id] + addition_ids
            logger.info(f"🔧 DB_SET_MANDATORY: Query: {query}")
            logger.info(f"🔧 DB_SET_MANDATORY: Params: {params}")
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            logger.info(
                f"🔧 DB_SET_MANDATORY: {affected_rows} linhas marcadas como obrigatórias")

            # Verifica se todas foram marcadas corretamente
            if affected_rows != len(addition_ids):
                logger.warning(
                    f"🔧 DB_SET_MANDATORY: AVISO - Esperado {len(addition_ids)} linhas, mas {affected_rows} foram afetadas")
        else:
            logger.info(
                f"🔧 DB_SET_MANDATORY: Nenhum complemento para marcar como obrigatório")

        # Log estado DEPOIS das alterações
        cursor.execute(
            'SELECT addition_id, is_mandatory FROM item_addition_link WHERE item_id = ?', (item_id,))
        after_links = cursor.fetchall()
        logger.info(f"🔧 DB_SET_MANDATORY: Links DEPOIS: {after_links}")

        conn.commit()
        logger.info(
            f"🔧 DB_SET_MANDATORY: Commit executado para item {item_id}")


def set_item_specific_mandatory_additions(item_id, specific_addition_ids):
    """Define quais complementos específicos são obrigatórios para um item"""
    from utils.log_utils import get_logger
    logger = get_logger(__name__)

    logger.info(
        f"🔧 DB_SET_SPECIFIC: Iniciando para item {item_id}, IDs: {specific_addition_ids}")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Log estado ANTES das alterações
        cursor.execute(
            'SELECT id, name, is_mandatory FROM item_specific_additions WHERE item_id = ?', (item_id,))
        before_specifics = cursor.fetchall()
        logger.info(
            f"🔧 DB_SET_SPECIFIC: Específicos ANTES: {before_specifics}")

        # Atualiza o campo is_mandatory para todos os complementos específicos do item
        logger.info(
            f"🔧 DB_SET_SPECIFIC: Zerando is_mandatory para todos os específicos do item {item_id}")
        cursor.execute(
            'UPDATE item_specific_additions SET is_mandatory = 0 WHERE item_id = ?', (item_id,))
        affected_rows = cursor.rowcount
        logger.info(
            f"🔧 DB_SET_SPECIFIC: {affected_rows} linhas afetadas pelo zerando")

        # Marca os complementos específicos selecionados como obrigatórios
        if specific_addition_ids:
            logger.info(
                f"🔧 DB_SET_SPECIFIC: Marcando {len(specific_addition_ids)} específicos como obrigatórios")
            placeholders = ','.join(['?' for _ in specific_addition_ids])
            query = f'UPDATE item_specific_additions SET is_mandatory = 1 WHERE item_id = ? AND id IN ({placeholders})'
            params = [item_id] + specific_addition_ids
            logger.info(f"🔧 DB_SET_SPECIFIC: Query: {query}")
            logger.info(f"🔧 DB_SET_SPECIFIC: Params: {params}")
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            logger.info(
                f"🔧 DB_SET_SPECIFIC: {affected_rows} linhas marcadas como obrigatórias")
        else:
            logger.info(
                f"🔧 DB_SET_SPECIFIC: Nenhum específico para marcar como obrigatório")

        # Log estado DEPOIS das alterações
        cursor.execute(
            'SELECT id, name, is_mandatory FROM item_specific_additions WHERE item_id = ?', (item_id,))
        after_specifics = cursor.fetchall()
        logger.info(
            f"🔧 DB_SET_SPECIFIC: Específicos DEPOIS: {after_specifics}")

        conn.commit()
        logger.info(f"🔧 DB_SET_SPECIFIC: Commit executado para item {item_id}")


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


def add_item_specific_addition(item_id, name, price, is_mandatory=False):
    """Adiciona um complemento específico para um item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO item_specific_additions (item_id, name, price, is_mandatory) VALUES (?, ?, ?, ?)',
                (item_id, name, price, int(is_mandatory))
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
            SELECT isa.id, isa.name, isa.price, 
                   COALESCE(isa.is_mandatory, 0) as is_mandatory, 
                   'item_specific' as source
            FROM item_specific_additions isa
            WHERE isa.item_id = ?
        ''', (item_id,))
        item_specific_additions = cursor.fetchall()

        # Combina os resultados
        all_additions = list(category_additions) + \
            list(item_specific_additions)
        return all_additions


# Funções para configurações do sistema
def get_system_setting(key, default_value=None):
    """Obtém uma configuração do sistema pelo nome da chave"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT setting_value FROM system_settings WHERE setting_key = ?',
            (key,)
        )
        result = cursor.fetchone()
        return result[0] if result else default_value


def set_system_setting(key, value):
    """Define ou atualiza uma configuração do sistema"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, str(value)))
        conn.commit()


def get_all_system_settings():
    """Retorna todas as configurações do sistema"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT setting_key, setting_value FROM system_settings'
        )
        return dict(cursor.fetchall())
