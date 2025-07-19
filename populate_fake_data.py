"""
Script para popular o banco de dados com dados fake para testes.
Execute este arquivo para inserir dados de exemplo no sistema.
"""
from database.db import (
    init_db, add_category, add_addition, add_menu_item, add_customer,
    add_neighborhood, save_order, get_category_id, get_all_additions_with_id, get_menu_items
)

# Inicializa o banco e tabelas
init_db()

# Categorias
categorias = ['Pizza', 'Lanche', 'Bebida']
categoria_ids = {}
for nome in categorias:
    add_category(nome)
    categoria_ids[nome] = get_category_id(nome)

# Adicionais
adicionais = [
    ('Queijo Extra', 3.0),
    ('Bacon', 4.0),
    ('Catupiry', 3.5),
    ('Refrigerante Lata', 5.0),
    ('Batata Frita', 7.0)
]
adicional_ids = []
for nome, preco in adicionais:
    adicional_ids.append(add_addition(nome, preco))

# Bairros
bairros = [
    ('Centro', 5.0),
    ('Jardim das Flores', 7.0),
    ('Vila Nova', 6.0)
]
bairro_ids = []
for nome, taxa in bairros:
    bairro_ids.append(add_neighborhood(nome, taxa))

# Clientes
clientes = [
    ('João Silva', '11999990001', 'Rua A', '100', 1, 'Próx. padaria'),
    ('Maria Souza', '11999990002', 'Rua B', '200', 2, 'Casa azul'),
    ('Carlos Lima', '11999990003', 'Rua C', '300', 3, 'Portão verde')
]
cliente_ids = []
for nome, telefone, rua, numero, bairro_id, referencia in clientes:
    add_customer(nome, telefone, rua, numero, bairro_id, referencia)

# Itens do cardápio
itens = [
    ('Pizza Calabresa', 35.0, categoria_ids['Pizza'], 'Pizza tradicional de calabresa', [adicional_ids[0], adicional_ids[1]]),
    ('X-Burguer', 18.0, categoria_ids['Lanche'], 'Hambúrguer simples', [adicional_ids[1], adicional_ids[2]]),
    ('Coca-Cola Lata', 6.0, categoria_ids['Bebida'], 'Refrigerante gelado', [adicional_ids[3]]),
    ('Batata Frita', 12.0, categoria_ids['Lanche'], 'Porção de batata frita', [adicional_ids[4]])
]
item_ids = []
for nome, preco, categoria_id, descricao, adicionais_item in itens:
    item_id = add_menu_item(nome, preco, categoria_id, descricao, adicionais_item)
    item_ids.append(item_id)

# Pedidos
pedidos = [
    {
        'customer_id': 1,
        'items_data': [
            {'menu_item_id': item_ids[0], 'quantity': 1, 'unit_price': 35.0, 'additions': [adicional_ids[0]]},
            {'menu_item_id': item_ids[2], 'quantity': 2, 'unit_price': 6.0, 'additions': [adicional_ids[3]]}
        ],
        'total_amount': 47.0,
        'notes': 'Entregar rápido'
    },
    {
        'customer_id': 2,
        'items_data': [
            {'menu_item_id': item_ids[1], 'quantity': 1, 'unit_price': 18.0, 'additions': [adicional_ids[2]]},
            {'menu_item_id': item_ids[3], 'quantity': 1, 'unit_price': 12.0, 'additions': [adicional_ids[4]]}
        ],
        'total_amount': 30.0,
        'notes': 'Sem cebola'
    }
]
for pedido in pedidos:
    save_order(pedido['customer_id'], pedido['items_data'], pedido['total_amount'], pedido['notes'])

print('Dados fake inseridos com sucesso!')
