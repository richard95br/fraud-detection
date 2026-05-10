import pandas as pd
import logging
from .base import FraudDetectionRule
from ..utils import clean_name

logger = logging.getLogger(__name__)


class RestrictedPortadoresRule(FraudDetectionRule):
    """
    Detecta uso de portadores ou cartões que estão em lista restrita/bloqueada.
    Requer um DataFrame com portadores/cartões restritos e motivo da restrição.
    
    Indicador de: Fraude com cartão bloqueado, clonagem, roubo
    """

    def __init__(self, config):
        self.config = config
        weight = config.get('alert_weights', {}).get('restricted_portador', 10)
        super().__init__(self.config, weight)
        self.restricted_df = None

    def set_restricted_list(self, restricted_df):
        """
        Define a lista de portadores/cartões restritos.
        
        Args:
            restricted_df: DataFrame com colunas CARDHOLDER, CARD_NUMBER, REASON
        """
        if restricted_df.empty:
            logger.warning("Lista de portadores restritos vazia")
            return

        try:
            self.restricted_df = restricted_df.copy()
            # Limpar nomes
            if 'CARDHOLDER' in self.restricted_df.columns:
                self.restricted_df['CARDHOLDER'] = self.restricted_df['CARDHOLDER'].apply(clean_name)
            if 'CARD_NUMBER' in self.restricted_df.columns:
                self.restricted_df['CARD_NUMBER'] = self.restricted_df['CARD_NUMBER'].fillna('').astype(str).str.strip()
            
            logger.info(f"Lista de restritos carregada: {len(self.restricted_df)} portadores/cartões")
        except Exception as e:
            logger.error(f"Erro ao carregar lista de restritos: {e}")

    def detect(self, df):
        """
        Detecta uso de portadores ou cartões restritos.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações usando portadores/cartões restritos
        """
        if self.restricted_df is None or self.restricted_df.empty:
            logger.warning("Lista de restritos não carregada")
            return pd.DataFrame()

        required_columns = ['CARDHOLDER', 'CARD_NUMBER']
        
        if not self.validate_columns(df, required_columns):
            return pd.DataFrame()

        try:
            data = df.copy()

            # Limpar dados
            data['CARDHOLDER'] = data['CARDHOLDER'].apply(clean_name)
            data['CARD_NUMBER'] = data['CARD_NUMBER'].fillna('').astype(str).str.strip()

            # Filtrar apenas cartões válidos
            data = data[data['CARD_NUMBER'] != '']
            restricted_list = self.restricted_df[self.restricted_df['CARD_NUMBER'] != '']

            # Merge por CARDHOLDER
            by_cardholder = data.merge(
                restricted_list[['CARDHOLDER', 'REASON']],
                on='CARDHOLDER',
                how='left',
                indicator='CARDHOLDER_MATCH'
            )

            # Merge por CARD_NUMBER
            by_card = data.merge(
                restricted_list[['CARD_NUMBER', 'REASON']],
                on='CARD_NUMBER',
                how='left',
                indicator='CARD_MATCH'
            )

            # Combinar resultados
            result = by_cardholder.copy()
            result['CARD_MATCH_REASON'] = by_card['REASON']
            result['CARD_MATCH'] = by_card['CARD_MATCH']

            # Identificar transações restritas
            restricted = result[
                (result['CARDHOLDER_MATCH'] == 'both') | (result['CARD_MATCH'] == 'both')
            ].copy()

            if not restricted.empty:
                # Consolidar motivo
                restricted['RESTRICTION_REASON'] = restricted.apply(
                    lambda row: row['REASON'] if pd.notna(row['REASON']) else row['CARD_MATCH_REASON'],
                    axis=1
                )
                restricted['RESTRICTION_REASON'] = restricted['RESTRICTION_REASON'].fillna('Motivo desconhecido')

                restricted = self.add_alert_metadata(
                    restricted,
                    'Portador ou cartão em lista de restritos'
                )
                logger.info(f"Detectadas {len(restricted)} transações com portadores/cartões restritos")

            # Limpar colunas temporárias
            cols_to_drop = ['CARDHOLDER_MATCH', 'CARD_MATCH', 'CARD_MATCH_REASON', 'REASON']
            restricted = restricted.drop(columns=cols_to_drop, errors='ignore')

            return restricted

        except Exception as e:
            logger.error(f"Erro em RestrictedPortadoresRule.detect(): {e}")
            return pd.DataFrame()
