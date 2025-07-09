# AnotaJá 📋

Sistema de gerenciamento de cardápio e pedidos desenvolvido em Python com PySide6.

## 🚀 Funcionalidades

- **Gerenciamento de Cardápio**: Cadastro de categorias, itens e adicionais
- **Gerenciamento de Clientes**: Cadastro completo com endereço e histórico
- **Gerenciamento de Bairros**: Controle de taxas de entrega por região
- **Sistema de Pedidos**: Criação e acompanhamento de pedidos
- **Busca Avançada**: Pesquisa por nome, telefone e endereço
- **Impressão**: Suporte para impressão de pedidos

## 📁 Estrutura do Projeto

```
AnotaJá/
├── main.py                    # Arquivo principal
├── requirements.txt           # Dependências
├── database/                  # Gerenciamento do banco de dados
│   └── db.py                 # Funções CRUD e conexão SQLite
├── ui/                       # Interface gráfica
│   ├── customer_management.py # Tela de clientes
│   ├── neighborhood_management.py # Tela de bairros
│   ├── menu_registration.py  # Cadastro de cardápio
│   ├── menu_edit.py          # Edição de cardápio
│   └── dialogs.py            # Diálogos diversos
├── utils/                    # Utilitários
│   ├── printer.py            # Funções de impressão
│   ├── log_utils.py          # Sistema de logs
│   └── firebase_sync.py      # Sincronização (opcional)
└── data/                     # Arquivos de dados
    ├── menu.db               # Banco SQLite
    └── anotaja.log           # Arquivo de log
```

## 🛠️ Instalação

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd AnotaJa
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Como Usar

1. **Execute o aplicativo**:
   ```bash
   python main.py
   ```

2. **Menu Principal**:
   - **Cardápio**: Cadastre categorias, itens e adicionais
   - **Cliente**: Gerencie clientes e bairros
   - **Ajustes**: Configure impressora

3. **Primeiros Passos**:
   - Cadastre bairros e suas taxas de entrega
   - Adicione categorias ao cardápio
   - Cadastre itens do cardápio
   - Registre clientes
   - Comece a fazer pedidos!

## 🗃️ Banco de Dados

O sistema usa SQLite e cria automaticamente as seguintes tabelas:
- `categories`: Categorias do cardápio
- `menu_items`: Itens do cardápio
- `additions`: Adicionais disponíveis
- `customers`: Dados dos clientes
- `neighborhoods`: Bairros e taxas de entrega
- `orders`: Pedidos realizados
