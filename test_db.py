#!/usr/bin/env python3
"""
Script para testar a conexão com os bancos de dados
"""

import sqlite3
import os
from config import DATABASE_CONFIG

def test_database_connection(db_name, db_path):
    """Testa a conexão com um banco de dados específico"""
    print(f"\n=== Testando {db_name} ===")
    
    if not os.path.exists(db_path):
        print(f"❌ Arquivo {db_path} não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ Conexão com {db_path} bem-sucedida!")
        print(f"📊 Tabelas encontradas: {[table[0] for table in tables]}")
        
        # Testa consultas simples em cada tabela (apenas os primeiros registros)
        for table in tables:
            table_name = table[0]
            try:
                # Testa apenas os primeiros 5 registros para ser rápido
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                
                if sample_data:
                    print(f"   - {table_name}: ✅ Tabela acessível (amostra: {len(sample_data)} registros)")
                else:
                    print(f"   - {table_name}: ⚠️  Tabela vazia")
                    
            except Exception as e:
                print(f"   - {table_name}: ❌ Erro ao acessar tabela - {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com {db_path}: {e}")
        return False

def test_specific_queries():
    """Testa consultas específicas do sistema"""
    print(f"\n=== Testando Consultas Específicas ===")
    
    try:
        # Teste no banco basecpf.db
        print("\n🧪 Testando consulta no basecpf.db...")
        conn_cpf = sqlite3.connect('basecpf.db')
        cursor_cpf = conn_cpf.cursor()
        
        # Testa estrutura da tabela cpf
        cursor_cpf.execute("PRAGMA table_info(cpf);")
        columns = cursor_cpf.fetchall()
        print(f"   Colunas da tabela 'cpf': {[col[1] for col in columns]}")
        
        # Testa uma consulta simples
        cursor_cpf.execute("SELECT * FROM cpf LIMIT 1;")
        sample = cursor_cpf.fetchone()
        if sample:
            print("   ✅ Consulta de teste bem-sucedida")
        
        conn_cpf.close()
        
        # Teste no banco cnpj.db
        print("\n🧪 Testando consulta no cnpj.db...")
        conn_cnpj = sqlite3.connect('cnpj.db')
        cursor_cnpj = conn_cnpj.cursor()
        
        # Testa estrutura das tabelas principais
        cursor_cnpj.execute("PRAGMA table_info(empresas);")
        columns = cursor_cnpj.fetchall()
        print(f"   Colunas da tabela 'empresas': {[col[1] for col in columns]}")
        
        cursor_cnpj.execute("PRAGMA table_info(socios);")
        columns = cursor_cnpj.fetchall()
        print(f"   Colunas da tabela 'socios': {[col[1] for col in columns]}")
        
        # Testa consultas simples
        cursor_cnpj.execute("SELECT * FROM empresas LIMIT 1;")
        sample_empresa = cursor_cnpj.fetchone()
        if sample_empresa:
            print("   ✅ Consulta de teste em 'empresas' bem-sucedida")
        
        cursor_cnpj.execute("SELECT * FROM socios LIMIT 1;")
        sample_socio = cursor_cnpj.fetchone()
        if sample_socio:
            print("   ✅ Consulta de teste em 'socios' bem-sucedida")
        
        conn_cnpj.close()
        
        print("   ✅ Todas as consultas específicas funcionaram!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nas consultas específicas: {e}")
        return False

def main():
    """Função principal para testar todos os bancos"""
    print("🧪 Testando conexões com os bancos de dados...")
    
    all_ok = True
    
    # Testa basecpf.db
    basecpf_ok = test_database_connection("Base CPF", DATABASE_CONFIG['basecpf'])
    all_ok = all_ok and basecpf_ok
    
    # Testa cnpj.db
    cnpj_ok = test_database_connection("CNPJ", DATABASE_CONFIG['cnpj'])
    all_ok = all_ok and cnpj_ok
    
    # Testa consultas específicas se os bancos estiverem OK
    if all_ok:
        queries_ok = test_specific_queries()
        all_ok = all_ok and queries_ok
    
    print(f"\n{'='*60}")
    if all_ok:
        print("✅ Todos os bancos de dados estão funcionando corretamente!")
        print("🚀 O sistema está pronto para uso!")
    else:
        print("❌ Alguns bancos de dados apresentaram problemas.")
        print("   Certifique-se de que os arquivos estão presentes no diretório raiz.")
    
    return all_ok

if __name__ == "__main__":
    main()