# Status e Bloqueios de Conta Cartão

Referência de códigos de status de conta (FIS/Vision Plus) e bloqueios do PicPay Card,
incluindo descrições, tipos e impactos nas transações.

---

## 1. Status de Conta FIS 

Os códigos de status da conta determinam como uma conta é processada. **Não são bloqueios**,
são estados do ciclo de vida da conta.

### Tabela de Status

| Código | Nome | Descrição |
|--------|------|-----------|
| **N** | Nova | Conta incluída no dia |
| **A** | Ativa | Conta com saldo e/ou atividades monetárias desde o último extrato |
| **D** | Dormente | Conta sem movimentação: saldo zero ou abaixo do Bill Thresh, sem atividade adicional |
| **I** | Inativa | Conta migrada para critério de inativa (definido na tela ARQL13) |
| **M** | Migrada | Conta inativa que foi acessada online ou recebeu transação |
| **T** | Transferida | Conta com saldos transferidos para nova conta |
| **F** | Fraude | Conta transferida que recebeu transação (exceto pagamento) após transferência |
| **Z** | Charge-Off | Conta inibida (manual ou automática). Inclui contas em CRELI com bloqueio J |
| **8** | Encerrada | Conta inativa por XX dias. Não aceita transações. Requer: cartões expirados, saldo zero, sem planos |
| **9** | A ser eliminada após recarga | Conta marcada para expurgo do sistema |
| **P** | A ser eliminada na próxima recarga | Conta eliminada aguardando atualização do arquivo |

### Sinônimos e Variações para Busca

- "conta ativa" → status = 'A'
- "conta nova" → status = 'N'
- "conta dormente", "conta sem movimentação" → status = 'D'
- "conta inativa" → status = 'I'
- "conta encerrada", "conta fechada" → status = '8'
- "charge-off", "chargeoff", "conta em creli" → status = 'Z'
- "conta transferida" → status = 'T'
- "conta fraude" → status = 'F'

---

## 2. Bloqueios PicPay Card

Os bloqueios são divididos em dois tipos:
- **Bloqueios de Conta Cartão**: Impactam TODOS os cartões (digital, físico, virtual)
- **Bloqueios de Cartão**: Impactam apenas o cartão específico

### Regra de Prioridade

Bloqueios mais prioritários sobrepõem os menos prioritários. A ordem de prioridade
(do mais para o menos prioritário) é importante para determinar o estado efetivo.

### Tabela de Bloqueios

| Código | Nome | Tipo | Descrição |
|--------|------|------|-----------|
| **(branco)** | Ativo | - | Sem bloqueio, cartão ativo |
| **A** | Atraso até 5 dias | Conta | Atraso de pagamento até 5 dias. Usuário pode transacionar normalmente |
| **B** | Atraso 6-30 dias | Conta | Atraso de 6-30 dias. Bloqueia função crédito. Desbloqueio ao pagar |
| **C** | Cancelamento adicional | Cartão | Usado para cartão adicional/virtual |
| **D** | Devolução correios | Cartão | Não está sendo usado atualmente |
| **E** | Extravio | Cartão | Cancelamento do físico por extravio. Nova via gerada automaticamente |
| **F** | Fraude | Cartão | Cancelamento do físico por fraude. Nova via gerada automaticamente |
| **G** | Substituição | Cartão | Bloqueio automático quando segundo cartão físico é gerado |
| **H** | Acordo | Conta | Acordo com assessoria. Bloqueia crédito. Desbloqueio após quitação |
| **I** | SPC | Conta | Atraso de 31-60 dias. Bloqueia crédito. Desbloqueio após quitação |
| **J** | CRELI | Conta | Atraso acima de 67 dias. Conta não cancelada definitivamente |
| **K** | Excesso de limite | Conta | **Descadastrado em 07/02/2022**. Limite consumido > contratado |
| **L** | Crédito desabilitado | Conta | Limite zerado. Função débito funciona |
| **M** | Falecimento | Cartão | Cancelamento por falecimento. Conta cartão cancelada |
| **N** | Cancelamento por fraude | Cartão | Fraude por clonagem. Aplica também bloqueio U na conta |
| **O** | Preventivo Fraude | Cartão | Bloqueio temporário automático. Requer contato com central |
| **P** | Perda | Cartão | Cancelamento do físico por perda (via app). Nova via automática |
| **Q** | Quebra de acordo | Conta | Quebra de acordo. Desbloqueio após quitação. Não automático |
| **R** | Roubo | Cartão | Cancelamento do físico por roubo (via app). Nova via automática |
| **S** | Função crédito dormente | Conta | Cartão apenas débito. Irreversível uma vez retirado |
| **T** | Transporte | Cartão | Cartão em trânsito. Desbloqueio pelo cliente. Virtual/digital funcionam |
| **U** | Cancelamento do cartão | Conta | Cancelamento por solicitação. Permite futura reativação |
| **V** | VIP | Conta | Não usado |
| **X** | Anuidade não paga | Conta | Fatura apenas com taxas/tarifas. Cliente pode usar normalmente |
| **Y** | Renegociação | Cartão | Bloqueio manual da assessoria. Permanece após quitação |
| **Z** | Bloqueio temporário | Cartão | Bloqueio temporário |

