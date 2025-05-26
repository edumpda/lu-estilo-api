# Lu Estilo API

API de gerenciamento para loja de roupas Lu Estilo, desenvolvida com FastAPI, PostgreSQL, SQLAlchemy e JWT.

## Funcionalidades

- **Autenticação e Autorização**: Sistema completo com JWT, registro e login de usuários
- **Gerenciamento de Clientes**: CRUD completo com validações de dados
- **Gerenciamento de Produtos**: CRUD completo com controle de estoque
- **Gerenciamento de Pedidos**: Sistema completo com itens, status e validação de estoque
- **Integração com WhatsApp**: Notificações automáticas para clientes

## Requisitos

- Python
- PostgreSQL
- Docker e Docker Compose

## Configuração e Execução

### Usando Docker (Recomendado)

1. Clone o repositório
2. Configure as variáveis de ambiente no arquivo `.env` (use `.env.example` como base)
3. Execute com Docker Compose:

```bash
docker-compose up -d
```

A API estará disponível em `http://localhost:8000`, documentação em `http://localhost:8000/api/docs` e documentação de ReDoc em `http://localhost:8000/api/redoc`.

### Instalação Manual

1. Clone o repositório
2. Crie um ambiente virtual e ative-o:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente no arquivo `.env`
5. Execute as migrações do banco de dados:

```bash
alembic upgrade head
```

6. Inicie o servidor:

```bash
uvicorn src.main:app --reload
```

## Estrutura do Projeto

```
lu_estilo_api/
├── alembic/              # Migrações de banco de dados
├── src/                  # Código fonte principal
│   ├── auth/             # Autenticação e autorização
│   ├── clients/          # Endpoints de clientes
│   ├── core/             # Configurações e utilitários
│   ├── models/           # Modelos SQLAlchemy
│   ├── orders/           # Endpoints de pedidos
│   ├── products/         # Endpoints de produtos
│   ├── schemas/          # Schemas Pydantic
│   ├── services/         # Lógica de negócio
│   └── main.py           # Ponto de entrada da aplicação
├── static/               # Arquivos estáticos (imagens)
├── tests/                # Testes automatizados
├── .env                  # Variáveis de ambiente
├── docker-compose.yml    # Configuração Docker Compose
├── Dockerfile            # Configuração Docker
└── requirements.txt      # Dependências Python
```

## Endpoints da API

### Autenticação

- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Login e obtenção de token JWT

### Clientes

- `GET /clients` - Listar clientes (com paginação e filtros)
- `POST /clients` - Criar cliente
- `GET /clients/{id}` - Obter cliente específico
- `PUT /clients/{id}` - Atualizar cliente
- `DELETE /clients/{id}` - Excluir cliente

### Produtos

- `GET /products` - Listar produtos (com paginação e filtros)
- `POST /products` - Criar produto
- `GET /products/{id}` - Obter produto específico
- `PUT /products/{id}` - Atualizar produto
- `DELETE /products/{id}` - Excluir produto

### Pedidos

- `GET /orders` - Listar pedidos (com filtros)
- `POST /orders` - Criar pedido
- `GET /orders/{id}` - Obter pedido específico
- `PUT /orders/{id}` - Atualizar pedido (status)
- `DELETE /orders/{id}` - Excluir pedido

## Testes da Aplicação (46 testes)

### Autenticação (6 testes)
- Registro de novo usuário
- Tentativa de registro com e-mail existente
- Login bem-sucedido
- Login com senha incorreta
- Login com usuário inexistente
- Atualização de token (não implementado)

### Clientes (13 testes)
- Criação de cliente
- Tentativa de criar cliente com e-mail duplicado
- Tentativa de criar cliente com CPF duplicado
- Validação de formato de CPF inválido
- Listagem de clientes
- Filtragem de clientes
- Busca de cliente específico
- Busca de cliente inexistente
- Atualização de dados do cliente
- Conflito de e-mail ao atualizar
- Atualização de cliente inexistente
- Exclusão de cliente
- Tentativa de excluir cliente inexistente

### Pedidos (13 testes)
- Criação de pedido
- Tentativa de criar pedido com estoque insuficiente
- Tentativa de criar pedido com produto inexistente
- Tentativa de criar pedido com cliente inexistente
- Listagem de pedidos
- Filtragem de pedidos
- Busca de pedido específico
- Busca de pedido inexistente
- Atualização de status do pedido
- Tentativa de atualizar status sem ser admin
- Atualização de pedido inexistente
- Exclusão de pedido
- Tentativa de exclusão sem ser admin
- Tentativa de excluir pedido inexistente

### Produtos (14 testes)
- Criação de produto
- Tentativa de criar produto sem ser admin
- Validação de dados inválidos
- Listagem de produtos
- Filtragem de produtos
- Busca de produto específico
- Busca de produto inexistente
- Atualização de produto
- Tentativa de atualizar sem ser admin
- Atualização de produto inexistente
- Exclusão de produto
- Tentativa de exclusão sem ser admin
- Tentativa de excluir produto inexistente

## Testes

Execute os testes automatizados com:

**Testes Unitários via Docker:**
```bash
docker-compose exec api pytest
```

**Testes Unitários via Docker com Coverage:**
```bash
docker-compose exec api pytest --cov=src --cov-report=term-missing
```

**Testes Unitários via Docker com Logging:**
```bash
docker-compose exec api pytest -v --log-cli-level=INFO
```

ou

**Testes Unitários via Python (Deve ser usado quando instalado manualmente):**    
```bash
pytest
```

## Integração com WhatsApp

A API inclui integração com WhatsApp via Twilio para notificações automáticas:

- Confirmação de pedidos
- Atualizações de status
- Promoções e novidades

Para configurar, adicione suas credenciais Twilio no arquivo `.env`.

## Futuras Implementações

* **Relatórios Automatizados (Airflow):** Pipeline ETL para extrair dados do PostgreSQL, transformar com Pandas e enviar relatórios de vendas.
* **Chatbot Inteligente (GroqCloud):** Endpoint FastAPI para receber perguntas, contextualizar com dados da API (produtos/pedidos do PostgreSQL) e obter respostas rápidas de um LLM via GroqCloud para atendimento ao cliente.

## Documentação da API

A documentação interativa está disponível em:

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`

## Licença

Este projeto está licenciado sob a licença MIT.
