# Objetivo do Projeto
Desenvolver uma aplicação que facilite a busca de massas de usuários no ambiente de QA, em nossas bases de dados. A aplicação deve permitir que os usuários encontrem rapidamente massas de usuários relevantes para seus testes. 

## Front-end

### Opção 1: HubAI
**Pros:**
1. Entrega mais rápida e com mais pessoas atingidas.
   
**Contras:**
1. Reduz a possibilidade de features possíveis.
2. A UX é limitada a uma interface de chat.


### Opção 2: CLI
**Pros:**
1. Atinge o público técnico.

### Opçao 3: React Native


## Funcionalidades

1. Busca por cenários específicos (ex: "usuários com cartão de crédito ativo e fatura aberta").
2. Garante a autenticação integrando com o sistema de login.
3. Permite a exportação dos dados em formatos comuns (CSV, JSON).
4. Interface amigável para facilitar a navegação e busca.
5. Classificação das massas por filtro rápido (ex: "cartão de crédito", "empréstimo", "investimentos").
Um filtro rápido equivale a uma query pré-definida para facilitar a busca.
6. Os filtros rápidos são públicos e podem ser criados por qualquer usuário.
7. Sistema de criação de queries dinâmicas com base em prompts fornecidos pelos usuários.
8. Histórico de buscas para facilitar buscas recorrentes.
9. Permitir que os usuários avaliem a qualidade das massas encontradas.

# Casos de uso

## Consultando a partir de um prompt

1. "Preciso de um usuário com cartão de crédito ativo e fatura aberta."
2. Encontrar massas bases (ativas e com cartão de crédito).
3. IA: Criar uma query para fazer o filtro por fatura aberta.
4. Executar a query gerada pela IA.
5. Retornar os resultados encontrados.
6. Salvar essa query como um filtro rápido chamado "Cartão de crédito com fatura aberta".