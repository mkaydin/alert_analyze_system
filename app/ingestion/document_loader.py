import os
import uuid

from app.config import settings
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client


class DocumentChunk:
    def __init__(
        self,
        text: str,
        metadata: dict,
        chunk_id: str | None = None,
    ):
        self.id = chunk_id or str(uuid.uuid4())
        self.text = text
        self.metadata = metadata
        self.collection = "documents"


def parse_markdown_file(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    source = _detect_source(filepath)
    title = _extract_title(content) or filename.replace(".md", "")

    sections = _chunk_by_headings(content)
    result = []
    for heading, body in sections:
        full_text = f"{heading}\n{body}" if heading else body
        result.append(
            {
                "title": title,
                "source": source,
                "heading": heading.strip("# ") if heading else title,
                "text": full_text.strip(),
            }
        )
    return result


def _detect_source(filepath: str) -> str:
    parts = filepath.replace("\\", "/").split("/")
    for p in parts:
        if p == "mitre_attack":
            return "mitre-attack"
        if p == "lolbins":
            return "lolbins"
        if p == "playbooks":
            return "playbook"
    return "custom"


def _extract_title(content: str) -> str | None:
    for line in content.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            return line.strip("# ")
    return None


def _chunk_by_headings(content: str) -> list[tuple[str, str]]:
    lines = content.split("\n")
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []

    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if current_heading or current_body:
                sections.append((current_heading, "\n".join(current_body).strip()))
            current_heading = line
            current_body = []
        elif line.startswith("# "):
            continue
        else:
            current_body.append(line)

    if current_heading or current_body:
        sections.append((current_heading, "\n".join(current_body).strip()))

    return sections


async def ingest_document_file(filepath: str) -> dict:
    sections = parse_markdown_file(filepath)
    if not sections:
        return {"file": filepath, "chunks_created": 0, "error": "No sections found"}

    col = chroma.get_collection("documents")

    filename = os.path.basename(filepath)
    chunks_created = 0

    batch_size = settings.ollama_concurrency * 2
    for i in range(0, len(sections), batch_size):
        batch = sections[i : i + batch_size]
        texts = [s["text"] for s in batch]
        embeddings = await embed_client.embed(texts)

        ids = []
        metadatas = []
        documents = []
        for j, sec in enumerate(batch):
            cid = str(uuid.uuid4())
            ids.append(cid)
            metadatas.append(
                {
                    "doc_id": cid,
                    "title": sec["title"],
                    "source": sec["source"],
                    "heading": sec["heading"],
                    "filename": filename,
                    "type": "reference",
                }
            )
            documents.append(sec["text"])
            chunks_created += 1

        col.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    return {
        "file": filename,
        "source": _detect_source(filepath),
        "chunks_created": chunks_created,
    }


async def ingest_directory(dirpath: str) -> list[dict]:
    results = []
    for root, _dirs, files in os.walk(dirpath):
        for f in sorted(files):
            if f.endswith(".md") and not f.startswith("."):
                path = os.path.join(root, f)
                result = await ingest_document_file(path)
                results.append(result)
    return results


async def load_all_reference_documents() -> list[dict]:
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "documents"
    )
    results = []
    for subdir in sorted(os.listdir(base_dir)):
        dirpath = os.path.join(base_dir, subdir)
        if os.path.isdir(dirpath):
            res = await ingest_directory(dirpath)
            results.extend(res)
    return results
