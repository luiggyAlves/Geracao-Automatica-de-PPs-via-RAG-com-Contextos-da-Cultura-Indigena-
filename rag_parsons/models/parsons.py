from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, field_validator, model_validator


@dataclass
class Topic:
    id: str
    label_pt: str
    label_en: str


@dataclass
class Language:
    id: str
    label: str


TOPICS: list[Topic] = [
    Topic("variaveis", "Variáveis", "Variables"),
    Topic("constantes", "Constantes", "Constants"),
    Topic("tipos_dados", "Tipos de dados básicos", "Basic data types"),
    Topic("op_atribuicao", "Operadores de atribuição", "Assignment operators"),
    Topic("op_aritmeticos", "Operadores aritméticos", "Arithmetic operators"),
    Topic("op_logicos", "Operadores lógicos", "Logical operators"),
    Topic("op_comparacao", "Operadores de comparação", "Comparison operators"),
    Topic("expressoes_logicas", "Expressões lógicas", "Logical expressions"),
    Topic("entrada_saida", "Operações de entrada e saída", "I/O operations"),
    Topic("fluxo_controle", "Fluxo de controle", "Control flow"),
    Topic("cond_simples", "Estruturas condicionais simples", "Simple conditionals"),
    Topic("cond_compostas", "Estruturas condicionais compostas", "Compound conditionals"),
    Topic("cond_aninhadas", "Estruturas condicionais aninhadas", "Nested conditionals"),
    Topic("cond_encadeadas", "Estruturas condicionais encadeadas", "Chained conditionals"),
    Topic("switch_case", "Estruturas switch/case", "Switch/case"),
    Topic("lacos", "Laços de repetição", "Repetition loops"),
    Topic("laco_for", "Laço for", "For loop"),
    Topic("laco_while", "Laço while", "While loop"),
    Topic("vetores", "Vetores", "Vectors/Arrays"),
    Topic("strings", "Strings", "Strings"),
    Topic("boas_praticas", "Boas práticas de programação", "Good programming practices"),
    Topic("funcoes", "Funções", "Functions"),
    Topic("procedimentos", "Procedimentos", "Procedures"),
    Topic("param_funcoes", "Parâmetros de funções", "Function parameters"),
    Topic("escopo_variaveis", "Escopo de variáveis", "Variable scope"),
]

LANGUAGES: list[Language] = [
    Language("python", "Python"),
    Language("java", "Java"),
    Language("c", "C"),
    Language("cpp", "C++"),
    Language("javascript", "JavaScript"),
]

TOPIC_IDS: set[str] = {t.id for t in TOPICS}
LANGUAGE_IDS: set[str] = {l.id for l in LANGUAGES}


def get_topic(topic_id: str) -> Topic | None:
    return next((t for t in TOPICS if t.id == topic_id), None)


def get_language(language_id: str) -> Language | None:
    return next((l for l in LANGUAGES if l.id == language_id), None)


class ParsonsBlock(BaseModel):
    id: int
    code: str
    is_distractor: bool = False


class TestCase(BaseModel):
    inputs: list[str]
    expected_output: str


class ParsonsProblem(BaseModel):
    topic: str
    language: str
    cultural_context: str
    programming_concept: str
    enunciado: str
    blocks: list[ParsonsBlock]
    correct_order: list[int]
    distractor_blocks: list[ParsonsBlock]
    solution_explanation: str
    test_cases: list[TestCase] = []
    retrieved_passages: list[str] = []

    @field_validator("cultural_context")
    @classmethod
    def context_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cultural_context must not be empty")
        return v

    @model_validator(mode="after")
    def total_blocks_limit(self) -> "ParsonsProblem":
        total = len(self.blocks) + len(self.distractor_blocks)
        if total > 20:
            raise ValueError(
                f"Total blocks (solution + distractors) must not exceed 20, got {total}"
            )
        return self
