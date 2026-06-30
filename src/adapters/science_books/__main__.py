from adapters.science_books.adapter import ScienceBookAdapter
from adapters.science_books.config import ScienceBookConfig
from shared.logging_config import configure_logging

configure_logging()

config = ScienceBookConfig()

adapter = ScienceBookAdapter(
    books_path=config.books_path,
    output_path=config.output_path,
)

adapter.start()
