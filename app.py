from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import re
import logging
from contextlib import contextmanager
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from config import check_databases, API_CONFIG, CORS_CONFIG, THREAD_CONFIG, LOGGING_CONFIG

# Configuração
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG['level']), format=LOGGING_CONFIG['format'])
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=CORS_CONFIG['origins'])
executor = ThreadPoolExecutor(max_workers=THREAD_CONFIG['max_workers'])

if not check_databases():
    logger.warning("Alguns bancos de dados não foram encontrados.")

# Utilitários
def validate_document(doc, doc_type):
    """Valida CPF ou CNPJ"""
    doc = re.sub(r'\D', '', doc)

    if doc_type == 'cpf':
        if len(doc) != 11 or doc == doc[0] * 11:
            return False
        # Validação do primeiro dígito
        sum1 = sum(int(doc[i]) * (10 - i) for i in range(9))
        digit1 = ((sum1 * 10) % 11) % 10
        # Validação do segundo dígito
        sum2 = sum(int(doc[i]) * (11 - i) for i in range(10))
        digit2 = ((sum2 * 10) % 11) % 10
        return doc[-2:] == f"{digit1}{digit2}"

    elif doc_type == 'cnpj':
        if len(doc) != 14:
            return False
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(doc[i]) * weights1[i] for i in range(12))
        sum2 = sum(int(doc[i]) * weights2[i] for i in range(13))
        digit1 = 0 if (sum1 % 11) < 2 else (11 - (sum1 % 11))
        digit2 = 0 if (sum2 % 11) < 2 else (11 - (sum2 % 11))
        return doc[-2:] == f"{digit1}{digit2}"

    return False

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

        if len(query_clean) == 11 and validate_document(query_clean, 'cpf'):
            cursor.execute("SELECT * FROM cpf WHERE cpf = ?", (query_clean,))
            result = cursor.fetchone()
            return [dict(result)] if result else []
        else:
            cursor.execute("SELECT * FROM cpf WHERE nome LIKE ? LIMIT 100", (f"%{query}%",))
            return [dict(row) for row in cursor.fetchall()]

def search_companies_by_cpf(cpf):
    """Busca empresas por CPF do sócio"""
    with get_db('cnpj.db') as conn:
        cursor = conn.cursor()
        query = """
        SELECT DISTINCT 
            e.cnpj_basico, e.razao_social, e.natureza_juridica, e.porte_empresa, e.capital_social,
            est.cnpj, est.nome_fantasia, est.situacao_cadastral, est.data_inicio_atividades,
            est.logradouro, est.numero, est.bairro, est.cep, est.uf, est.municipio,
            s.qualificacao_socio, s.data_entrada_sociedade
        FROM socios s
        JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        LEFT JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico AND est.matriz_filial = '1'
        WHERE s.cnpj_cpf_socio = ?
        """
        cursor.execute(query, (cpf,))
        return [dict(row) for row in cursor.fetchall()]

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
    """Busca sócios por CNPJ da empresa"""
    partners = []

    with get_db('cnpj.db') as conn_cnpj, get_db('basecpf.db') as conn_cpf:
        cursor_cnpj = conn_cnpj.cursor()
        cursor_cpf = conn_cpf.cursor()

        query = """
        SELECT cnpj_cpf_socio, nome_socio, qualificacao_socio, data_entrada_sociedade, faixa_etaria
        FROM socios WHERE cnpj = ?
        """
        cursor_cnpj.execute(query, (cnpj,))

        for row in cursor_cnpj.fetchall():
            partner = dict(row)
            cpf_socio = partner['cnpj_cpf_socio']

            # Se for CPF, buscar dados completos
            if cpf_socio and len(re.sub(r'\D', '', cpf_socio)) == 11:
                cursor_cpf.execute("SELECT nome, sexo, nasc FROM cpf WHERE cpf = ?", (cpf_socio,))
                person_data = cursor_cpf.fetchone()
                if person_data:
                    person_dict = dict(person_data)
                    # Renomear para ficar mais claro
                    partner['cpf'] = cpf_socio
                    partner['nome_completo'] = person_dict.get('nome')
                    partner['sexo'] = person_dict.get('sexo')
                    partner['data_nascimento'] = person_dict.get('nasc')

            partners.append(partner)

    return partners

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

    if not validate_document(cnpj, 'cnpj'):
        return jsonify({'error': 'CNPJ inválido'}), 400

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

    if not validate_document(cpf, 'cpf'):
        return jsonify({'error': 'CPF inválido'}), 400

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