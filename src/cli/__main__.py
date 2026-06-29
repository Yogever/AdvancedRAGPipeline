import click

from rag.config import RAGServiceConfig
from rag.service import RAGService


def _repl(service: RAGService) -> None:
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


@click.group()
def cli():
    pass


@cli.command()
def query():
    """Fixed-chain RAG: always retrieves top-k, then answers."""
    config = RAGServiceConfig()
    service = RAGService(config)
    click.echo("RAG CLI ready. Ask a question about your notes, or type 'exit' to quit.\n")
    _repl(service)


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Print tool calls as they happen.")
def agent(debug: bool):
    """Agentic RAG: model decides when and what to retrieve, supports multi-hop."""
    config = RAGServiceConfig()
    service = RAGService(config, agentic=True, debug=debug)
    click.echo("Agent CLI ready. The model will search your notes as needed. Type 'exit' to quit.\n")
    _repl(service)


if __name__ == "__main__":
    cli()
