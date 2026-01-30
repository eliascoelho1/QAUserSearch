---
mode: agent
description: Cria PR automaticamente com análise de commits, testes e checklist inteligente
---

## Comando /create-pr - Criação Automatizada de Pull Request

Automatize a criação de Pull Requests no GitHub com análise inteligente de commits, execução de testes obrigatória e checklist contextual.

**Todas as mensagens devem ser em Português Brasileiro.**

## Fase 1: Validação de Pré-requisitos

Valide o ambiente executando os seguintes comandos em paralelo:

```bash
# Verificar gh CLI
which gh

# Verificar autenticação
gh auth status

# Verificar repositório git
git rev-parse --git-dir

# Verificar alterações não commitadas
git status --porcelain
```

**Tratamento de Erros (Fail Fast):**

- Se `which gh` falhar:
  ```
  ❌ Erro: gh CLI não instalado.

  Instale com:
  - Ubuntu/Debian: sudo apt install gh
  - macOS: brew install gh
  - Outros: https://cli.github.com/
  ```

- Se `gh auth status` falhar:
  ```
  ❌ Erro: gh CLI não autenticado.

  Execute: gh auth login
  ```

- Se `git status --porcelain` retornar qualquer saída:
  ```
  ❌ Erro: Há alterações não commitadas.

  Execute:
  - git status (para ver as alterações)
  - git add . && git commit -m "mensagem" (para commitar)
  ```

**IMPORTANTE:** Se qualquer validação falhar, PARE IMEDIATAMENTE com a mensagem de erro apropriada.

## Fase 2: Execução de Testes e Linting

Execute sequencialmente (política de zero warnings):

```bash
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
```

**Tratamento de Erros:**

- Se `uv run pytest` falhar:
  ```
  ❌ Erro: Testes falharam.

  Corrija os erros de teste antes de criar o PR.
  Execute: uv run pytest
  ```

- Se `uv run ruff check` falhar:
  ```
  ❌ Erro: Ruff encontrou problemas de linting.

  Corrija os problemas ou execute: uv run ruff check src/ tests/ --fix
  ```

- Se `uv run mypy src/` falhar:
  ```
  ❌ Erro: MyPy encontrou erros de tipagem.

  Corrija os erros de tipo antes de criar o PR.
  Execute: uv run mypy src/
  ```

## Fase 3: Detecção da Branch Base

Detecte a branch principal do repositório:

```bash
# Método 1: Detectar branch padrão do remote
git remote show origin | grep "HEAD branch" | cut -d: -f2 | xargs

# Se falhar, use fallback:
# Verificar se main existe
git show-ref --verify --quiet refs/remotes/origin/main

# Se não, verificar master
git show-ref --verify --quiet refs/remotes/origin/master
```

Após detectar a branch base:
1. Armazene o nome (main ou master)
2. Obtenha a branch atual: `git branch --show-current`
3. Valide que branch atual ≠ branch base

**Se estiver na branch base:**
```
❌ Erro: Você está na branch base (<branch-name>). Crie uma feature branch primeiro.
```

**Sucesso:**
```
✅ Branch base detectada: <base-branch>
✅ Branch atual: <current-branch>
```

## Fase 4: Análise de Commits e Mudanças

Colete informações sobre as mudanças:

```bash
# Contar commits
git log <base-branch>..HEAD --oneline | wc -l

# Obter mensagens de commits
git log <base-branch>..HEAD --format="%s"

# Obter arquivos modificados
git diff --name-only <base-branch>...HEAD

# Obter estatísticas
git diff <base-branch>...HEAD --stat
```

**Validação:** Se não houver commits (count = 0):
```
❌ Erro: Nenhum commit novo em relação a <base-branch>
```

## Fase 5: Geração do Título do PR

**Lógica de Geração:**

**Se houver APENAS 1 commit:**
- Use a mensagem do commit exata como título do PR

**Se houver MÚLTIPLOS commits:**
1. Analise as mensagens de commit para identificar tipos conventional commits
2. Conte quantos commits de cada tipo: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`
3. Use o tipo mais frequente como base
4. Extraia o escopo do commit mais recente (se houver)
5. Sintetize uma descrição clara que englobe as mudanças principais

**Exemplo de análise:**
```bash
# Commits:
# "feat(design-system): add Button component"
# "feat(design-system): add Button stories"
# "test(design-system): add Button tests"