### Sinônimos e Variações para Busca

#### Bloqueios de Atraso/Inadimplência
- "em atraso", "fatura atrasada" → bloqueio IN ('A', 'B', 'I', 'J')
- "atraso leve", "atraso pequeno" → bloqueio = 'A'
- "atraso moderado" → bloqueio = 'B'
- "spc", "serasa", "negativado" → bloqueio = 'I'
- "creli", "charge off", "inadimplente grave" → bloqueio = 'J'

#### Bloqueios de Fraude/Segurança
- "fraude", "fraudado" → bloqueio IN ('F', 'N', 'O')
- "preventivo", "bloqueio preventivo" → bloqueio = 'O'
- "clonado", "clonagem" → bloqueio = 'N'

#### Bloqueios de Perda/Roubo
- "perdido", "perda" → bloqueio = 'P'
- "roubado", "roubo" → bloqueio = 'R'
- "extraviado", "extravio" → bloqueio = 'E'

#### Bloqueios de Cancelamento
- "cancelado", "cancelamento" → bloqueio IN ('U', 'M', 'N')
- "cancelado pelo cliente" → bloqueio = 'U'
- "falecido", "óbito" → bloqueio = 'M'

#### Bloqueios de Função
- "só débito", "sem crédito", "crédito bloqueado" → bloqueio IN ('S', 'L')
- "crédito dormente" → bloqueio = 'S'
- "limite zerado" → bloqueio = 'L'

#### Outros
- "acordo", "renegociação" → bloqueio IN ('H', 'Y')
- "quebra de acordo" → bloqueio = 'Q'
- "cartão em transporte", "aguardando entrega" → bloqueio = 'T'
- "substituição", "segunda via" → bloqueio = 'G'

---

## 3. Combinações Comuns de Status e Bloqueio

| Cenário | Condição |
|---------|----------|
| Base ativa apta a uso | status = 'A' AND bloqueio IS NULL |
| Base cancelada | status IN ('8', '9', 'P') OR bloqueio IN ('U', 'M', 'N') |
| Bloqueado CRELI | status = 'Z' AND bloqueio = 'J' |
| Bloqueado crédito (ativo) | status = 'A' AND bloqueio = 'L' |
| Bloqueado por atraso até 66 dias | status = 'A' AND bloqueio IN ('B', 'I') |
| Bloqueio preventivo fraude | status = 'A' AND bloqueio = 'O' |

---

## 4. Impacto nas Transações por Tipo de Bloqueio

| Bloqueio | Crédito | Débito | Observação |
|----------|---------|--------|------------|
| (branco) | ✅ | ✅ | Ativo |
| A | ✅ | ✅ | Atraso leve, funciona normal |
| B | ❌ | ✅ | Crédito bloqueado |
| I | ❌ | ✅ | Crédito bloqueado (SPC) |
| J | ❌ | ❌ | Tudo bloqueado (CRELI) |
| K | ❌ | ✅ | Crédito bloqueado (excesso limite) |
| L | ❌ | ✅ | Crédito desabilitado |
| S | ❌ | ✅ | Só débito |
| T | ❌ | ❌ | Em transporte |
| U | ❌ | ❌ | Cancelado |
