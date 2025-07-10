import sqlite3
import re
import logging
from multiprocessing import Pool
from contextlib import contextmanager
import sys
import os

# Adicionar o diretório pai ao path para permitir imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import DATABASE_CONFIG, THREAD_CONFIG

logger = logging.getLogger(__name__)

@contextmanager
def get_db(db_name):
    """Context manager para conexões de banco"""
    conn = None
    try:
        db_path = DATABASE_CONFIG.get(db_name.replace('.db', ''), db_name)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Erro no banco {db_name}: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Funções de busca originais (mantidas para compatibilidade)
def search_person(query):
    """Busca pessoa por CPF ou nome"""
    with get_db('basecpf.db') as conn:
        cursor = conn.cursor()
        query_clean = re.sub(r'\D', '', query)

        # Se parece ser um CPF (11 dígitos), buscar exato
        if len(query_clean) == 11:
            cursor.execute("SELECT * FROM cpf WHERE cpf = ?", (query_clean,))
            result = cursor.fetchone()
            return [dict(result)] if result else []
        else:
            # Buscar por nome (parcial)
            cursor.execute("SELECT * FROM cpf WHERE nome LIKE ? LIMIT 100", (f"%{query}%",))
            return [dict(row) for row in cursor.fetchall()]

def search_companies_by_cpf(cpf):
    """Busca empresas por CPF do sócio"""
    with get_db('cnpj.db') as conn:
        cursor = conn.cursor()

        # Extrair os 6 dígitos do meio do CPF (posições 4-9)
        cpf_middle = cpf[3:9] if len(cpf) == 11 else cpf

        # Buscar pessoa no banco de CPF para obter o nome
        pessoa = None
        with get_db('basecpf.db') as conn_cpf:
            cursor_cpf = conn_cpf.cursor()
            cursor_cpf.execute("SELECT nome FROM cpf WHERE cpf = ?", (cpf,))
            result = cursor_cpf.fetchone()
            pessoa = dict(result) if result else None

        # Query para buscar por CPF parcial e/ou nome
        query = """
        SELECT DISTINCT
            e.cnpj_basico, e.razao_social, e.natureza_juridica, e.porte_empresa, e.capital_social,
            est.cnpj, est.nome_fantasia, est.situacao_cadastral, est.data_inicio_atividades,
            est.logradouro, est.numero, est.bairro, est.cep, est.uf, est.municipio,
            s.qualificacao_socio, s.data_entrada_sociedade, s.cnpj_cpf_socio, s.nome_socio
        FROM socios s
        JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        LEFT JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico AND est.matriz_filial = '1'
        WHERE s.cnpj_cpf_socio LIKE ? OR (? IS NOT NULL AND s.nome_socio LIKE ?)
        """

        # Parâmetros da query
        cpf_pattern = f"%{cpf_middle}%"
        nome_pattern = f"%{pessoa['nome']}%" if pessoa else None

        cursor.execute(query, (cpf_pattern, nome_pattern, nome_pattern))
        results = cursor.fetchall()

        # Filtrar resultados para garantir que o match de CPF seja mais preciso
        filtered_results = []
        for row in results:
            row_dict = dict(row)

            # Verificar se o CPF parcial contém os dígitos do meio
            if row_dict['cnpj_cpf_socio'] and cpf_middle in row_dict['cnpj_cpf_socio']:
                filtered_results.append(row_dict)
            # Ou se o nome bate (caso exista)
            elif pessoa and row_dict['nome_socio'] and pessoa['nome'].upper() in row_dict['nome_socio'].upper():
                filtered_results.append(row_dict)

        return filtered_results

def search_company_by_cnpj(cnpj):
    """Busca empresa por CNPJ"""
    with get_db('cnpj.db') as conn:
        cursor = conn.cursor()
        query = """
        SELECT 
            e.cnpj_basico, e.razao_social, e.natureza_juridica, e.porte_empresa, e.capital_social,
            est.cnpj, est.nome_fantasia, est.situacao_cadastral, est.data_inicio_atividades,
            est.logradouro, est.numero, est.bairro, est.cep, est.uf, est.municipio
        FROM empresas e
        JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico
        WHERE est.cnpj = ?
        """
        cursor.execute(query, (cnpj,))
        result = cursor.fetchone()
        return dict(result) if result else None

