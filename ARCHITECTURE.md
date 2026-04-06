# Arquitetura Hexagonal - Prompt Gallery

```
┌─────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   SQLite    │  │   Flask     │  │   File System          │ │
│  │ Repository  │  │   Routes    │  │   (Uploads)            │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘ │
│         │                │                                      │
│         ▼                ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              INTERFACE ADAPTERS (Controllers)            │   │
│  │         Converte dados do framework para o domínio      │   │
│  └─────────────────────────┬────────────────────────────────┘   │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    USE CASES                              │   │
│  │  • CreatePromptUseCase    • CopyPromptUseCase            │   │
│  │  • UpdatePromptUseCase    • AnalyticsUseCase             │   │
│  │  • DeletePromptUseCase                                    │   │
│  │                                                           │   │
│  │  Orquestra regras de negócio, independente de frameworks  │   │
│  └─────────────────────────┬────────────────────────────────┘   │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                              │
│  ┌─────────────────────┐        ┌─────────────────────────────┐  │
│  │     ENTITIES        │        │      REPOSITORIES (Ports)  │  │
│  │  • Prompt           │◄──────►│  • PromptRepository        │  │
│  │  • CopyLog          │        │  • CopyLogRepository       │  │
│  │                     │        │                             │  │
│  │  Regras de negócio │        │  Interfaces/Contratos       │  │
│  │  puras, sem deps    │        │  para persistência          │  │
│  └─────────────────────┘        └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Benefícios da Arquitetura

### 1. **Independência de Framework**
O domínio não depende de Flask, pode ser trocado por FastAPI, Django, etc.

### 2. **Independência de Banco de Dados**
SQLite pode ser trocado por PostgreSQL, MongoDB, etc. sem alterar o domínio.

### 3. **Testabilidade**
Use cases podem ser testados com mocks/repositórios em memória.

### 4. **Clean Code**
Cada camada tem responsabilidade única e bem definida.

## 🔄 Como Trocar o Banco de Dados

### Exemplo: Trocar SQLite por PostgreSQL

1. Criar novo adapter:
```python
# infrastructure/postgres_repositories.py
class PostgresPromptRepository(PromptRepository):
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
    # ... implementar métodos
```

2. Trocar no composition root:
```python
# app.py
from infrastructure.postgres_repositories import PostgresPromptRepository

prompt_repo = PostgresPromptRepository(os.environ['DATABASE_URL'])
```

**Pronto!** Todo o resto do código permanece igual.

## 📁 Estrutura de Pastas

```
prompt-gallery-py/
├── domain/              # Regras de negócio puras
│   ├── entities.py      # Entidades (Prompt, CopyLog)
│   └── repositories.py  # Interfaces (Ports)
│
├── application/         # Casos de uso
│   └── use_cases.py     # Orquestração de regras
│
├── infrastructure/      # Implementações concretas
│   └── sqlite_repositories.py  # Adapters SQLite
│
├── interface/           # Adaptadores de interface
│   └── controllers.py   # Controllers Flask
│
└── app.py              # Composition Root (main)
```

## 🚀 Iniciar o Servidor

```bash
python app.py
```

O servidor iniciará na porta 8080 (ou PORT do ambiente).
