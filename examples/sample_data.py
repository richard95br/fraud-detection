import pandas as pd
from datetime import datetime, timedelta
import random

def generate_sample_transactions(n_transactions=100):
    """Gera transações de exemplo com alguns padrões suspeitos"""
    
    cardholder = ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira'] * 25
    
    establishments = [
        ('João Silva Comércio LTDA', '12345678901234', '5411'),  # Supermercado
        ('Maria Santos Serviços', '98765432109876', '7299'),      # Serviços
        ('Pedro Costa Varejo', '11111111111111', '5411'),          # Supermercado
        ('Ana Oliveira Viagens', '22222222222222', '4511'),        # Aeroporto
    ]
    
    data = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(n_transactions):
        # Portador e estabelecimento aleatórios
        cardholder_name = cardholder[i]
        establishment_name, cnpj, mcc = establishments[i % len(establishments)]
        
        # Data aleatória
        days_offset = random.randint(0, 29)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        transaction_date = base_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        # Valor (alguns com padrão suspeito)
        if i % 20 == 0:  # 5% estruturing
            value = random.choice([1999.99, 3388.88, 4999.99, 9999.99])
        elif i % 15 == 0:  # 6% acima da média
            value = random.uniform(5000, 10000)
        else:
            value = random.uniform(50, 500)
        
        # Canal (90% presencial, 10% online)
        channel = 'PRESENCIAL' if random.random() > 0.1 else 'ONLINE'
        
        # Card number (BIN + últimos 4 dígitos)
        # BIN: primeiros 6 dígitos (identifica banco/instituição)
        # Últimos 4: identifica cartão específico
        bin_number = f"{random.randint(100000, 999999)}"
        last_four = f"{random.randint(1000, 9999)}"
        card_number = f"{bin_number}****{last_four}"
        
        data.append({
            'TRANSACTION_ID': f"TXN{i+1:06d}",
            'TRANSACTION_DATE': transaction_date.strftime('%d/%m/%Y %H:%M'),
            'CARDHOLDER': cardholder_name,
            'ESTABLISHMENT_NAME': establishment_name,
            'ESTABLISHMENT_CNPJ': cnpj,
            'MCC': mcc,
            'VALUE': round(value, 2),
            'CHANNEL': channel,
            'CARD_NUMBER': card_number,
            'STATUS': 'APPROVED',
        })
    
    return pd.DataFrame(data)


def generate_sample_mcc_limits():
    """Gera limites de MCC de exemplo"""
    data = {
        'MCC': ['5411', '7299', '4511', '5812', '5814'],
        'DESCRIPTION': ['Supermercados', 'Serviços', 'Aeroporto', 'Restaurante', 'Fast Food'],
        'LIMIT': [5000, 3000, 15000, 2000, 1000],
    }
    return pd.DataFrame(data)


def generate_sample_restricted_portadores():
    """Gera lista de portadores restritos de exemplo"""
    data = {
        'CARDHOLDER': ['FRAUDE CONHECIDA', 'BLOQUEADO TEMPORAL'],
        'CARD_NUMBER': ['123456****9999', '654321****8888'],
        'REASON': ['Fraude confirmada', 'Cartão bloqueado temporariamente'],
    }
    return pd.DataFrame(data)


def generate_sample_averages():
    """Gera médias de estabelecimento de exemplo"""
    data = {
        'ESTABLISHMENT_CNPJ': ['12345678901234', '98765432109876', '11111111111111', '22222222222222'],
        'AVERAGE_VALUE': [350.00, 280.00, 320.00, 450.00],
    }
    return pd.DataFrame(data)