# Função auxiliar para multiprocessing - deve estar no nível do módulo
def get_partner_with_details(partner):
    """Busca detalhes completos de um sócio específico"""
    cnpj_cpf_socio = partner['cnpj_cpf_socio']
    nome_socio = partner['nome_socio']
    
    partner_details = search_partner_details(cnpj_cpf_socio, nome_socio)
    
    if partner_details:
        partner['cpf'] = partner_details['cpf']
        partner['nome_completo'] = partner_details['nome']
        partner['sexo'] = partner_details['sexo']
        partner['data_nascimento'] = partner_details['nasc']
        
    return partner

def search_partners_by_cnpj(cnpj):
    """Busca sócios por CNPJ da empresa - versão sequencial"""
    partners = []

    with get_db('cnpj.db') as conn_cnpj:
        cursor_cnpj = conn_cnpj.cursor()

        query = """
        SELECT cnpj_cpf_socio, nome_socio, qualificacao_socio, data_entrada_sociedade, faixa_etaria
        FROM socios WHERE cnpj = ?
        """
        cursor_cnpj.execute(query, (cnpj,))

        for row in cursor_cnpj.fetchall():
            partner = dict(row)
            cnpj_cpf_socio = partner['cnpj_cpf_socio']
            nome_socio = partner['nome_socio']

            # Buscar dados completos no basecpf.db
            partner_details = search_partner_details(cnpj_cpf_socio, nome_socio)

            if partner_details:
                # Adicionar dados completos ao partner
                partner['cpf'] = partner_details['cpf']
                partner['nome_completo'] = partner_details['nome']
                partner['sexo'] = partner_details['sexo']
                partner['data_nascimento'] = partner_details['nasc']

            partners.append(partner)

    return partners

def search_partners_basic_by_cnpj(cnpj):
    """Busca dados básicos dos sócios por CNPJ da empresa"""
    with get_db('cnpj.db') as conn_cnpj:
        cursor_cnpj = conn_cnpj.cursor()

        query = """
        SELECT cnpj_cpf_socio, nome_socio, qualificacao_socio, data_entrada_sociedade, faixa_etaria
        FROM socios WHERE cnpj = ?
        """
        cursor_cnpj.execute(query, (cnpj,))
        return [dict(row) for row in cursor_cnpj.fetchall()]

def search_partner_details(cnpj_cpf_socio, nome_socio):
    """Busca dados completos de um sócio específico usando CPF parcial e nome"""
    with get_db('basecpf.db') as conn_cpf:
        cursor_cpf = conn_cpf.cursor()

        # Extrair os dígitos do meio do CPF parcial (formato: ***456789**)
        # Remove os 3 asteriscos do início e 2 do final
        cpf_digits = cnpj_cpf_socio[3:-2] if len(cnpj_cpf_socio) >= 6 else cnpj_cpf_socio

        # Buscar pessoa que tenha esses dígitos no CPF e nome exato
        query = """
        SELECT cpf, nome, sexo, nasc
        FROM cpf
        WHERE cpf LIKE ? AND nome = ?
        LIMIT 1
        """
        cursor_cpf.execute(query, (f"%{cpf_digits}%", nome_socio))

        result = cursor_cpf.fetchone()
        return dict(result) if result else None


# ----------- Novas funções com multiprocessing
def search_person_parallel(query):
    """Busca pessoa com otimização paralela se necessário"""
    # Para busca simples, não há muito a paralelizar
    return search_person(query)

def search_company_with_partners_parallel(cnpj):
    """Busca empresa e sócios em paralelo - refatorado para evitar processos aninhados"""
    # Primeiro buscar dados básicos
    with Pool(processes=2) as pool:
        # Executar buscas básicas em paralelo
        future_company = pool.apply_async(search_company_by_cnpj, (cnpj,))
        future_partners_basic = pool.apply_async(search_partners_basic_by_cnpj, (cnpj,))
        
        # Aguardar resultados
        company = future_company.get()
        partners_basic = future_partners_basic.get()
    
    # Se não há sócios, retornar apenas empresa
    if not partners_basic:
        return {
            'company': company,
            'partners': []
        }
    
    # Agora buscar detalhes de cada sócio em paralelo
    with Pool(processes=THREAD_CONFIG['max_workers']) as pool:
        partners_with_details = pool.map(get_partner_with_details, partners_basic)
    
    return {
        'company': company,
        'partners': partners_with_details
    }

def search_person_companies_parallel(cpf):
    """Busca pessoa e empresas em paralelo"""
    with Pool(processes=2) as pool:
        # Buscar dados da pessoa e empresas simultaneamente
        future_person = pool.apply_async(search_person, (cpf,))
        future_companies = pool.apply_async(search_companies_by_cpf, (cpf,))
        
        person_data = future_person.get()
        companies_data = future_companies.get()
        
        return {
            'person': person_data,
            'companies': companies_data
        }