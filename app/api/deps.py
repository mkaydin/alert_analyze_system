from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client


def get_chroma():
    return chroma


def get_embed_client():
    return embed_client


def get_llm_client():
    return llm_client
