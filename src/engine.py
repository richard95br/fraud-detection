import pandas as pd
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from .rules import (
    RepeatedTransactionsRule,
    AutofinancingRule,
    RestrictedPortadoresRule,
    BusinessHoursRule,
    MCCLimitsRule,
    AverageCheckRule,
)
from .utils import load_csv, save_csv

logger = logging.getLogger(__name__)


class FraudDetectionEngine:
    """
    Engine principal de detecção de fraude.
    Orquestra múltiplas regras de detecção e agrega os resultados.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o engine com configurações.
        
        Args:
            config_path: caminho para arquivo YAML de configuração
        """
        self.config = self._load_config(config_path)
        self.rules: Dict[str, object] = {}
        self.alerts = pd.DataFrame()
        self._initialize_rules()

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Carrega configuração do arquivo YAML"""
        if config_path is None:
            # Procurar config.yaml no mesmo diretório
            config_path = Path(__file__).parent / 'config.yaml'

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuração carregada de: {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"Arquivo de config não encontrado: {config_path}. Usando config padrão.")
            return self._default_config()
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return self._default_config()

    def _default_config(self) -> dict:
        """Retorna configuração padrão"""
        return {
            'repeated_transactions': {'time_window_hours': 1, 'min_value': 0},
            'autofinancing': {'similarity_threshold': 70},
            'business_hours': {'start_hour': 7, 'end_hour': 21, 'high_value_threshold': 1000},
            'average_check': {'multiplier': 1.5, 'default_average': 450},
            'alert_weights': {
                'repeated_transactions': 3,
                'autofinancing': 5,
                'restricted_portador': 10,
                'business_hours_violation': 2,
                'mcc_limit_exceeded': 4,
                'above_average': 2,
            }
        }

    def _initialize_rules(self):
        """Inicializa todas as regras com configuração"""
        self.rules = {
            'repeated_transactions': RepeatedTransactionsRule(self.config),
            'autofinancing': AutofinancingRule(self.config),
            'restricted_portadores': RestrictedPortadoresRule(self.config),
            'business_hours': BusinessHoursRule(self.config),
            'mcc_limits': MCCLimitsRule(self.config),
            'average_check': AverageCheckRule(self.config),
        }
        logger.info(f"Engine inicializado com {len(self.rules)} regras")

    def set_restricted_list(self, restricted_df: pd.DataFrame):
        """Carrega lista de portadores restritos"""
        self.rules['restricted_portadores'].set_restricted_list(restricted_df)

    def set_mcc_limits(self, mcc_df: pd.DataFrame):
        """Carrega limites por MCC"""
        self.rules['mcc_limits'].set_mcc_limits(mcc_df)

    def set_establishment_averages(self, avg_df: pd.DataFrame):
        """Carrega médias por estabelecimento"""
        self.rules['average_check'].set_establishment_averages(avg_df)

    def detect(self, transactions_df: pd.DataFrame, rules_to_run: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Executa detecção de fraude em um DataFrame de transações.
        
        Args:
            transactions_df: DataFrame com transações
            rules_to_run: lista de nomes de regras a executar (None = todas)
            
        Returns:
            DataFrame com todas as alertas geradas
        """
        if transactions_df.empty:
            logger.warning("DataFrame de transações vazio")
            return pd.DataFrame()

        logger.info(f"Iniciando detecção em {len(transactions_df)} transações")

        # Determinar quais regras executar
        if rules_to_run is None:
            rules_to_run = list(self.rules.keys())
        else:
            rules_to_run = [r for r in rules_to_run if r in self.rules]

        all_alerts = []

        # Executar cada regra
        for rule_name in rules_to_run:
            try:
                rule = self.rules[rule_name]
                alerts = rule.detect(transactions_df)

                if not alerts.empty:
                    all_alerts.append(alerts)
                    logger.info(f"Regra '{rule_name}': {len(alerts)} alertas gerados")
                else:
                    logger.debug(f"Regra '{rule_name}': nenhum alerta")

            except Exception as e:
                logger.error(f"Erro ao executar regra '{rule_name}': {e}")

        # Combinar todos os alertas
        if all_alerts:
            self.alerts = pd.concat(all_alerts, ignore_index=True)
            logger.info(f"Total de alertas gerados: {len(self.alerts)}")
        else:
            self.alerts = pd.DataFrame()
            logger.info("Nenhum alerta gerado")

        return self.alerts

    def get_alerts_summary(self) -> dict:
        """Retorna resumo dos alertas gerados"""
        if self.alerts.empty:
            return {'total': 0, 'by_type': {}}

        summary = {
            'total': len(self.alerts),
            'by_type': {},
            'total_weight': 0,
        }

        if 'ALERT_TYPE' in self.alerts.columns:
            summary['by_type'] = self.alerts['ALERT_TYPE'].value_counts().to_dict()

        if 'ALERT_WEIGHT' in self.alerts.columns:
            summary['total_weight'] = int(self.alerts['ALERT_WEIGHT'].sum())

        return summary

    def save_alerts(self, output_path: str, delimiter: str = ';') -> bool:
        """
        Salva alertas em arquivo CSV.
        
        Args:
            output_path: caminho do arquivo de saída
            delimiter: delimitador do CSV
            
        Returns:
            True se salvo com sucesso
        """
        return save_csv(self.alerts, output_path, delimiter)

    def get_alerts(self) -> pd.DataFrame:
        """Retorna DataFrame com todos os alertas"""
        return self.alerts.copy()

    def __repr__(self):
        return f"FraudDetectionEngine(rules={len(self.rules)}, alerts={len(self.alerts)})"
