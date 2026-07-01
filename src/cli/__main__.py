import click
from pymongo import MongoClient

from rag.config import RAGServiceConfig
from rag.service import RAGService
from rag.session_logger import SessionLogger
from shared.logging_config import configure_logging
from shared.repositories.session_log_repository import SessionLogRepository

configure_logging()


def _build_service(config: RAGServiceConfig, agentic: bool, debug: bool, name: str | None) -> RAGService:
    db = MongoClient(config.mongodb_uri)[config.mongodb_db_name]
    session_logger = SessionLogger(SessionLogRepository(db))
    return RAGService(config, session_logger, agentic=agentic, debug=debug, name=name)


def _repl(service: RAGService) -> None:
    try:
        while True:
            mode = "Agent" if service.agentic else "Query"
            try:
                question = click.prompt(f"[{mode}] You", prompt_suffix="> ")
            except (EOFError, KeyboardInterrupt):
                click.echo("\nGoodbye.")
                break

            question = question.strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit", "q"):
                click.echo("Goodbye.")
                break
            if question == "/agent":
                service.agentic = True
                click.echo("[Agent mode]\n")
                continue
            if question == "/query":
                service.agentic = False
                click.echo("[Query mode]\n")
                continue

            answer, sources = service.query(question)

            click.echo(f"\n{answer}\n")
            if sources:
                click.echo("Sources:")
                for source in sorted(sources):
                    click.echo(f"  {source}")
            click.echo()
    finally:
        service.end_session()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--name", default=None, help="Name for this session. Defaults to the first prompt.")
def query(name: str | None):
    """Fixed-chain RAG: always retrieves top-k, then answers."""
    config = RAGServiceConfig()
    service = _build_service(config, agentic=False, debug=False, name=name)
    click.echo("RAG CLI ready. Ask a question about your notes, or type 'exit' to quit.\n")
    _repl(service)


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Print tool calls as they happen.")
@click.option("--name", default=None, help="Name for this session. Defaults to the first prompt.")
def agent(debug: bool, name: str | None):
    """Agentic RAG: model decides when and what to retrieve, supports multi-hop."""
    config = RAGServiceConfig()
    service = _build_service(config, agentic=True, debug=debug, name=name)
    click.echo("Agent CLI ready. The model will search your notes as needed. Type 'exit' to quit.\n")
    _repl(service)


if __name__ == "__main__":
    cli()
