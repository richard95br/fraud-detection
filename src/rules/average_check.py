import pandas as pd
import logging
from .base import FraudDetectionRule
from ..utils import clean_cnpj_cpf, format_percentage

logger = logging.getLogger(__name__)


class AverageCheckRule(FraudDetectionRule):
    """
    Detecta transações que excedem significativamente a média histórica
    do estabelecimento para transações presenciais.
    
    Requer histórico de valores médios por estabelecimento.
    
    Indicador de: Padrão de comportamento anormal, fraude
    """

    def __init__(self, config):
        self.config = config.get('average_check', {})
        weight = config.get('alert_weights', {}).get('above_average', 2)
        super().__init__(self.config, weight)
        self.averages = {}

    def set_establishment_averages(self, avg_df):
        """
        Define as médias de valor por estabelecimento.
        
        Args:
            avg_df: DataFrame com colunas ESTABLISHMENT_CNPJ, AVERAGE_VALUE
                   Exemplo:
                       ESTABLISHMENT_CNPJ,AVERAGE_VALUE
                       12345678901234,450.50
        """
        if avg_df.empty:
            logger.warning("DataFrame de médias vazio")
            return

        try:
            if 'ESTABLISHMENT_CNPJ' not in avg_df.columns:
                logger.error("Coluna 'ESTABLISHMENT_CNPJ' não encontrada")
                return

            # Limpar CNPJs
            avg_df['ESTABLISHMENT_CNPJ_CLEAN'] = avg_df['ESTABLISHMENT_CNPJ'].apply(clean_cnpj_cpf)

            # Encontrar coluna de média
            avg_col = None
            for col in ['AVERAGE_VALUE', 'AVERAGE', 'MEDIA', 'MEDIA_PRESENCIAL']:
                if col in avg_df.columns:
                    avg_col = col
                    break

            if avg_col is None:
                logger.error("Nenhuma coluna de média encontrada")
                return

            # Criar dicionário
            self.averages = dict(zip(
                avg_df['ESTABLISHMENT_CNPJ_CLEAN'],
                avg_df[avg_col]
            ))
            logger.info(f"Médias por estabelecimento carregadas: {len(self.averages)} estabelecimentos")

        except Exception as e:
            logger.error(f"Erro ao carregar médias: {e}")

    def detect(self, df):
        """
        Detecta transações presenciais acima de múltiplos da média.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações acima da média
        """
        if not self.averages:
            logger.warning("Médias de estabelecimento não carregadas")
            return pd.DataFrame()

        required_columns = ['ESTABLISHMENT_CNPJ', 'VALUE', 'CHANNEL']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            config = self.config
            multiplier = config.get('multiplier', 1.5)
            default_avg = config.get('default_average', 450)

            data = df.copy()

            # Limpar CNPJ
            data['ESTABLISHMENT_CNPJ_CLEAN'] = data['ESTABLISHMENT_CNPJ'].apply(clean_cnpj_cpf)

            # Buscar média
            data['ESTABLISHMENT_AVERAGE'] = data['ESTABLISHMENT_CNPJ_CLEAN'].map(self.averages)
            data['ESTABLISHMENT_AVERAGE'] = data['ESTABLISHMENT_AVERAGE'].fillna(default_avg)

            # Calcular percentual acima da média
            data['PERCENTAGE_ABOVE_AVERAGE'] = (
                ((data['VALUE'] - data['ESTABLISHMENT_AVERAGE']) / data['ESTABLISHMENT_AVERAGE'] * 100)
                .clip(lower=0)
                .apply(lambda x: format_percentage(x) if x != float('inf') else 0)
            )

            # Filtrar: canal presencial E valor > média * multiplicador
            channel_lower = data['CHANNEL'].str.lower() if isinstance(data['CHANNEL'].iloc[0], str) else data['CHANNEL']
            
            suspicious = data[
                (channel_lower == 'presencial') &
                (data['VALUE'] > (data['ESTABLISHMENT_AVERAGE'] * multiplier))
            ].copy()

            if not suspicious.empty:
                suspicious = self.add_alert_metadata(
                    suspicious,
                    f"Valor presencial acima de {multiplier}x a média histórica do estabelecimento"
                )
                logger.info(f"Detectadas {len(suspicious)} transações acima da média")

            # Limpar colunas temporárias
            suspicious = suspicious.drop(
                columns=['ESTABLISHMENT_CNPJ_CLEAN', 'ESTABLISHMENT_AVERAGE'],
                errors='ignore'
            )

            return suspicious

        except Exception as e:
            logger.error(f"Erro em AverageCheckRule.detect(): {e}")
            return pd.DataFrame()
