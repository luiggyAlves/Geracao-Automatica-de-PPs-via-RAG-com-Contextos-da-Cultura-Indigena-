from __future__ import annotations

import sys
from typing import Optional

import typer

from rag_parsons.generation.generator import ParsonsGenerator
from rag_parsons.generation.retriever import Retriever
from rag_parsons.kb.ingestion import ingest_all, load_pdfs
from rag_parsons.kb.vectorstore import VectorStore
from rag_parsons.models.parsons import (
    LANGUAGE_IDS,
    LANGUAGES,
    TOPIC_IDS,
    TOPICS,
    get_language,
    get_topic,
)

app = typer.Typer(
    name="rag-parsons",
    help="Gerador de exercícios de Parsons com contexto cultural indígena brasileiro.",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo("rag-parsons 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


@app.command("build-kb")
def build_kb(
    livros_dir: str = typer.Option("./Livros", help="Diretório com os PDFs."),
    db_path: str = typer.Option("./chroma_db", help="Caminho do banco ChromaDB."),
    force: bool = typer.Option(False, "--force", help="Limpa e reconstrói a base."),
) -> None:
    """Indexa os PDFs do diretório Livros/ na base de conhecimento vetorial."""
    try:
        load_pdfs(livros_dir)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    store = VectorStore(db_path=db_path)
    store.init_collection()

    if force or store.count() == 0:
        if force:
            typer.echo("Limpando base existente...")
            store.clear()
    else:
        typer.echo(
            f"Base já contém {store.count()} chunks. Use --force para reconstruir."
        )
        raise typer.Exit(0)

    try:
        pdfs = load_pdfs(livros_dir)
        typer.echo(f"Indexando {len(pdfs)} PDF(s) de {livros_dir}...")
        total = ingest_all(livros_dir, store)
        typer.echo(f"Base de conhecimento construída: {total} chunks no total.")
    except Exception as exc:
        typer.echo(f"Error: falha ao escrever no ChromaDB: {exc}", err=True)
        raise typer.Exit(2)


@app.command("topics")
def topics(
    as_json: bool = typer.Option(False, "--json", help="Saída em formato JSON."),
) -> None:
    """Lista os tópicos disponíveis para geração de exercícios."""
    if as_json:
        import json

        data = [
            {"id": t.id, "label_pt": t.label_pt, "label_en": t.label_en}
            for t in TOPICS
        ]
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        typer.echo("Tópicos disponíveis:\n")
        for t in TOPICS:
            typer.echo(f"  {t.id:<22} {t.label_pt}")


@app.command("languages")
def languages(
    as_json: bool = typer.Option(False, "--json", help="Saída em formato JSON."),
) -> None:
    """Lista as linguagens de programação disponíveis para os exercícios."""
    if as_json:
        import json

        data = [{"id": l.id, "label": l.label} for l in LANGUAGES]
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        typer.echo("Linguagens disponíveis:\n")
        for l in LANGUAGES:
            typer.echo(f"  {l.id:<15} {l.label}")


@app.command("generate")
def generate(
    topic_id: str = typer.Option(..., "--topic", help="ID do tópico (ver: rag-parsons topics)."),
    language_id: str = typer.Option(..., "--language", help="ID da linguagem (ver: rag-parsons languages)."),
    db_path: str = typer.Option("./chroma_db", help="Caminho do banco ChromaDB."),
    show_sources: bool = typer.Option(
        False,
        "--show-sources",
        help="Inclui os trechos recuperados da base no JSON de saída.",
    ),
) -> None:
    """Gera um exercício de Parsons com contexto cultural indígena.

    Execute múltiplas vezes para o mesmo tópico para obter contextos culturais diferentes.
    """
    topic = get_topic(topic_id)
    if topic is None:
        typer.echo(
            f"Error: tópico desconhecido '{topic_id}'. Execute 'rag-parsons topics' para ver as opções.",
            err=True,
        )
        raise typer.Exit(1)

    language = get_language(language_id)
    if language is None:
        typer.echo(
            f"Error: linguagem desconhecida '{language_id}'. Execute 'rag-parsons languages' para ver as opções.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        store = VectorStore(db_path=db_path)
        store.init_collection()
        if store.count() == 0:
            typer.echo(
                "Error: base de conhecimento vazia. Execute 'rag-parsons build-kb' primeiro.",
                err=True,
            )
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Error: não foi possível acessar o ChromaDB: {exc}", err=True)
        raise typer.Exit(2)

    retriever = Retriever(store)
    context_passages = retriever.get_context(n=3)

    generator = ParsonsGenerator()

    try:
        problem = generator.generate(topic, language, context_passages)
    except TimeoutError:
        typer.echo(
            "Error: tempo limite de geração excedido (30s). Tente novamente.",
            err=True,
        )
        raise typer.Exit(3)
    except Exception as exc:
        if "validation" in str(exc).lower() or "schema" in str(exc).lower():
            typer.echo(f"Error: exercício gerado inválido: {exc}", err=True)
            raise typer.Exit(4)
        typer.echo(f"Error: falha na API Groq: {exc}", err=True)
        raise typer.Exit(3)

    if not show_sources:
        problem.retrieved_passages = []

    typer.echo(problem.model_dump_json(indent=2))


@app.command("info")
def info(
    db_path: str = typer.Option("./chroma_db", help="Caminho do banco ChromaDB."),
) -> None:
    """Exibe informações sobre a base de conhecimento atual."""
    try:
        store = VectorStore(db_path=db_path)
        store.init_collection()
        count = store.count()
        if count == 0:
            typer.echo(
                "Error: base de conhecimento vazia ou não encontrada. Execute 'rag-parsons build-kb' primeiro.",
                err=True,
            )
            raise typer.Exit(2)
        sources = store.get_sources()
        typer.echo(f"Total de chunks: {count}")
        typer.echo(f"Fontes ({len(sources)} PDF(s)):")
        for s in sources:
            typer.echo(f"  - {s}")
        typer.echo("\nAmostra de 3 trechos aleatórios:")
        samples = store.random_sample(3)
        for i, s in enumerate(samples, 1):
            preview = s[:200].replace("\n", " ")
            typer.echo(f"\n  [{i}] {preview}...")
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(2)
