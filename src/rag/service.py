from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

from rag.config import RAGServiceConfig
from shared.models.retrieved_chunk import RetrievedChunk

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


class RAGService:
    def __init__(self, config: RAGServiceConfig, agentic: bool = False, debug: bool = False):
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

    def query(self, question: str) -> tuple[str, list[str]]:
        if self.agentic:
            return self._query_agent(question)
        return self._query_fixed(question)

    def _query_fixed(self, question: str) -> tuple[str, list[str]]:
        docs = self._retriever.invoke(question)
        chunks = [RetrievedChunk.from_document(doc) for doc in docs]
        context = "\n\n".join(chunk.format_for_prompt() for chunk in chunks)
        sources = list({chunk.source_id for chunk in chunks})
        answer = self._chain.invoke({"question": question, "context": context})
        return answer, sources

    def _query_agent(self, question: str) -> tuple[str, list[str]]:
        sources: list[str] = []

        @tool
        def search_notes(query: str) -> str:
            """Search the user's personal notes for information relevant to a query. Call multiple times with different queries for multi-hop retrieval."""
            if self._debug:
                print(f'[debug] The AI activated search_notes tool with the query: "{query}"')
            docs = self._retriever.invoke(query)
            chunks = [RetrievedChunk.from_document(doc) for doc in docs]
            sources.extend(chunk.source_id for chunk in chunks)
            if not chunks:
                return "No relevant notes found for this query."
            return "\n\n".join(chunk.format_for_prompt() for chunk in chunks)

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
