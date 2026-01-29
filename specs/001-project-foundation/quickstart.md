# Quickstart: QAUserSearch

Guia rápido para configurar e executar o projeto QAUserSearch localmente.

**Tempo estimado**: < 15 minutos

---

## Pré-requisitos

- **Python 3.11+** ([download](https://python.org/downloads/))
- **Docker e Docker Compose** ([download](https://docker.com/get-started/))
- **Git** para clonar o repositório

### Verificar instalação

```bash
python --version   # Python 3.11.x
docker --version   # Docker 24.x ou superior
docker compose version  # Docker Compose v2.x
```

---

## Setup Rápido (Recomendado)

### 1. Clone o repositório

```bash
git clone <repo-url>
cd QAUserSearch
```

### 2. Copie o arquivo de ambiente

```bash
cp .env.example .env
```

### 3. Inicie os serviços com Docker Compose

```bash
docker compose up -d
```

Isso irá:
- Criar e iniciar o PostgreSQL local
- Criar e iniciar a aplicação QAUserSearch
- Expor a API em `http://localhost:8000`

### 4. Verifique se está funcionando

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": [...]
}
```

### 5. Acesse a documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Setup para Desenvolvimento

Se você pretende modificar o código, siga estes passos adicionais:

### 1. Crie um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows
```

### 2. Instale as dependências

```bash
pip install -e ".[dev]"
```

### 3. Inicie apenas o PostgreSQL

```bash
docker compose up -d db
```

### 4. Execute a aplicação em modo de desenvolvimento

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

O flag `--reload` reinicia automaticamente quando você modifica o código.

---

## Comandos Úteis

### Executar testes

```bash
pytest                          # Todos os testes
pytest tests/unit/              # Apenas testes unitários
pytest --cov=src --cov-report=html  # Com cobertura
```

### Verificar linting

```bash
ruff check src/ tests/          # Verificar problemas
ruff check src/ tests/ --fix    # Corrigir automaticamente
```

### Formatar código

```bash
black src/ tests/               # Formatar todos os arquivos
```

### Executar migrations (quando houver)

```bash
alembic upgrade head            # Aplicar migrations pendentes
alembic revision --autogenerate -m "descrição"  # Criar nova migration
```

### Logs da aplicação

```bash
docker compose logs -f app      # Seguir logs do container
```

---

## Variáveis de Ambiente

| Variável | Descrição | Obrigatório | Padrão |
|----------|-----------|-------------|--------|
| `DATABASE_URL` | URL do PostgreSQL da aplicação | Sim | - |
| `ENVIRONMENT` | Ambiente (development/staging/production) | Não | development |
| `DEBUG` | Modo debug | Não | false |
| `LOG_LEVEL` | Nível de log (DEBUG/INFO/WARNING/ERROR) | Não | INFO |

Veja `.env.example` para todos os valores de referência.

---

## Troubleshooting

### Erro: "Connection refused" ao acessar banco

```bash
# Verifique se o container do PostgreSQL está rodando
docker compose ps

# Se não estiver, reinicie
docker compose down && docker compose up -d
```

### Erro: "Port 8000 already in use"

```bash
# Encontre o processo usando a porta
lsof -i :8000

# Mate o processo ou use outra porta
uvicorn src.main:app --port 8001
```

### Testes falhando por timeout de banco

```bash
# Aguarde o banco inicializar completamente
docker compose logs db | grep "ready to accept connections"
```

---

## Próximos Passos

Após o setup inicial:

1. Leia a documentação de arquitetura em `/docs/architecture.md`
2. Explore os endpoints via Swagger UI
3. Execute os testes para garantir que tudo funciona
4. Comece a desenvolver seguindo o ciclo TDD (Red-Green-Refactor)

---

## Suporte

- Problemas com setup? Abra uma issue no repositório
- Dúvidas sobre arquitetura? Consulte `/docs/architecture.md`
- Contribuições? Leia `CONTRIBUTING.md` (quando disponível)
