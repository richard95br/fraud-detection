from abc import ABC, abstractmethod
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FraudDetectionRule(ABC):
    """
    Classe base abstrata para todas as regras de detecção de fraude.
    Todas as regras devem herdar desta classe e implementar o método detect().
    """

    def __init__(self, config, weight=1):
        """
        Args:
            config: dicionário com configurações da regra
            weight: peso da regra para priorização de alertas
        """
        self.config = config
        self.weight = weight
        self.name = self.__class__.__name__
        self.alerts = pd.DataFrame()

    @abstractmethod
    def detect(self, df):
        """
        Método que deve ser implementado por cada regra.
        
        Args:
            df: DataFrame com transações
            
        Returns:
            DataFrame com transações que violam a regra
        """
        pass

    def validate_columns(self, df, required_columns):
        """
        Valida se as colunas necessárias existem no DataFrame.
        
        Args:
            df: DataFrame a validar
            required_columns: lista de colunas necessárias
            
        Returns:
            bool: True se todas as colunas existem
        """
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.warning(f"Colunas faltantes em {self.name}: {missing}")
            return False
        return True

    def add_alert_metadata(self, df, alert_description):
        """
        Adiciona metadados do alerta ao DataFrame.
        
        Args:
            df: DataFrame com transações que geraram alerta
            alert_description: descrição do alerta
            
        Returns:
            DataFrame com metadados adicionados
        """
        result = df.copy()
        result['ALERT_TYPE'] = self.name
        result['ALERT_DESCRIPTION'] = alert_description
        result['ALERT_WEIGHT'] = self.weight
        return result

    def __repr__(self):
        return f"{self.name} (weight={self.weight})"
