from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

from rag.config import RAGServiceConfig
from rag.session_logger import SessionLogger
from shared.models.retrieved_chunk import RetrievedChunk
from shared.models.session_log import ErrorLog, ToolCallLog

_FIXED_PROMPT = ChatPromptTemplate.from_template(
    "You are a personal knowledge assistant. The context below comes exclusively from the user's own notes "
    "(Obsidian vaults; PDF documents will be added soon).\n\n"
    "Answer the question by reasoning carefully over the provided context. "
    "Synthesize across multiple excerpts if they complement each other. "
    "If the context fully addresses the question, answer directly without caveats. "
    "If the context only partially addresses the question, reason from what is there — only mention gaps if they materially affect the answer.\n\n"
    "If the context contains no relevant signal at all, do not guess. "
    "Instead, briefly describe what the closest retrieved material covers and suggest the user rephrase "
    "or check whether the relevant content has been indexed.\n\n"
    "Do not use your general knowledge to fill gaps — ground your answer only in the context provided.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)

_AGENT_SYSTEM_PROMPT = (
    "You are a personal knowledge assistant with access to the user's indexed notes (Obsidian vaults).\n\n"
    "You have a search_notes tool. Use it as many times as needed — search once to understand the context, "
    "then search again with a more targeted query if the first results suggest a more specific angle.\n\n"
    "Ground your answer only in what you find in the notes. "
    "If after searching you cannot find relevant information, say so clearly."
)

_MAX_AGENT_ITERATIONS = 10


def _build_error_log(exc: Exception) -> ErrorLog:
    """Extracts provider-specific failure detail (e.g. Groq's `failed_generation`) when present."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        detail = body.get("error", {})
        if detail.get("failed_generation") or detail.get("message"):
            return ErrorLog(
                error_type=type(exc).__name__,
                message=detail.get("message", str(exc)),
                raw=detail.get("failed_generation"),
            )
    return ErrorLog(error_type=type(exc).__name__, message=str(exc))


class RAGService:
    def __init__(
        self,
        config: RAGServiceConfig,
        session_logger: SessionLogger,
        agentic: bool = False,
        debug: bool = False,
        name: str | None = None,
    ):
        embeddings = OllamaEmbeddings(
            model=config.embedding_model_id,
            base_url=config.ollama_base_url,
        )
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name=config.qdrant_collection_name,
            url=f"http://{config.qdrant_host}:{config.qdrant_port}",
            content_payload_key="content",
        )
        self._retriever = vectorstore.as_retriever(search_kwargs={"k": config.top_k})
        self.agentic = agentic
        self._debug = debug
        llm = ChatGroq(model=config.groq_model_id, api_key=config.groq_api_key)
        self._chain = _FIXED_PROMPT | llm | StrOutputParser()
        self._llm = llm
        self._session_logger = session_logger
        self._message_number = 0
        self._name = name
        self._session_logger.start_session(name=name)

    def query(self, question: str) -> tuple[str, list[str]]:
        self._message_number += 1
        if self._message_number == 1 and self._name is None:
            self._name = question
            self._session_logger.set_name(self._name)
        mode = "agent" if self.agentic else "query"
        self._session_logger.start_message(self._message_number, mode, question)

        try:
            if self.agentic:
                answer, sources = self._query_agent(question, self._message_number)
            else:
                answer, sources = self._query_fixed(question)
        except Exception as exc:
            error = _build_error_log(exc)
            self._session_logger.log_message_error(self._message_number, error)
            return f"Error: {error.raw or error.message}", []

        self._session_logger.complete_message(self._message_number, answer, sources)
        return answer, sources

    def end_session(self) -> None:
        self._session_logger.end_session()

    def _query_fixed(self, question: str) -> tuple[str, list[str]]:
        docs = self._retriever.invoke(question)
        chunks = [RetrievedChunk.from_document(doc) for doc in docs]
        context = "\n\n".join(chunk.format_for_prompt() for chunk in chunks)
        sources = list({chunk.source_id for chunk in chunks})
        answer = self._chain.invoke({"question": question, "context": context})
        return answer, sources

    def _query_agent(self, question: str, message_number: int) -> tuple[str, list[str]]:
        sources: list[str] = []
        tool_call_count = 0

        @tool
        def search_notes(query: str) -> str:
            """Search the user's personal notes for information relevant to a query. Call multiple times with different queries for multi-hop retrieval."""
            nonlocal tool_call_count
            tool_call_count += 1
            iteration = tool_call_count
            if self._debug:
                print(f'[debug] The AI activated search_notes tool with the query: "{query}"')

            try:
                docs = self._retriever.invoke(query)
            except Exception as exc:
                self._session_logger.log_tool_call(
                    message_number,
                    ToolCallLog(
                        iteration=iteration,
                        tool_name="search_notes",
                        params={"query": query},
                        error=_build_error_log(exc),
                    ),
                )
                raise

            chunks = [RetrievedChunk.from_document(doc) for doc in docs]
            result_sources = [chunk.source_id for chunk in chunks]
            sources.extend(result_sources)
            content = (
                "\n\n".join(chunk.format_for_prompt() for chunk in chunks)
                if chunks
                else "No relevant notes found for this query."
            )
            self._session_logger.log_tool_call(
                message_number,
                ToolCallLog(
                    iteration=iteration,
                    tool_name="search_notes",
                    params={"query": query},
                    result_content=content,
                    result_sources=result_sources,
                ),
            )
            return content

        llm = self._llm.bind_tools([search_notes])
        messages = [SystemMessage(_AGENT_SYSTEM_PROMPT), HumanMessage(question)]

        response = None
        for _ in range(_MAX_AGENT_ITERATIONS):
            response = llm.invoke(messages)
            messages.append(response)
            if not response.tool_calls:
                break
            for tc in response.tool_calls:
                result = search_notes.invoke(tc["args"])
                messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

        answer = response.content if response else ""
        return answer, list(dict.fromkeys(sources))
