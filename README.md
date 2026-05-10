# Fraud Detection Engine

Um motor modular de detecção de fraude em transações, focado em transações de pagamento e análise PLD/AML.

## Aviso Importante

Todos os dados utilizados nos exemplos deste repositório são fictícios e gerados artificialmente para fins de demonstração. Nenhum dado real de clientes, portadores, estabelecimentos ou operações financeiras é utilizado.

Este projeto tem finalidade educacional e demonstrativa. As regras públicas foram descritas em nível seguro e não representam a totalidade de controles, estratégias ou critérios utilizados em ambientes reais de prevenção à fraude.

## Visão Geral

O Fraud Detection Engine implementa um conjunto de regras de detecção para identificar comportamentos transacionais que merecem revisão. Cada regra é independente e pode ser ativada/desativada conforme necessário.

### Regras implementadas

- Transações repetidas em curta janela de tempo
- Portadores restritos
- Horário comercial
- Limites por MCC
- Média presencial

## Instalação

### Requisitos

- Python 3.8+
- pandas
- PyYAML

### Setup

```bash
# Clonar repositório
git clone https://github.com/richard95br/fraud-detection.git
cd fraud-detection

# Criar ambiente virtual
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\\Scripts\\activate

# Instalar dependências
pip install -r requirements.txt
```

## Executando exemplo

```bash
python examples/run_example.py
```

O script gera transações fictícias, executa as regras e salva os alertas em CSV.

## Objetivo do projeto

Este projeto foi criado com foco em:

- Estudos de prevenção à fraude e PLD/AML
- Simulação segura de regras de monitoramento transacional
- Estrutura modular para criação de novas regras
- Testes e experimentação com análise comportamental
- Portfólio técnico voltado ao mercado financeiro

## Estrutura do projeto

```text
fraud-detection/
├── examples/
├── src/
│   ├── rules/
│   ├── config.yaml
│   └── engine.py
├── requirements.txt
└── README.md
```

## Melhorias futuras

- Score consolidado por transação
- Testes unitários
- Validação e padronização automática de colunas
- Relatório sintético por estabelecimento
- Resumo executivo dos alertas gerados
- Integração com dados em lote
- Documentação técnica das regras em nível conceitual

## Licença

MIT
