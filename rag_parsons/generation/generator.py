from __future__ import annotations

import json
import os

from groq import Groq

from rag_parsons.models.parsons import Language, ParsonsProblem, Topic

_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
_TIMEOUT_SECONDS = 28

_JSON_SCHEMA = """{
  "topic": "<topic id string>",
  "language": "<language id string>",
  "cultural_context": "<narrative paragraph in Portuguese grounded in the provided passages>",
  "programming_concept": "<human-readable concept label in Portuguese>",
  "enunciado": "<full problem statement — see format rules and examples below>",
  "blocks": [
    {"id": 1, "code": "<line of code>", "is_distractor": false},
    ...
  ],
  "correct_order": [1, 2, 3],
  "distractor_blocks": [
    {"id": 10, "code": "<plausible-but-wrong line>", "is_distractor": true},
    {"id": 11, "code": "<another wrong line>", "is_distractor": true}
  ],
  "solution_explanation": "<short explanation in Portuguese of what the code does>",
  "test_cases": [
    {"inputs": ["<input value 1>", "<input value 2>"], "expected_output": "<expected output>"},
    ...
  ],
  "retrieved_passages": []
}"""

_FEW_SHOT_ENUNCIADOS = """EXEMPLOS DE ENUNCIADOS BEM FORMULADOS:

Exemplo 1 (estrutura condicional simples):
Ordene os blocos ao lado para resolver o seguinte problema:

Entre o povo Tikuna, habitantes das margens do rio Solimões, os mais velhos da aldeia recebem o título de Guardiões da Memória, responsáveis por transmitir os saberes ancestrais às novas gerações. Para assumir essa função, o ancião precisa ter atingido uma idade mínima estabelecida pelo conselho da aldeia.
Escreva um programa que verifique se um ancião está apto a se tornar Guardião da Memória.

ENTRADAS:
Dois valores inteiros:
Idade do ancião.
Idade mínima exigida pelo conselho.
SAÍDA:
Exibir "APTO" se a idade do ancião for maior ou igual à idade mínima.
Exibir "NÃO APTO" caso contrário.

---

Exemplo 2 (comparação com três saídas):
Ordene os blocos ao lado para resolver o seguinte problema:

Durante o ritual de escolha do pajé entre os Yanomami, dois candidatos apresentam suas oferendas ao espírito da floresta. A força de cada oferenda é medida por um valor inteiro. Para definir a ordem das cerimônias, é necessário comparar os valores das duas oferendas.
Escreva um programa que:
Leia o valor da Oferenda A.
Leia o valor da Oferenda B.
Compare os dois valores e mostre a mensagem correspondente.

ENTRADAS:
Valor da Oferenda A (inteiro).
Valor da Oferenda B (inteiro).
SAÍDAS:
Se os valores forem iguais, imprima:
As oferendas têm o mesmo poder.
Se o valor de A for menor que o de B, imprima:
A oferenda B tem precedência.
Se o valor de A for maior que o de B, imprima:
A oferenda A tem precedência.

---

Exemplo 3 (comparação de estoque/quantidade):
Ordene os blocos ao lado para resolver o seguinte problema:

A comunidade Guarani controla a quantidade de sementes sagradas armazenadas para o próximo plantio. A liderança da aldeia estabelece uma quantidade mínima recomendada para garantir a colheita. A responsável pelo armazém precisa verificar se o estoque está adequado.
Escreva um programa que:
Leia a quantidade atual de sementes.
Leia a quantidade mínima recomendada.
Compare os dois valores e mostre a mensagem correspondente.

ENTRADAS:
Quantidade atual de sementes (inteiro).
Quantidade mínima recomendada (inteiro).
SAÍDAS:
Se os valores forem iguais, imprima:
Estoque no limite ideal.
Se a quantidade atual for menor que a mínima, imprima:
Atenção! Estoque abaixo do recomendado.
Se a quantidade atual for maior que a mínima, imprima:
Estoque acima do necessário."""