# Tipo dominante: feat (3 ocorrências)
# Escopo: design-system (do último commit)
# Título sintetizado: "feat(design-system): add Button component with stories and tests"
```

**IMPORTANTE:** Você DEVE analisar os commits e sintetizar um título claro e descritivo. Não use placeholders genéricos.

**Formato:** Seguir conventional commits: `tipo(escopo): descrição`

## Fase 6: Geração da Descrição do PR

Crie a descrição com 3 seções:

### 6.1 Seção de Resumo

Analise os commits, diff e arquivos modificados para criar 2-3 bullets explicando:
- **O QUE** foi mudado (tecnicamente)
- **POR QUE** foi mudado (contexto/motivação)

**Formato:**
```markdown
## Resumo
- [Bullet point 1 explicando mudança principal]
- [Bullet point 2 explicando outra mudança]
- [Bullet point 3 se necessário]
```

**Exemplo:**
```markdown
## Resumo
- Adiciona componente Button com variantes default, destructive, outline, ghost e link
- Implementa sistema de tipagem estrita usando useTheme hook para tokens do design system
- Inclui testes Jest e stories Storybook para todas as variantes com validação dark/light
```

### 6.2 Seção de Checklist Inteligente

Gere checklist baseado nos arquivos modificados.

**Base (sempre incluir):**
```markdown
## Checklist
- [x] ✅ Testes passando (uv run pytest)
- [x] ✅ Linting passando (uv run ruff check)
- [x] ✅ Tipagem verificada (uv run mypy src/)
```

**Condicional (adicione baseado em padrões):**

| Se arquivos modificados contêm | Adicione ao checklist |
|-------------------------------|----------------------|
| `src/api/` | `- [ ] ✅ Endpoints documentados com docstrings e schemas Pydantic` |
| `src/models/` | `- [ ] ✅ Migrations do Alembic criadas/atualizadas se necessário` |
| `src/schemas/` | `- [ ] ✅ Schemas Pydantic com validações apropriadas` |
| `src/services/` | `- [ ] ✅ Lógica de negócio com tratamento de erros adequado` |
| `src/repositories/` | `- [ ] ✅ Repositórios seguem padrão async com SQLAlchemy` |
| `src/core/` | `- [ ] ✅ Componentes cross-cutting documentados` |
| `tests/` | `- [ ] ✅ Cobertura de testes adequada (novos testes adicionados)` |
| `alembic/` | `- [ ] ✅ Migrations testadas e reversíveis` |
| `*.py` | `- [ ] ✅ Tipagem Python estrita mantida (sem Any implícito)` |

### 6.3 Seção de Footer

Adicione o footer padrão:
```markdown

🤖 Gerado com [Claude Code](https://claude.com/claude-code)
```

## Fase 7: Push e Criação do PR

Execute sequencialmente:

```bash
# Verificar se branch tem remote tracking
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null

# Se o comando acima falhar (sem tracking):
git push -u origin <current-branch>

# Se já tiver tracking:
git push
```

Após push, crie o PR usando HEREDOC para evitar problemas com quotes:

```bash
gh pr create --title "<título-gerado>" --body "$(cat <<'EOF'
<conteúdo-da-descrição-completa-gerada-nas-fases-6.1-6.2-6.3>
EOF
)"
```

**IMPORTANTE:** Substitua `<título-gerado>` e `<conteúdo-da-descrição-completa-gerada-nas-fases-6.1-6.2-6.3>` pelos valores reais gerados.

## Fase 8: Confirmação e Retorno

Após criação bem-sucedida do PR:

```bash
# Obter URL do PR
gh pr view --json url -q .url
```

Exiba mensagem de sucesso em PT-BR:
```
✅ Pull Request criado com sucesso!
🔗 URL: <url-do-pr>

📋 Próximos passos:
  1. Revise o PR no GitHub
  2. Preencha os itens pendentes do checklist
  3. Solicite revisão dos colaboradores
```

## Princípios de Execução

1. **Fail Fast:** Ao primeiro erro, pare imediatamente e exiba mensagem clara em PT-BR
2. **Validação Estrita:** Testes e lint devem passar (política de zero warnings)
3. **Análise Inteligente:** Sintetize informações dos commits, não apenas copie
4. **Checklist Contextual:** Adicione apenas itens relevantes aos arquivos modificados
5. **Conventional Commits:** Mantenha formato tipo(escopo): descrição
6. **Portuguese Output:** Todas as mensagens ao usuário em PT-BR

## Referências

- Projeto: `PROJECT.md`
- Conventional Commits: https://www.conventionalcommits.org/
- Arquitetura: `docs/architecture.md`