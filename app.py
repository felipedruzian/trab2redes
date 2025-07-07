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

def search_person(query):
    """Busca pessoa por CPF ou nome no banco basecpf.db"""
    conn = None
    try:
        conn = get_db_connection('basecpf.db')
        cursor = conn.cursor()
        
        # Verificar se é CPF ou nome
        query_clean = re.sub(r'\D', '', query)
        
        if len(query_clean) == 11 and validate_cpf(query_clean):
            # Busca por CPF
            cursor.execute("SELECT * FROM cpf WHERE cpf = ?", (query_clean,))
            person = cursor.fetchone()
            return [dict(person)] if person else []
        else:
            
            
            # Fallback para busca com LIKE
            cursor.execute("SELECT * FROM cpf WHERE nome LIKE ? LIMIT 100", (f"%{query}%",))
            people = cursor.fetchall()
            return [dict(person) for person in people]
            
    except Exception as e:
        logger.error(f"Erro ao buscar pessoa {query}: {e}")
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
        
        # Busca empresas onde a pessoa é sócia
        query = """
        SELECT DISTINCT 
            e.cnpj_basico,
            e.razao_social,
            e.natureza_juridica,
            e.qualificacao_responsavel,
            e.porte_empresa,
            e.capital_social,
            est.cnpj,
            est.nome_fantasia,
            est.situacao_cadastral,
            est.data_situacao_cadastral,
            est.data_inicio_atividades,
            est.cnae_fiscal,
            est.logradouro,
            est.numero,
            est.complemento,
            est.bairro,
            est.cep,
            est.uf,
            est.municipio,
            est.telefone1,
            est.correio_eletronico,
            s.qualificacao_socio,
            s.data_entrada_sociedade
        FROM socios s
        JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        LEFT JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico AND est.matriz_filial = '1'
        WHERE s.cnpj_cpf_socio = ?
        """
        
        cursor.execute(query, (cpf,))
        companies = cursor.fetchall()
        
        return [dict(company) for company in companies]
        
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
        
        # Busca dados da empresa com estabelecimento
        query = """
        SELECT 
            e.cnpj_basico,
            e.razao_social,
            e.natureza_juridica,
            e.qualificacao_responsavel,
            e.porte_empresa,
            e.capital_social,
            est.cnpj,
            est.nome_fantasia,
            est.situacao_cadastral,
            est.data_situacao_cadastral,
            est.data_inicio_atividades,
            est.cnae_fiscal,
            est.logradouro,
            est.numero,
            est.complemento,
            est.bairro,
            est.cep,
            est.uf,
            est.municipio,
            est.telefone1,
            est.correio_eletronico
        FROM empresas e
        JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico
        WHERE est.cnpj = ?
        """
        
        cursor.execute(query, (cnpj,))
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
        
        # Busca sócios da empresa
        query = """
        SELECT DISTINCT 
            s.cnpj_cpf_socio,
            s.nome_socio,
            s.qualificacao_socio,
            s.data_entrada_sociedade,
            s.faixa_etaria,
            s.identificador_de_socio,
            s.representante_legal,
            s.nome_representante,
            s.qualificacao_representante_legal
        FROM socios s
        WHERE s.cnpj = ?
        """
        
        cursor_cnpj.execute(query, (cnpj,))
        partners_data = cursor_cnpj.fetchall()
        
        partners = []
        for partner_row in partners_data:
            partner = dict(partner_row)
            
            # Se o cnpj_cpf_socio for um CPF válido, buscar dados na tabela cpf
            cpf_socio = partner['cnpj_cpf_socio']
            if cpf_socio and len(re.sub(r'\D', '', cpf_socio)) == 11:
                cursor_cpf.execute("SELECT nome, sexo, nasc FROM cpf WHERE cpf = ?", (cpf_socio,))
                person_data = cursor_cpf.fetchone()
                if person_data:

                    partner.update(dict(person_data))
            
            partners.append(partner)
        
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
def search_person_endpoint():
    """Endpoint para buscar pessoas por CPF ou nome"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Parâmetro query é obrigatório'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Query não pode estar vazia'}), 400
        
        # Buscar pessoas (apenas pessoas, sem empresas)
        people = search_person(query)
        
        if not people:
            return jsonify({'message': 'Nenhuma pessoa encontrada', 'data': []}), 200
        
        return jsonify({
            'message': f'Encontradas {len(people)} pessoa(s)',
            'type': 'people_list',
            'people': people
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca por pessoa: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/search_company', methods=['POST'])
def search_company_endpoint():
    """Endpoint para buscar empresa por CNPJ"""
    try:
        data = request.get_json()
        if not data or 'cnpj' not in data:
            return jsonify({'error': 'Parâmetro cnpj é obrigatório'}), 400
        
        cnpj = data['cnpj'].strip()
        if not cnpj:
            return jsonify({'error': 'CNPJ não pode estar vazio'}), 400
        
        # Validar CNPJ
        if not validate_cnpj(cnpj):
            return jsonify({'error': 'CNPJ inválido'}), 400
        
        # Limpar CNPJ
        cnpj_clean = re.sub(r'\D', '', cnpj)
        
        # Buscar empresa
        company = search_company_by_cnpj(cnpj_clean)
        
        if not company:
            return jsonify({'message': 'Empresa não encontrada', 'data': None}), 200
        
        # Buscar sócios da empresa
        partners = search_partners_by_cnpj(cnpj_clean)
        
        return jsonify({
            'message': 'Empresa encontrada',
            'data': {
                'company': company,
                'partners': partners
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca por empresa: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/person_companies', methods=['POST'])
def get_person_companies():
    """Endpoint para buscar empresas de uma pessoa específica"""
    try:
        data = request.get_json()
        if not data or 'cpf' not in data:
            return jsonify({'error': 'Parâmetro cpf é obrigatório'}), 400
        
        cpf = data['cpf'].strip()
        if not cpf:
            return jsonify({'error': 'CPF é obrigatório'}), 400
        
        # Validar CPF
        if not validate_cpf(cpf):
            return jsonify({'error': 'CPF inválido'}), 400
        
        # Limpar CPF
        cpf_clean = re.sub(r'\D', '', cpf)
        
        # Buscar empresas da pessoa
        companies = search_companies_by_cpf(cpf_clean)
        
        return jsonify({
            'message': f'Encontradas {len(companies)} empresa(s) para o CPF {cpf}',
            'data': companies
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint person_companies: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    try:
        # Verificar conexão com os bancos
        conn_cpf = get_db_connection('basecpf.db')
        conn_cnpj = get_db_connection('cnpj.db')
        conn_cpf.close()
        conn_cnpj.close()
        
        return jsonify({'status': 'healthy', 'databases': 'connected'}), 200
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

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
        host=API_CONFIG['host'], 
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug']
    )