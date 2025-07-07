from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import threading
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from config import check_databases, API_CONFIG, CORS_CONFIG, THREAD_CONFIG, LOGGING_CONFIG

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=CORS_CONFIG['origins'])

# Configuração para usar threads
executor = ThreadPoolExecutor(max_workers=THREAD_CONFIG['max_workers'])

# Verificar bancos de dados na inicialização
if not check_databases():
    logger.warning("Alguns bancos de dados não foram encontrados. A aplicação pode não funcionar corretamente.")

def validate_cpf(cpf):
    """Valida se o CPF é válido"""
    try:
        cpf = re.sub(r'\D', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Validação do primeiro dígito
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = ((sum1 * 10) % 11) % 10
        
        # Validação do segundo dígito
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = ((sum2 * 10) % 11) % 10
        
        return cpf[-2:] == f"{digit1}{digit2}"
    except Exception as e:
        logger.error(f"Erro na validação do CPF: {e}")
        return False

def validate_cnpj(cnpj):
    """Valida se o CNPJ é válido"""
    try:
        cnpj = re.sub(r'\D', '', cnpj)
        if len(cnpj) != 14:
            return False
        
        # Validação do primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = ((sum1 % 11) < 2) and 0 or (11 - (sum1 % 11))
        
        # Validação do segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = ((sum2 % 11) < 2) and 0 or (11 - (sum2 % 11))
        
        return cnpj[-2:] == f"{digit1}{digit2}"
    except Exception as e:
        logger.error(f"Erro na validação do CNPJ: {e}")
        return False

def get_db_connection(db_name):
    """Obtém conexão com o banco de dados"""
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar com o banco {db_name}: {e}")
        raise

def search_person_by_cpf(cpf):
    """Busca pessoa por CPF no banco basecpf.db"""
    conn = None
    try:
        conn = get_db_connection('basecpf.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cpf WHERE cpf = ?", (cpf,))
        person = cursor.fetchone()
        return dict(person) if person else None
    except Exception as e:
        logger.error(f"Erro ao buscar por CPF {cpf}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def search_person_by_name(name):
    """Busca pessoas por nome no banco basecpf.db"""
    conn = None
    try:
        conn = get_db_connection('basecpf.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cpf WHERE nome LIKE ? LIMIT 100", (f"%{name}%",))
        people = cursor.fetchall()
        return [dict(person) for person in people]
    except Exception as e:
        logger.error(f"Erro ao buscar por nome {name}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def search_companies_by_cpf(cpf):
    """Busca empresas associadas a um CPF no banco CNPJ.db"""
    conn = None
    try:
        conn = get_db_connection('cnpj.db')
        cursor = conn.cursor()
        
        # Busca CNPJs dos sócios
        cursor.execute("SELECT DISTINCT cnpj FROM socios WHERE cpf = ?", (cpf,))
        cnpjs = cursor.fetchall()
        
        companies = []
        for cnpj_row in cnpjs:
            cnpj = cnpj_row['cnpj']
            # Busca dados da empresa
            cursor.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
            company = cursor.fetchone()
            if company:
                companies.append(dict(company))
        
        return companies
    except Exception as e:
        logger.error(f"Erro ao buscar empresas por CPF {cpf}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def search_company_by_cnpj(cnpj):
    """Busca empresa por CNPJ no banco CNPJ.db"""
    conn = None
    try:
        conn = get_db_connection('cnpj.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
        company = cursor.fetchone()
        return dict(company) if company else None
    except Exception as e:
        logger.error(f"Erro ao buscar empresa por CNPJ {cnpj}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def search_partners_by_cnpj(cnpj):
    """Busca sócios de uma empresa por CNPJ"""
    conn_cnpj = None
    conn_cpf = None
    try:
        conn_cnpj = get_db_connection('cnpj.db')
        conn_cpf = get_db_connection('basecpf.db')
        
        cursor_cnpj = conn_cnpj.cursor()
        cursor_cpf = conn_cpf.cursor()
        
        # Busca CPFs dos sócios
        cursor_cnpj.execute("SELECT cpf FROM socios WHERE cnpj = ?", (cnpj,))
        cpfs = cursor_cnpj.fetchall()
        
        partners = []
        for cpf_row in cpfs:
            cpf = cpf_row['cpf']
            # Busca dados da pessoa
            cursor_cpf.execute("SELECT * FROM cpf WHERE cpf = ?", (cpf,))
            person = cursor_cpf.fetchone()
            if person:
                partners.append(dict(person))
        
        return partners
    except Exception as e:
        logger.error(f"Erro ao buscar sócios por CNPJ {cnpj}: {e}")
        return []
    finally:
        if conn_cnpj:
            conn_cnpj.close()
        if conn_cpf:
            conn_cpf.close()

# ROTA PRINCIPAL - Serve o frontend
@app.route('/')
def index():
    """Serve a página principal (frontend)"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Erro ao servir index.html: {e}")
        return jsonify({'error': 'Arquivo index.html não encontrado'}), 404

@app.route('/api/search_person', methods=['POST'])
def search_person():
    """Endpoint para buscar pessoas por CPF ou nome"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query é obrigatório'}), 400
        
        # Verifica se é CPF ou nome
        if re.match(r'^\d{11}$', re.sub(r'\D', '', query)):
            # É CPF
            cpf = re.sub(r'\D', '', query)
            if not validate_cpf(cpf):
                return jsonify({'error': 'CPF inválido'}), 400
            
            person = search_person_by_cpf(cpf)
            if person:
                companies = search_companies_by_cpf(cpf)
                return jsonify({
                    'type': 'person',
                    'person': person,
                    'companies': companies
                })
            else:
                return jsonify({'error': 'Pessoa não encontrada'}), 404
        else:
            # É nome
            people = search_person_by_name(query)
            return jsonify({
                'type': 'people_list',
                'people': people
            })
    
    except Exception as e:
        logger.error(f"Erro no endpoint search_person: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/search_company', methods=['POST'])
def search_company():
    """Endpoint para buscar empresa por CNPJ"""
    try:
        data = request.json
        cnpj = data.get('cnpj', '').strip()
        
        if not cnpj:
            return jsonify({'error': 'CNPJ é obrigatório'}), 400
        
        cnpj = re.sub(r'\D', '', cnpj)
        if not validate_cnpj(cnpj):
            return jsonify({'error': 'CNPJ inválido'}), 400
        
        company = search_company_by_cnpj(cnpj)
        if company:
            partners = search_partners_by_cnpj(cnpj)
            return jsonify({
                'type': 'company',
                'company': company,
                'partners': partners
            })
        else:
            return jsonify({'error': 'Empresa não encontrada'}), 404
    
    except Exception as e:
        logger.error(f"Erro no endpoint search_company: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/person_companies', methods=['POST'])
def get_person_companies():
    """Endpoint para buscar empresas de uma pessoa específica"""
    try:
        data = request.json
        cpf = data.get('cpf', '').strip()
        
        if not cpf:
            return jsonify({'error': 'CPF é obrigatório'}), 400
        
        cpf = re.sub(r'\D', '', cpf)
        if not validate_cpf(cpf):
            return jsonify({'error': 'CPF inválido'}), 400
        
        person = search_person_by_cpf(cpf)
        if person:
            companies = search_companies_by_cpf(cpf)
            return jsonify({
                'person': person,
                'companies': companies
            })
        else:
            return jsonify({'error': 'Pessoa não encontrada'}), 404
    
    except Exception as e:
        logger.error(f"Erro no endpoint person_companies: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'OK', 
        'message': 'API funcionando corretamente',
        'databases': {
            'basecpf.db': 'disponível' if check_databases() else 'indisponível',
            'cnpj.db': 'disponível' if check_databases() else 'indisponível'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    logger.info("Iniciando servidor Flask...")
    logger.info(f"Servidor rodando em http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info("Acesse http://localhost:5000 para usar a aplicação")
    app.run(
        debug=API_CONFIG['debug'], 
        host=API_CONFIG['host'], 
        port=API_CONFIG['port']
    )