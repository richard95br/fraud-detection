import re
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_cnpj_cpf(value):
    """Remove caracteres não numéricos de CNPJ ou CPF"""
    return re.sub(r'\D', '', str(value))


def clean_name(value):
    """Limpa e padroniza nomes: remove espaços extras e converte para maiúsculo"""
    return re.sub(r'\s+', ' ', str(value).strip().upper())


def format_currency(value):
    """Converte string de valor em float, lidando com diferentes formatos"""
    try:
        return round(float(str(value).replace('.', '').replace(',', '.')), 2)
    except (ValueError, AttributeError):
        logger.warning(f"Erro ao formatar valor: {value}")
        return 0.0


def format_percentage(value):
    """Converte valor em percentual inteiro"""
    try:
        return int(round(float(value)))
    except (ValueError, TypeError):
        logger.warning(f"Erro ao formatar percentagem: {value}")
        return 0


def parse_datetime(date_str, date_format='%d/%m/%Y %H:%M'):
    """Parse de data com tratamento de erro"""
    try:
        return pd.to_datetime(date_str, format=date_format, dayfirst=True)
    except (ValueError, TypeError):
        logger.warning(f"Erro ao fazer parse de data: {date_str}")
        return pd.NaT


def load_csv(file_path, delimiter=';', encoding='utf-8-sig'):
    """Carrega arquivo CSV com tratamento de erro"""
    try:
        return pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo {file_path}: {e}")
        return pd.DataFrame()


def save_csv(df, file_path, delimiter=';'):
    """Salva DataFrame em CSV"""
    try:
        df.to_csv(file_path, index=False, sep=delimiter, encoding='utf-8-sig')
        logger.info(f"Arquivo salvo: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo {file_path}: {e}")
        return False


def identify_establishment_type(cnpj_cpf_str):
    """
    Identifica se é Pessoa Física (PF) ou Jurídica (PJ)
    PF tem 11 dígitos (CPF)
    PJ tem 14 dígitos (CNPJ)
    """
    clean_value = clean_cnpj_cpf(cnpj_cpf_str)
    if len(clean_value) == 11:
        return 'PF'
    elif len(clean_value) == 14:
        return 'PJ'
    else:
        return 'UNKNOWN'
