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
- **Frontend**: Vue.js 3 + HTML/CSS/JavaScript
- **Banco de dados**: SQLite (basecpf.db e cnpj.db)
- **Validação**: Validação nativa de CPF/CNPJ
- **CORS**: Habilitado para comunicação entre frontend e backend

## Pré-requisitos

- Python 3.7+
- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Bancos de dados SQLite: `basecpf.db` e `cnpj.db`

## Instalação

1. **Clone ou baixe o projeto**
   ```bash
   # Se estiver usando git
   git clone [url-do-repositorio]
   cd sistema-consulta
   ```

2. **Instale as dependências Python**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verifique se os bancos de dados estão presentes**
   - Certifique-se que os arquivos `basecpf.db` e `cnpj.db` estão na raiz do projeto
   - Estes arquivos devem ser fornecidos pelo professor

## Execução

### 1. Iniciar o Backend

```bash
python app.py
```

O backend será iniciado em `http://localhost:5000`

### 2. Abrir o Frontend

Simplesmente abra o arquivo `index.html` em seu navegador web. Você pode:

- Dar duplo clique no arquivo `index.html`
- Ou usar um servidor web simples (opcional):
  ```bash
  # Python 3
  python -m http.server 8080
  
  # Então acesse: http://localhost:8080
  ```

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

## Estrutura dos Bancos de Dados

### basecpf.db
- **Tabela**: `cpf`
- **Campos**: cpf, nome, sexo, data_nascimento, etc.

### cnpj.db
- **Tabela**: `empresas` - dados das empresas
- **Tabela**: `socios` - relacionamento entre empresas e sócios
- **Campos**: cnpj, razao_social, nome_fantasia, situacao, etc.

## Endpoints da API

### GET /api/health
Verifica se a API está funcionando.

### POST /api/search_person
Busca pessoa por CPF ou nome.
```json
{
    "query": "12345678901" // CPF ou nome
}
```

### POST /api/search_company
Busca empresa por CNPJ.
```json
{
    "cnpj": "12345678000195"
}
```

### POST /api/person_companies
Busca empresas de uma pessoa específica.
```json
{
    "cpf": "12345678901"
}
```

## Estrutura de Arquivos

```
projeto/
├── app.py              # Backend Flask
├── index.html          # Frontend Vue.js
├── requirements.txt    # Dependências Python
├── README.md          # Este arquivo
├── basecpf.db         # Banco de dados CPF
└── cnpj.db            # Banco de dados CNPJ
```

## Tratamento de Erros

- **CPF/CNPJ inválido**: Validação automática no frontend e backend
- **Dados não encontrados**: Mensagem de erro clara
- **Problemas de conexão**: Mensagens de erro informativas
- **Validação de entrada**: Campos obrigatórios e formato correto

## Desenvolvimento

### Modificações no Backend

Para adicionar novos endpoints ou modificar a lógica de busca, edite o arquivo `app.py`.

### Modificações no Frontend

Para alterar a interface, edite o arquivo `index.html`. O Vue.js está incluído via CDN.

## Solução de Problemas

1. **"Erro de CORS"**: Certifique-se que o backend está rodando em `http://localhost:5000`
2. **"Banco de dados não encontrado"**: Verifique se os arquivos `.db` estão na raiz do projeto
3. **"Módulo não encontrado"**: Execute `pip install -r requirements.txt`
4. **"Porta em uso"**: Altere a porta no arquivo `app.py` se necessário

## Notas Técnicas

- O sistema usa múltiplas threads para consultas aos bancos de dados
- A validação de CPF e CNPJ segue os algoritmos oficiais
- O frontend é uma Single Page Application (SPA) simples
- Todas as consultas são feitas via AJAX/API REST
- Os dados são retornados em formato JSON estruturado