class ParsonsGenerator:
    def __init__(self) -> None:
        if not _GROQ_API_KEY:
            raise RuntimeError(
                "Variável de ambiente GROQ_API_KEY não definida. "
                "Defina-a antes de executar: export GROQ_API_KEY=sua_chave"
            )
        self._client = Groq(api_key=_GROQ_API_KEY)

    def _build_prompt(
        self,
        topic: Topic,
        language: Language,
        context_passages: list[str],
    ) -> tuple[str, str]:
        system_message = (
            "Você é um professor especialista em ensino de programação e em culturas "
            "indígenas brasileiras. Sua missão é criar exercícios de Parsons — "
            "problemas de ordenação de blocos de código — que ensinam conceitos de "
            "programação usando contextos culturais indígenas brasileiros como narrativa.\n\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "1. Retorne SOMENTE JSON válido, sem texto adicional, sem markdown, sem explicações fora do JSON.\n"
            "2. O JSON deve seguir exatamente o schema fornecido.\n"
            "3. O campo 'cultural_context' deve ser um parágrafo em português baseado nos trechos fornecidos.\n"
            "4. O código nos blocos deve estar na linguagem especificada pelo usuário.\n"
            "5. O total de blocos (blocks + distractor_blocks) NÃO pode exceder 20.\n"
            "6. Os blocos de solução devem formar um programa completo e correto quando ordenados por 'correct_order'.\n"
            "7. Os blocos distratores devem ser plausíveis mas errados (lógica incorreta ou sintaxe errada). "
            "O campo 'distractor_blocks' deve conter OBJETOS COMPLETOS com id/code/is_distractor, NUNCA apenas IDs inteiros.\n"
            "8. O campo 'solution_explanation' deve ser em português.\n"
            f"9. O campo 'topic' deve ser '{topic.id}' e o campo 'language' deve ser '{language.id}'.\n"
            "10. O campo 'enunciado' deve seguir EXATAMENTE o formato dos exemplos: começar com "
            "'Ordene os blocos ao lado para resolver o seguinte problema:\\n\\n', seguido de um "
            "parágrafo de contexto cultural indígena brasileiro baseado nos trechos fornecidos, "
            "depois a descrição da tarefa ('Escreva um programa que...'), e por fim as seções "
            "ENTRADAS e SAÍDA(S) detalhando tipos e valores esperados. Todo o enunciado em português.\n"
            "11. O campo 'test_cases' deve conter ao menos 3 casos de teste que cubram: "
            "caso típico, caso limite e caso extremo ou alternativo. "
            "Cada caso deve ter 'inputs' (lista de strings) e 'expected_output' (string).\n\n"
            f"{_FEW_SHOT_ENUNCIADOS}\n\n"
            f"JSON Schema esperado:\n{_JSON_SCHEMA}"
        )

        passages_text = "\n".join(
            f"{i + 1}. {p}" for i, p in enumerate(context_passages)
        ) if context_passages else "Nenhuma passagem disponível."

        user_message = (
            f"Tópico de programação: {topic.label_pt} ({topic.label_en})\n"
            f"Linguagem de programação: {language.label}\n\n"
            f"Trechos da base de conhecimento indígena para usar como contexto cultural:\n"
            f"{passages_text}\n\n"
            "Gere um exercício de Parsons sobre o tópico acima, usando os trechos fornecidos "
            "como base para a narrativa cultural. O exercício deve ser pedagogicamente correto "
            "e culturalmente significativo. Retorne apenas o JSON."
        )

        return system_message, user_message

    def generate(
        self,
        topic: Topic,
        language: Language,
        context_passages: list[str],
    ) -> ParsonsProblem:
        system_msg, user_msg = self._build_prompt(topic, language, context_passages)

        response = self._client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            timeout=_TIMEOUT_SECONDS,
        )

        raw = response.choices[0].message.content or "{}"

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        data["retrieved_passages"] = context_passages

        # Normalize distractor_blocks: LLMs sometimes return IDs (ints) instead of full objects,
        # mirroring the correct_order field. Resolve them from the blocks array when that happens.
        distractors = data.get("distractor_blocks", [])
        if distractors and isinstance(distractors[0], int):
            block_map = {b["id"]: b for b in data.get("blocks", []) if isinstance(b, dict)}
            data["distractor_blocks"] = [
                block_map[bid] for bid in distractors if bid in block_map
            ]

        try:
            problem = ParsonsProblem.model_validate(data)
        except Exception as exc:
            raise ValueError(f"Generated problem failed schema validation: {exc}") from exc

        return problem
