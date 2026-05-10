#!/usr/bin/env python3
"""
Exemplo de uso do Fraud Detection Engine

Este script demonstra como:
1. Inicializar o engine
2. Carregar dados
3. Executar detecção
4. Analisar resultados
"""

import sys
import logging
from pathlib import Path

# Adicionar diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine import FraudDetectionEngine
from src.utils import save_csv
from examples.sample_data import (
    generate_sample_transactions,
    generate_sample_mcc_limits,
    generate_sample_restricted_portadores,
    generate_sample_averages,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Fraud Detection Engine - Exemplo de Uso ===\n")

    # 1. Gerar dados de exemplo
    logger.info("1. Gerando dados de exemplo...")
    transactions = generate_sample_transactions(n_transactions=100)
    mcc_limits = generate_sample_mcc_limits()
    restricted = generate_sample_restricted_portadores()
    averages = generate_sample_averages()

    logger.info(f"   - {len(transactions)} transações geradas")
    logger.info(f"   - {len(mcc_limits)} MCCs configurados")
    logger.info(f"   - {len(restricted)} portadores restritos")
    logger.info(f"   - {len(averages)} estabelecimentos com médias\n")

    # 2. Inicializar o engine
    logger.info("2. Inicializando o engine...")
    engine = FraudDetectionEngine()
    logger.info(f"   Engine: {engine}\n")

    # 3. Carregar dados nas regras
    logger.info("3. Carregando dados de configuração...")
    engine.set_restricted_list(restricted)
    engine.set_mcc_limits(mcc_limits)
    engine.set_establishment_averages(averages)
    logger.info("   Dados carregados com sucesso\n")

    # 4. Executar detecção
    logger.info("4. Executando detecção de fraude...")
    alerts = engine.detect(transactions)
    logger.info(f"   Total de alertas gerados: {len(alerts)}\n")

    # 5. Analisar resultados
    logger.info("5. Resumo de alertas:")
    summary = engine.get_alerts_summary()
    logger.info(f"   Total: {summary['total']} alertas")
    logger.info(f"   Peso total: {summary['total_weight']} pontos")
    
    if summary['by_type']:
        logger.info("   Por tipo:")
        for alert_type, count in summary['by_type'].items():
            logger.info(f"     - {alert_type}: {count}")
    logger.info()

    # 6. Exibir amostra de alertas
    if not alerts.empty:
        logger.info("6. Amostra dos alertas gerados (primeiras 5 linhas):")
        
        # Selecionar colunas principais para exibição
        display_cols = [
            'TRANSACTION_ID', 'TRANSACTION_DATE', 'CARDHOLDER',
            'ESTABLISHMENT_NAME', 'VALUE', 'ALERT_TYPE', 'ALERT_WEIGHT'
        ]
        display_cols = [col for col in display_cols if col in alerts.columns]
        
        print(alerts[display_cols].head(5).to_string(index=False))
        logger.info()
    else:
        logger.info("6. Nenhum alerta gerado\n")

    # 7. Salvar resultados
    output_file = 'fraud_detection_alerts.csv'
    logger.info(f"7. Salvando resultados em '{output_file}'...")
    if engine.save_alerts(output_file):
        logger.info(f"   Arquivo salvo com sucesso\n")
    else:
        logger.error(f"   Erro ao salvar arquivo\n")

    # 8. Mostrar colunas disponíveis
    if not alerts.empty:
        logger.info("8. Colunas disponíveis nos alertas:")
        for col in alerts.columns:
            logger.info(f"   - {col}")
    
    logger.info("\n=== Execução finalizada ===")


if __name__ == '__main__':
    main()
