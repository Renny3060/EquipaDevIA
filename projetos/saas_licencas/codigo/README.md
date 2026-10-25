# Sistema Comercial de Gestão e Validação de Licenças de Software

Este é um backend REST completo em Python utilizando a framework FastAPI e base de dados SQLite para gerir clientes e validar as chaves dos softwares vendidos.

## Instalação

Primeiro, clone o repositório do projeto:

```bash
git clone https://github.com/your-repo/sistema-comercial.git
cd sistema-comercial
```

Em seguida, instale as dependências necessárias com pip:

```bash
pip install -r requirements.txt
```

## Execução

Para executar o servidor FastAPI, utilize o seguinte comando:

```bash
uvicorn main:app --reload
```

Isso iniciará a aplicação em modo de desenvolvimento e estará disponível no endereço `http://127.0.0.1:8000`.

## Estrutura do Projeto

O projeto está estruturado da seguinte forma:

- **database.py**: Configuração e conexão com o SQLite via SQLAlchemy.
- **crud.py**: Funções CRUD para operações no banco de dados.
- **main.py**: Ponto de entrada da aplicação FastAPI, definindo os endpoints.
- **models.py**: Definições das tabelas do banco de dados.
- **schemas.py**: Definições dos modelos Pydantic para validação estrita das entradas/saídas.

## Exemplos de Uso

### Geração de Licenças

Para gerar uma nova licença, envie um POST request com o email do cliente e o prazo de validade em dias:

```bash
curl -X POST "http://127.0.0.1:8000/api/licenses" \
-H "Content-Type: application/json" \
-d '{"email": "example@example.com", "days_validity": 365}'
```

### Validação de Licenças

Para validar uma licença, envie um POST request com a chave da licença:

```bash
curl -X POST "http://127.0.0.1:8000/api/validate" \
-H "Content-Type: application/json" \
-d '{"license_key": "XXXX-XXXX-XXXX-XXXX"}'
```

### Revogação de Licenças

Para revogar uma licença, envie um POST request com a chave da licença:

```bash
curl -X POST "http://127.0.0.1:8000/api/revoke" \
-H "Content-Type: application/json" \
-d '{"license_key": "XXXX-XXXX-XXXX-XXXX"}'
```

## Documentação Adicional

Para obter mais informações sobre os endpoints disponíveis e exemplos de uso, consulte a documentação interativa gerada pelo FastAPI:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Testes

Para executar os testes unitários automáticos, utilize o seguinte comando:

```bash
pytest
```

Isso rodará todos os testes definidos no diretório `tests`.

Este backend foi criado seguindo rigorosamente as regras de negócio e requisitos técnicos fornecidos.
