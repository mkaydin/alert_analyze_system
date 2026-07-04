import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class ChromaClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        self.client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        for collection in settings.chromadb_collections:
            self.client.get_or_create_collection(collection)
        self._initialized = True

    def get_collection(self, name: str):
        return self.client.get_collection(name)

    def list_collections(self):
        return self.client.list_collections()

    def heartbeat(self):
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False


chroma = ChromaClient()
