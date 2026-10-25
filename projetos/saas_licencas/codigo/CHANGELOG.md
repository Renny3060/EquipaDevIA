# Changelog

## 2026-10-10 22:42
```markdown
- **Correção do problema de inicialização da aplicação**: O comando `uvicorn main:app --reload` agora inicia a aplicação corretamente, sem travar. A interface em Python foi perfeitamente logada ao resto do projeto.
```

## 2026-10-10 22:04
```markdown
- **Backend Completo**: Implementação do backend em FastAPI para gestão de licenças de SaaS, disponível no endereço [http://127.0.0.1:8000](http://127.0.0.1:8000). Inclui endpoints para gerar, validar e revogar licenças.
- **Interface Web Moderna**: Desenvolvimento de uma interface web moderna, intuitiva e responsiva (Dashboard) utilizando HTML5 + CSS (Tailwind CSS) + JavaScript (Fetch API), integrado no próprio FastAPI. A interface oferece funcionalidades para gerir as licenças sem a necessidade do Swagger UI.
- **Módulos Implementados**: Painel Principal, Módulo de Geração de Licenças, Módulo de Validação e Módulo de Revogação foram implementados conforme os requisitos especificados. A interface apresenta cartões com métricas rápidas, formulários para gerar licenças, campos para inserir chaves e botões para realizar as ações correspondentes.
- **Atualizações no `requirements.txt`**: Adição de dependências necessárias para o funcionamento da interface web moderna, como Tailwind CSS e Fetch API.
- **Instruções de Execução**: Inclusão de instruções claras em um novo arquivo README.md sobre como executar a interface lado a lado com a API FastAPI.
```

## 2026-10-10 21:08
```markdown
- **Versão 0.1.0 - 2023-XX-XX**
  - Criação do projeto com estrutura inicial.
  - Implementação de `main.py` como ponto de entrada da aplicação FastAPI.
  - Desenvolvimento dos ficheiros `database.py`, `models.py`, e `schemas.py` para a definição da base de dados, modelos e esquemas de dados.
  - Criação do módulo `crud.py` para operações CRUD básicas.
  - Adição de testes unitários em `tests/test_crud.py`, `tests/test_models.py`, e `tests/test_schemas.py`.
  - Inclusão de utilitários em `utils.py`.
  - Documentação inicial em `README.md`.
```

