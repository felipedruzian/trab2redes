from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import wraps
from config import DATABASE_CONFIG, API_CONFIG, CORS_CONFIG, THREAD_CONFIG, LOGGING_CONFIG

# Configurar logging
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, **CORS_CONFIG)
executor = ThreadPoolExecutor(max_workers=THREAD_CONFIG['max_workers'])

# Função removida: validate_document (agora validação é feita no frontend)

@contextmanager
def get_db(db_name):
    """Context manager para conexões de banco"""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Erro no banco {db_name}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def handle_errors(f):
    """Decorator para tratamento de erros"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em {f.__name__}: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    return wrapper

# Funções de busca
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

def search_partners_by_cnpj(cnpj):
    """Busca sócios por CNPJ da empresa - retorna apenas dados básicos"""
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

# Rotas
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/search_person', methods=['POST'])
@handle_errors
def search_person_endpoint():
    data = request.get_json()
    query = data.get('query', '').strip() if data else ''
    
    if not query:
        return jsonify({'error': 'Query é obrigatória'}), 400
    
    people = search_person(query)
    return jsonify({
        'message': f'Encontradas {len(people)} pessoa(s)',
        'type': 'people_list',
        'people': people
    })

@app.route('/api/search_company', methods=['POST'])
@handle_errors
def search_company_endpoint():
    data = request.get_json()
    cnpj = data.get('cnpj', '').strip() if data else ''

    if not cnpj:
        return jsonify({'error': 'CNPJ é obrigatório'}), 400

    # Remover máscara do CNPJ (validação já foi feita no frontend)
    cnpj_clean = re.sub(r'\D', '', cnpj)
    company = search_company_by_cnpj(cnpj_clean)

    if not company:
        return jsonify({
            'message': 'Empresa não encontrada',
            'type': 'company_not_found',
            'data': None
        })

    partners = search_partners_by_cnpj(cnpj_clean)
    return jsonify({
        'message': 'Empresa encontrada',
        'type': 'company_data',
        'data': {
            'company': company,
            'partners': partners
        }
    })

@app.route('/api/person_companies', methods=['POST'])
@handle_errors
def get_person_companies():
    data = request.get_json()
    cpf = data.get('cpf', '').strip() if data else ''

    if not cpf:
        return jsonify({'error': 'CPF é obrigatório'}), 400

    # Remover máscara do CPF (validação já foi feita no frontend)
    cpf_clean = re.sub(r'\D', '', cpf)
    companies = search_companies_by_cpf(cpf_clean)

    return jsonify({
        'message': f'Encontradas {len(companies)} empresa(s)',
        'type': 'person_companies',
        'data': companies
    })



@app.route('/api/health', methods=['GET'])
@handle_errors
def health_check():
    with get_db('basecpf.db'), get_db('cnpj.db'):
        return jsonify({'status': 'healthy', 'databases': 'connected'})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    logger.info(f"Servidor rodando em http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    app.run(host=API_CONFIG['host'], port=API_CONFIG['port'], debug=API_CONFIG['debug'])