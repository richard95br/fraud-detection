import pandas as pd
import logging
from .base import FraudDetectionRule

logger = logging.getLogger(__name__)


class MCCLimitsRule(FraudDetectionRule):
    """
    Detecta transações que excedem o limite de valor configurado para
    cada MCC (Merchant Category Code).
    
    Diferentes tipos de negócios têm diferentes volumes esperados.
    Por exemplo: aeroporto (4511) pode ter transações maiores que
    feira livre (5411).
    
    Indicador de: Valor anormalmente alto para categoria, fraude
    """

    def __init__(self, config):
        self.config = config
        weight = config.get('alert_weights', {}).get('mcc_limit_exceeded', 4)
        super().__init__(self.config, weight)
        self.mcc_limits = {}

    def set_mcc_limits(self, mcc_df):
        """
        Define os limites de valor por MCC.
        
        Args:
            mcc_df: DataFrame com colunas MCC, DESCRIPTION, LIMIT
                   Exemplo:
                       MCC,DESCRIPTION,LIMIT
                       5411,Supermercados,5000
                       4511,Aeroporto,15000
        """
        if mcc_df.empty:
            logger.warning("DataFrame de MCC limites vazio")
            return

        try:
            # Garantir coluna de MCC
            if 'MCC' not in mcc_df.columns:
                logger.error("Coluna 'MCC' não encontrada em mcc_df")
                return

            # Usar coluna de limite (pode ser LIMIT, VALUE, etc)
            limit_col = None
            for col in ['LIMIT', 'VALUE', 'LIMIT_VALUE']:
                if col in mcc_df.columns:
                    limit_col = col
                    break

            if limit_col is None:
                logger.error("Nenhuma coluna de limite encontrada (esperado: LIMIT, VALUE ou LIMIT_VALUE)")
                return

            # Criar dicionário para lookup rápido
            self.mcc_limits = dict(zip(mcc_df['MCC'].astype(str), mcc_df[limit_col]))
            logger.info(f"Limites por MCC carregados: {len(self.mcc_limits)} MCCs")

        except Exception as e:
            logger.error(f"Erro ao carregar limites por MCC: {e}")

    def detect(self, df):
        """
        Detecta transações que excedem o limite para seu MCC.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações que excedem limites
        """
        if not self.mcc_limits:
            logger.warning("Limites por MCC não carregados")
            return pd.DataFrame()

        required_columns = ['MCC', 'VALUE']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            data = df.copy()
            
            # Garantir MCC como string
            data['MCC'] = data['MCC'].astype(str)

            # Buscar limite para cada MCC
            data['MCC_LIMIT'] = data['MCC'].map(self.mcc_limits)

            # Filtrar transações sem limite configurado (potencial problema)
            data_with_limit = data[data['MCC_LIMIT'].notna()].copy()

            # Identificar excedentes
            exceeded = data_with_limit[data_with_limit['VALUE'] > data_with_limit['MCC_LIMIT']].copy()

            if not exceeded.empty:
                exceeded = self.add_alert_metadata(
                    exceeded,
                    'Valor acima do limite configurado para o MCC'
                )
                logger.info(f"Detectadas {len(exceeded)} transações acima do limite MCC")

            # Limpar colunas temporárias
            exceeded = exceeded.drop(columns=['MCC_LIMIT'], errors='ignore')

            return exceeded

        except Exception as e:
            logger.error(f"Erro em MCCLimitsRule.detect(): {e}")
            return pd.DataFrame()
