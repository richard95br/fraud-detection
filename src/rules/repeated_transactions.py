import pandas as pd
import logging
from .base import FraudDetectionRule
from ..utils import parse_datetime, clean_name

logger = logging.getLogger(__name__)


class RepeatedTransactionsRule(FraudDetectionRule):
    """
    Detecta transações repetidas do mesmo portador no mesmo estabelecimento
    dentro de uma janela de tempo específica (padrão: 1 hora).
    
    Indicador de: Split transactions, teste de cartão, ou duplicação
    """

    def __init__(self, config):
        self.config = config.get('repeated_transactions', {})
        weight = config.get('alert_weights', {}).get('repeated_transactions', 3)
        super().__init__(self.config, weight)

    def detect(self, df):
        """
        Detecta transações repetidas.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações repetidas
        """
        required_columns = ['CARDHOLDER', 'ESTABLISHMENT_CNPJ', 'TRANSACTION_DATE', 'VALUE']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            # Configurações
            time_window = self.config.get('time_window_hours', 1)
            min_value = self.config.get('min_value', 0)
            generic_portadores = self.config.get('generic_portadores', [])

            # Cópia para não modificar original
            data = df.copy()

            # Filtrar
            data = data.dropna(subset=['CARDHOLDER'])
            data = data[~data['CARDHOLDER'].isin(generic_portadores)]
            data = data[data['VALUE'] > min_value]

            # Parse de data
            data['TRANSACTION_DATE'] = data['TRANSACTION_DATE'].apply(
                lambda x: parse_datetime(x) if isinstance(x, str) else x
            )

            # Ordenar
            data = data.sort_values(by=['CARDHOLDER', 'ESTABLISHMENT_CNPJ', 'TRANSACTION_DATE'])

            # Calcular diferença de horas entre transações consecutivas
            data['HOURS_DIFF'] = (
                data.groupby(['CARDHOLDER', 'ESTABLISHMENT_CNPJ'])['TRANSACTION_DATE']
                .diff()
                .dt.total_seconds()
                .div(3600)
            )

            # Filtrar transações dentro da janela de tempo
            repeated = data[data['HOURS_DIFF'] < time_window].dropna(subset=['HOURS_DIFF'])

            if not repeated.empty:
                repeated = self.add_alert_metadata(
                    repeated,
                    f"Transação repetida do mesmo portador no mesmo estabelecimento em menos de {time_window} hora(s)"
                )
                logger.info(f"Detectadas {len(repeated)} transações repetidas")

            return repeated

        except Exception as e:
            logger.error(f"Erro em RepeatedTransactionsRule.detect(): {e}")
            return pd.DataFrame()
