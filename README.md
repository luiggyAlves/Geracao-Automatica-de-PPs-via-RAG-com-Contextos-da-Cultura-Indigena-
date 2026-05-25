# Geracão Automática de Problemas de Parsons via RAG para o Ensino Inclusivo de Programacão com Contextos da Cultura Indígena

Gerador de exercícios de Parsons com contexto cultural indígena brasileiro.

Usa RAG (Retrieval-Augmented Generation) para criar problemas de ordenação de código cujo contexto narrativo é extraído de livros sobre culturas indígenas brasileiras.

## Pré-requisitos

- Python 3.11+

## Instalação

```bash
git clone https://github.com/luiggyAlves/Geracao-Automatica-de-PPs-via-RAG-com-Contextos-da-Cultura-Indigena-.git
cd Geracao-Automatica-de-PPs-via-RAG-com-Contextos-da-Cultura-Indigena-
```

> **Atenção:** o ambiente virtual não é incluído no repositório. Crie-o manualmente após clonar:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux/macOS:
source .venv/bin/activate

# Windows — PowerShell:
.\.venv\Scripts\activate

# Windows — Prompt de Comando (cmd.exe):
.venv\Scripts\activate.bat
```

Instale as dependências:

```bash
pip install -e .
```

## Configuração

Obtenha uma chave gratuita em [console.groq.com](https://console.groq.com) e defina a variável de ambiente:

```bash
# Linux/macOS
export GROQ_API_KEY=sua_chave_aqui

# Windows — PowerShell
$env:GROQ_API_KEY = "sua_chave_aqui"

# Windows — Prompt de Comando (cmd.exe)
set GROQ_API_KEY=sua_chave_aqui
```

Ou copie `.env.example` para `.env` e preencha o valor (use `python-dotenv` ou carregue manualmente antes de executar).

## Uso

### 1. Construir a base de conhecimento

> Os livros já estão incluídos na pasta `Livros/` do repositório. Não é necessário adicionar PDFs manualmente.

```bash
rag-parsons build-kb
```

Use `--force` para reconstruir após adicionar novos livros.

### 3. Listar tópicos disponíveis

```bash
rag-parsons topics
```

### 4. Listar linguagens disponíveis

```bash
rag-parsons languages
```

### 5. Gerar um exercício

```bash
rag-parsons generate --topic variaveis --language python
```

Salvar em arquivo:

```bash
rag-parsons generate --topic laco_for --language java > exercicio.json
```

Ver os trechos da base usados na geração:

```bash
rag-parsons generate --topic funcoes --language python --show-sources
```

Execute múltiplas vezes para obter contextos culturais diferentes.

### 6. Inspecionar a base de conhecimento

```bash
rag-parsons info
```

## Tópicos disponíveis

| ID | Tópico |
|----|--------|
| `variaveis` | Variáveis |
| `tipos_dados` | Tipos de dados básicos |
| `op_atribuicao` | Operadores de atribuição |
| `op_aritmeticos` | Operadores aritméticos |
| `op_logicos` | Operadores lógicos |
| `op_comparacao` | Operadores de comparação |
| `expressoes_logicas` | Expressões lógicas |
| `entrada_saida` | Operações de entrada e saída |
| `fluxo_controle` | Fluxo de controle |
| `cond_simples` | Estruturas condicionais simples |
| `cond_compostas` | Estruturas condicionais compostas |
| `cond_aninhadas` | Estruturas condicionais aninhadas |
| `cond_encadeadas` | Estruturas condicionais encadeadas |
| `lacos` | Laços de repetição |
| `laco_for` | Laço for |
| `laco_while` | Laço while |
| `vetores` | Vetores |
| `strings` | Strings |
## Formato de saída (JSON)

```json
{
  "topic": "variaveis",
  "language": "python",
  "cultural_context": "Entre o povo Yanomami...",
  "programming_concept": "Variáveis",
  "blocks": [
    {"id": 1, "code": "nome_aldeia = 'Yanomami'", "is_distractor": false}
  ],
  "correct_order": [1, 2, 3],
  "distractor_blocks": [
    {"id": 10, "code": "nome_aldeia == 'Yanomami'", "is_distractor": true}
  ],
  "solution_explanation": "...",
  "retrieved_passages": []
}
```

Total de blocos (solução + distratores): máximo 20.

## Solução de problemas

| Erro | Causa | Solução |
|------|-------|---------|
| `base de conhecimento vazia` | `build-kb` não executado | Executar `rag-parsons build-kb` |
| `Directory not found: ./Livros` | Comando executado fora da raiz do projeto | Executar a partir de `rag-parsons/` ou usar `--livros-dir <caminho absoluto>` |
| Timeout na geração | Limite da API Groq | Aguardar e tentar novamente |
| Nenhum PDF encontrado | Pasta `Livros/` vazia | Adicionar PDFs à pasta `Livros/` |
| `distractor_blocks` com inteiros | LLM retorna IDs em vez de objetos completos | Tratado automaticamente pelo normalizador interno |
