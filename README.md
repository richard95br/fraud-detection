# Fraud Detection Engine

Um motor modular de detecção de fraude em transações, focado em transações de pagamento e análise PLD/AML.

## Visão Geral

O Fraud Detection Engine implementa um conjunto de regras de detecção para identificar padrões suspeitos em transações. Cada regra é independente e pode ser ativada/desativada conforme necessário.

**Regras implementadas:**

- **Transações repetidas**: detecta mesma transação em múltiplas tentativas em janela de tempo (ex: 1 hora)
- **Autofinanciamento**: identifica quando o nome do portador é muito similar ao estabelecimento (cash-out suspeito)
- **Portadores restritos**: valida contra lista de portadores/cartões bloqueados
- **Horário comercial**: alerta transações de valor alto fora do horário comercial (7h-21h)
- **Limites por MCC**: valida valor da transação contra limite configurado para categoria (MCC)
- **Média presencial**: compara valor da transação com média histórica do estabelecimento

## Instalação

### Requisitos

- Python 3.8+
- pandas
- PyYAML

### Setup

```bash
# Clonar repositório
git clone <repository>
cd fraud_detection

# Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Uso Rápido

### Exemplo Básico

```python
from src.engine import FraudDetectionEngine
import pandas as pd

# 1. Inicializar engine
engine = FraudDetectionEngine()

# 2. Carregar dados (dataframes com transações e configs)
transactions = pd.read_csv('transactions.csv', sep=';')
restricted = pd.read_csv('restricted_portadores.csv', sep=',')
mcc_limits = pd.read_csv('mcc_limits.csv', sep=',')
averages = pd.read_csv('establishment_averages.csv', sep=',')

# 3. Carregar configurações
engine.set_restricted_list(restricted)
engine.set_mcc_limits(mcc_limits)
engine.set_establishment_averages(averages)

# 4. Executar detecção
alerts = engine.detect(transactions)

# 5. Analisar resultados
print(f"Total de alertas: {len(alerts)}")
print(alerts[['TRANSACTION_ID', 'ALERT_TYPE', 'ALERT_WEIGHT']])

# 6. Salvar em CSV
engine.save_alerts('output_alerts.csv')
```

### Executar Exemplo

```bash
python examples/run_example.py
```

Isso gera dados de exemplo, executa detecção e salva resultados em `fraud_detection_alerts.csv`.

## Estrutura de Dados

### Transações (Input)

Esperado um DataFrame com as seguintes colunas:

```
TRANSACTION_ID          - ID único da transação
TRANSACTION_DATE        - Data/hora (formato: 'DD/MM/YYYY HH:MM')
CARDHOLDER              - Nome do portador do cartão
ESTABLISHMENT_NAME      - Nome do estabelecimento
ESTABLISHMENT_CNPJ      - CNPJ do estabelecimento
MCC                     - Merchant Category Code (código da categoria)
VALUE                   - Valor em moeda (float)
CHANNEL                 - Canal ('PRESENCIAL' ou 'ONLINE')
CARD_NUMBER             - Número do cartão (BIN + últimos 4, ex: '123456****1234')
STATUS                  - Status da transação (filtrar por 'APPROVED')
```

### Alertas (Output)

Cada alerta retorna:

```
TRANSACTION_ID          - ID da transação que gerou alerta
ALERT_TYPE              - Tipo de alerta gerado
ALERT_DESCRIPTION       - Descrição detalhada do alerta
ALERT_WEIGHT            - Peso do alerta (para priorização)
... (todas as colunas da transação original)
```

## Configuração

### Arquivo config.yaml

Todas as configurações estão em `src/config.yaml`:

```yaml
repeated_transactions:
  time_window_hours: 1      # Janela de tempo (horas)
  min_value: 0              # Valor mínimo para considerar

autofinancing:
  similarity_threshold: 70   # % de similaridade para alerta

business_hours:
  start_hour: 7              # Início horário comercial
  end_hour: 21               # Fim horário comercial
  high_value_threshold: 1000 # Valor mínimo fora de horário

average_check:
  multiplier: 1.5            # Quanto acima da média dispara alerta
  default_average: 450       # Valor padrão se sem histórico

alert_weights:
  repeated_transactions: 3
  autofinancing: 5
  restricted_portador: 10
  # ... outros pesos
