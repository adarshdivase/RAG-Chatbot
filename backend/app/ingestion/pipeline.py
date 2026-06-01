"""Document loading, chunking, and vector store management."""

import logging
import os
import shutil
import time
from pathlib import Path

from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings

logger = logging.getLogger(__name__)

try:
    from langchain_community.document_loaders import UnstructuredWordDocumentLoader as DocxLoader
except ImportError:
    DocxLoader = None

LOADER_MAP = {
    ".txt": TextLoader,
    ".md": TextLoader,
    ".pdf": PyPDFLoader,
    ".csv": CSVLoader,
}


class IngestionPipeline:
    def __init__(self, settings: Settings, embeddings: GoogleGenerativeAIEmbeddings):
        self.settings = settings
        self.embeddings = embeddings
        self._vectorstore: Chroma | None = None
        self._chunk_count = 0
        self._document_count = 0

    @property
    def vectorstore(self) -> Chroma | None:
        return self._vectorstore

    @property
    def chunk_count(self) -> int:
        return self._chunk_count

    @property
    def document_count(self) -> int:
        return self._document_count

    def load_documents_from_disk(self) -> list[Document]:
        data_dir = self.settings.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        documents: list[Document] = []

        for path in sorted(data_dir.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext not in self.settings.allowed_ext_set:
                continue
            loader_cls = LOADER_MAP.get(ext)
            if ext == ".docx" and DocxLoader:
                loader_cls = DocxLoader
            if not loader_cls:
                logger.warning("No loader for %s", path.name)
                continue
            try:
                loader = loader_cls(str(path))
                docs = loader.load()
                for doc in docs:
                    doc.metadata.setdefault("source", str(path))
                    doc.metadata["filename"] = path.name
                documents.extend(docs)
                logger.info("Loaded %s (%d parts)", path.name, len(docs))
            except Exception as exc:
                logger.warning("Failed to load %s: %s", path.name, exc)

        self._document_count = len({d.metadata.get("filename", d.metadata.get("source")) for d in documents})
        return documents

    def split_documents(self, documents: list[Document]) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        splits = splitter.split_documents(documents)
        self._chunk_count = len(splits)
        return splits

    def build_or_load_vectorstore(self, force_rebuild: bool = False) -> Chroma:
        chroma_dir = self.settings.chroma_dir
        chroma_dir.mkdir(parents=True, exist_ok=True)

        if not force_rebuild and any(chroma_dir.iterdir()):
            logger.info("Loading existing vector store from %s", chroma_dir)
            self._vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=self.embeddings,
            )
            try:
                self._chunk_count = self._vectorstore._collection.count()
            except Exception:
                self._chunk_count = 0
            return self._vectorstore

        documents = self.load_documents_from_disk()
        if not documents:
            documents = [
                Document(
                    page_content=(
                        "Enterprise RAG knowledge base is empty. Upload documents via the API "
                        "or place files in the data directory, then trigger reindex."
                    ),
                    metadata={"source": "system", "filename": "placeholder.txt"},
                )
            ]
            self._document_count = 0

        splits = self.split_documents(documents)
        if force_rebuild and chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            chroma_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Indexing %d chunks from %d documents", len(splits), self._document_count)
        self._vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=str(chroma_dir),
        )
        return self._vectorstore

    def reindex(self) -> tuple[int, int, float]:
        start = time.perf_counter()
        self.build_or_load_vectorstore(force_rebuild=True)
        duration_ms = (time.perf_counter() - start) * 1000
        return self._document_count, self._chunk_count, duration_ms

    def list_documents(self) -> list[dict]:
        data_dir = self.settings.data_dir
        if not data_dir.exists():
            return []
        items = []
        for path in sorted(data_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in self.settings.allowed_ext_set:
                stat = path.stat()
                items.append(
                    {
                        "filename": path.name,
                        "size_bytes": stat.st_size,
                        "extension": path.suffix.lower(),
                        "modified_at": stat.st_mtime,
                    }
                )
        return items

    def delete_document(self, filename: str) -> bool:
        safe_name = os.path.basename(filename)
        path = self.settings.data_dir / safe_name
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
