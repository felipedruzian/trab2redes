from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re
import logging
from functools import wraps
from backend.config import API_CONFIG, CORS_CONFIG, LOGGING_CONFIG
from backend.databases import (
    search_person,
    search_person_parallel,
    search_company_by_cnpj,
    search_partners_by_cnpj,
    search_companies_by_cpf,
    search_company_with_partners_parallel,
    search_person_companies_parallel,
    get_db
)

# Configurar logging
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, **CORS_CONFIG)

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

# Rotas
@app.route('/')
def index():
    return send_from_directory('frontend/public', 'index.html')

@app.route('/api/search_person', methods=['POST'])
@handle_errors
def search_person_endpoint():
    data = request.get_json()
    query = data.get('query', '').strip() if data else ''

    if not query:
        return jsonify({'error': 'Query é obrigatória'}), 400

    people = search_person_parallel(query)
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
    
    # Usar a versão paralela para melhor performance
    result = search_company_with_partners_parallel(cnpj_clean)
    company = result['company']
    partners = result['partners']

    if not company:
        return jsonify({
            'message': 'Empresa não encontrada',
            'type': 'company_not_found',
            'data': None
        })

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
    
    # Usar a versão paralela para melhor performance
    result = search_person_companies_parallel(cpf_clean)
    companies = result['companies']

    return jsonify({
        'message': f'Encontradas {len(companies)} empresa(s)',
        'type': 'person_companies',
        'data': companies
    })

@app.route('/api/health', methods=['GET'])
@handle_errors
def health_check():
    try:
        with get_db('basecpf.db'), get_db('cnpj.db'):
            return jsonify({'status': 'healthy', 'databases': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    logger.info(f"Servidor rodando em http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    app.run(host=API_CONFIG['host'], port=API_CONFIG['port'], debug=API_CONFIG['debug'])