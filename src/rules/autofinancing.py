import difflib
import pandas as pd
import logging
from .base import FraudDetectionRule
from ..utils import clean_name

logger = logging.getLogger(__name__)


class AutofinancingRule(FraudDetectionRule):
    """
    Detecta autofinanciamento: quando o nome do portador é muito similar
    ao nome do estabelecimento. Geralmente indica que alguém está usando
    cartão para sacar dinheiro da própria empresa.
    
    Indicador de: Autofinanciamento, cash-out, desvio de recursos
    """

    def __init__(self, config):
        self.config = config.get('autofinancing', {})
        weight = config.get('alert_weights', {}).get('autofinancing', 5)
        super().__init__(self.config, weight)

    def _calculate_similarity(self, name1, name2):
        """
        Calcula similaridade entre dois nomes usando SequenceMatcher.
        Retorna percentual (0-100).
        """
        try:
            similarity = difflib.SequenceMatcher(None, name1, name2).ratio() * 100
            return similarity
        except Exception as e:
            logger.warning(f"Erro ao calcular similaridade: {e}")
            return 0

    def detect(self, df):
        """
        Detecta autofinanciamento comparando nomes de portador e estabelecimento.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações suspeitas de autofinanciamento
        """
        required_columns = ['CARDHOLDER', 'ESTABLISHMENT_NAME']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            threshold = self.config.get('similarity_threshold', 70)
            
            data = df.copy()

            # Limpar nomes
            data['CARDHOLDER_CLEAN'] = data['CARDHOLDER'].apply(clean_name)
            data['ESTABLISHMENT_CLEAN'] = data['ESTABLISHMENT_NAME'].apply(clean_name)

            # Calcular similaridade para cada transação
            data['SIMILARITY'] = data.apply(
                lambda row: self._calculate_similarity(
                    row['CARDHOLDER_CLEAN'],
                    row['ESTABLISHMENT_CLEAN']
                ),
                axis=1
            )

            # Filtrar suspeitas
            suspicious = data[data['SIMILARITY'] >= threshold].copy()

            if not suspicious.empty:
                suspicious = self.add_alert_metadata(
                    suspicious,
                    f"Nome do portador muito similar ao estabelecimento ({threshold}% de similaridade)"
                )
                logger.info(f"Detectadas {len(suspicious)} transações com autofinanciamento suspeito")

            # Limpar colunas temporárias
            suspicious = suspicious.drop(columns=['CARDHOLDER_CLEAN', 'ESTABLISHMENT_CLEAN', 'SIMILARITY'], 
                                        errors='ignore')

            return suspicious

        except Exception as e:
            logger.error(f"Erro em AutofinancingRule.detect(): {e}")
            return pd.DataFrame()
