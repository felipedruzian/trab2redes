# Sistema de Consulta Integrada

Sistema web para consulta de informações de pessoas físicas e jurídicas, integrando dados de múltiplos bancos de dados SQLite.

## Funcionalidades

- **Busca por CPF/Nome**: Permite buscar pessoas por CPF ou nome completo/parcial
- **Busca por CNPJ**: Permite buscar empresas por CNPJ
- **Correlação de dados**: Mostra empresas associadas a uma pessoa e sócios associados a uma empresa
- **Validação**: Validação automática de CPF e CNPJ no frontend
- **Interface responsiva**: Interface web responsiva usando Vue.js

## Tecnologias Utilizadas

- **Backend**: Python + Flask
- **Frontend**: Vue.js 3 + Axios
- **Banco de dados**: SQLite (basecpf.db e cnpj.db)
- **Validação**: Validação nativa de CPF/CNPJ
- **CORS**: Habilitado para comunicação entre frontend e backend

## Pré-requisitos

- Python 3.7+
- Node.js 14+
- Bancos de dados SQLite: `basecpf.db` e `cnpj.db`

## Instalação e Execução

### 1. Backend (Flask)

```bash
# Instalar dependências Python
pip install -r requirements.txt

# Executar o backend
python app.py
```

O backend será iniciado em `http://localhost:5000`

### 2. Frontend (Vue.js)

```bash
# Entrar na pasta do frontend
cd frontend

# Instalar dependências
npm install

# Executar em modo desenvolvimento
npm run serve
```

O frontend será iniciado em `http://localhost:8080`

## Uso da Aplicação

### Busca por Pessoa (CPF/Nome)

1. Selecione a aba "Buscar Pessoa (CPF/Nome)"
2. Digite um CPF (apenas números) ou nome (completo ou parcial)
3. Clique em "Buscar"
4. Se buscar por nome, será exibida uma lista de pessoas encontradas
5. Clique em uma pessoa para ver seus dados e empresas associadas

### Busca por Empresa (CNPJ)

1. Selecione a aba "Buscar Empresa (CNPJ)"
2. Digite um CNPJ (apenas números ou formatado)
3. Clique em "Buscar"
4. Será exibida a empresa encontrada e todos os seus sócios

## Estrutura do Projeto

```
├── app.py              # Servidor Flask principal
├── backend/            # Configurações e acesso aos bancos
│   ├── config.py       # Configurações da aplicação
│   └── databases.py    # Funções de acesso ao banco
├── frontend/           # Aplicação Vue.js
│   ├── src/
│   │   ├── components/ # Componentes Vue
│   │   └── utils/      # Validadores CPF/CNPJ (validatores.js)
│   └── public/         # Arquivos públicos (index.html)
└── requirements.txt    # Dependências Python
```

## Produção

Para produção, faça o build do frontend:

```bash
cd frontend
npm run build
```

Os arquivos de produção ficarão em `frontend/dist/`