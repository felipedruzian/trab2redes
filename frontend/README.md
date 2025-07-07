# Sistema de Consulta Integrada

Sistema web para consulta de informações de pessoas físicas e jurídicas, integrando dados de múltiplos bancos SQLite.

## Tecnologias

- **Backend**: Python + Flask
- **Frontend**: Vue.js 3 + Axios
- **Banco de dados**: SQLite (basecpf.db e cnpj.db)

## Funcionalidades

- Busca por CPF/Nome de pessoas
- Busca por CNPJ de empresas  
- Visualização de empresas associadas a uma pessoa
- Visualização de sócios de uma empresa
- Validação automática de CPF/CNPJ

## Como Executar

### 1. Backend (Flask)
```bash
# Na pasta raiz do projeto
python app.py
```
Backend disponível em: http://localhost:5000

### 2. Frontend (Vue.js)
```bash
# Na pasta frontend/
npm install
npm run serve
```
Frontend disponível em: http://localhost:8080

## Requisitos

- Python 3.7+
- Node.js 14+
- Bancos de dados: `basecpf.db` e `cnpj.db` na pasta `backend/`