```

## Regras Detalhadas

### RepeatedTransactionsRule

Detecta transações repetidas do mesmo portador no mesmo estabelecimento dentro de uma janela de tempo.

**Caso de uso**: Teste de cartão clonado, split de transação

**Configuração**:
```yaml
repeated_transactions:
  time_window_hours: 1
  min_value: 0
  generic_portadores: []  # Nomes a ignorar
```

### AutofinancingRule

Identifica quando o nome do portador é muito similar ao estabelecimento (comparação fuzzy).

**Caso de uso**: Cash-out ilícito, desvio de recursos

**Configuração**:
```yaml
autofinancing:
  similarity_threshold: 70  # percentual (0-100)
```

### RestrictedPortadoresRule

Valida transação contra lista de portadores/cartões bloqueados.

**Caso de uso**: Fraude com cartão roubado/clonado, contas sancionadas

**Dados necessários**:
```
CARDHOLDER          - Nome do portador
CARD_NUMBER         - BIN + últimos 4 dígitos (ex: 123456****1234)
REASON              - Motivo da restrição
```

### BusinessHoursRule

Alerta transações de valor alto fora do horário comercial.

**Caso de uso**: Fraude, teste de cartão, atividade suspeita

**Configuração**:
```yaml
business_hours:
  start_hour: 7
  end_hour: 21
  high_value_threshold: 1000
```

### MCCLimitsRule

Valida valor contra limites configurados por MCC.

**Caso de uso**: Valor anormalmente alto para categoria de estabelecimento

**Dados necessários**:
```
MCC                 - Merchant Category Code
DESCRIPTION         - Descrição do MCC
LIMIT               - Limite de valor
```

### AverageCheckRule

Compara valor da transação com média histórica presencial do estabelecimento.

**Caso de uso**: Padrão de comportamento anormal

**Dados necessários**:
```
ESTABLISHMENT_CNPJ  - CNPJ do estabelecimento
AVERAGE_VALUE       - Valor médio histórico
```

## Estendendo com Novas Regras

Criar nova regra é simples. Herdar de `FraudDetectionRule`:

```python
from src.rules.base import FraudDetectionRule
import pandas as pd

class MyCustomRule(FraudDetectionRule):
    def __init__(self, config):
        self.config = config.get('my_rule', {})
        weight = config.get('alert_weights', {}).get('my_rule', 1)
        super().__init__(self.config, weight)
    
    def detect(self, df):
        required_columns = ['COLUMN1', 'COLUMN2']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()
        
        # Implementar lógica de detecção
        suspicious = df[df['COLUMN1'] > 1000].copy()
        
        if not suspicious.empty:
            suspicious = self.add_alert_metadata(
                suspicious,
                'Descrição do alerta'
            )
        
        return suspicious
```

Depois adicionar ao engine:

```python
from examples.my_custom_rule import MyCustomRule

engine.rules['my_rule'] = MyCustomRule(engine.config)
```

## Usando Apenas Algumas Regras

```python
# Executar apenas regras específicas
alerts = engine.detect(transactions, rules_to_run=[
    'repeated_transactions',
    'autofinancing',
    'mcc_limits'
])
```

## Performance

Para grandes volumes (>100k transações), considerar:

1. **Usar dicionários em vez de DataFrames para lookup** (já implementado em `set_*` methods)
2. **Processar em chunks** se a memória for limitada
3. **Paralelizar regras** (futuro)

## Limitações Conhecidas

- Comparação de nome em autofinancing usa `SequenceMatcher` (O(n*m)) — considerar alternativa em escala
- Sem detecção de velocity real-time (requer streaming)
- Sem detecção de structuring (valores logo abaixo de limites redondos)
- Sem análise de split payments

## Contribuindo

Sugestões de melhorias são bem-vindas! Áreas de interesse:

- [ ] Velocity rules (múltiplas transações em curto tempo)
- [ ] Structuring detection (valores 9.999,99, 1.999,88, etc)
- [ ] Split payment detection
- [ ] Wishlist por estabelecimento
- [ ] Failed transaction patterns
- [ ] Machine learning scoring
- [ ] Testes unitários
- [ ] Documentação em PDF

## Licença

MIT

## Contato

Dúvidas ou sugestões? Abrir uma issue no repositório.
