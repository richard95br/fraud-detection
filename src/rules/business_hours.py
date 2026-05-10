import pandas as pd
import logging
from .base import FraudDetectionRule
from ..utils import parse_datetime

logger = logging.getLogger(__name__)


class BusinessHoursRule(FraudDetectionRule):
    """
    Detecta transações de valor alto fora do horário comercial.
    Padrão: 7h até 21h (horário comercial normal)
    
    Indicador de: Fraude, teste de cartão, atividade suspeita
    """

    def __init__(self, config):
        self.config = config.get('business_hours', {})
        weight = config.get('alert_weights', {}).get('business_hours_violation', 2)
        super().__init__(self.config, weight)

    def detect(self, df):
        """
        Detecta transações de valor alto fora do horário comercial.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações suspeitas
        """
        required_columns = ['TRANSACTION_DATE', 'VALUE']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            config = self.config
            start_hour = config.get('start_hour', 7)
            end_hour = config.get('end_hour', 21)
            threshold = config.get('high_value_threshold', 1000)

            data = df.copy()

            # Parse de data
            data['TRANSACTION_DATE'] = data['TRANSACTION_DATE'].apply(
                lambda x: parse_datetime(x) if isinstance(x, str) else x
            )

            # Extrair hora
            data['HOUR'] = data['TRANSACTION_DATE'].dt.hour

            # Identificar fora do horário comercial
            data['OFF_HOURS'] = (data['HOUR'] < start_hour) | (data['HOUR'] > end_hour)

            # Filtrar
            suspicious = data[(data['OFF_HOURS']) & (data['VALUE'] > threshold)].copy()

            if not suspicious.empty:
                suspicious = self.add_alert_metadata(
                    suspicious,
                    f"Transação de valor alto fora do horário comercial (antes das {start_hour}h ou depois das {end_hour}h)"
                )
                logger.info(f"Detectadas {len(suspicious)} transações fora do horário comercial")

            # Limpar coluna temporária
            suspicious = suspicious.drop(columns=['HOUR', 'OFF_HOURS'], errors='ignore')

            return suspicious

        except Exception as e:
            logger.error(f"Erro em BusinessHoursRule.detect(): {e}")
            return pd.DataFrame()
