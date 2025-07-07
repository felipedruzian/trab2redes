# Configuração para desenvolvimento
import os

# Configurações do banco de dados
DATABASE_CONFIG = {
    'basecpf': 'backend/basecpf.db',
    'cnpj': 'backend/cnpj.db'
}

# Configurações da API
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Configurações de CORS
CORS_CONFIG = {
    'origins': ['*'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'allow_headers': ['Content-Type', 'Authorization']
}

# Configurações de threading
THREAD_CONFIG = {
    'max_workers': 10
}

# Verificar se os bancos de dados existem
def check_databases():
    """Verifica se os bancos de dados existem"""
    missing_dbs = []
    for name, path in DATABASE_CONFIG.items():
        if not os.path.exists(path):
            missing_dbs.append(path)
    
    if missing_dbs:
        print(f"AVISO: Os seguintes bancos de dados não foram encontrados:")
        for db in missing_dbs:
            print(f"  - {db}")
        print("Certifique-se de que os arquivos de banco de dados estão no diretório backend.")
        return False
    return True

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}