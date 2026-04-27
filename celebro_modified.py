#!/usr/bin/env /home/jcorcuera/cerebro_env/bin/python
"""
CEREBRO - Sistema de memoria persistente propio.
Embeddings via Ollama (nomic-embed-text) + Qdrant local + SQLite.
Versión mejorada con metadatos (source, tags).
"""
import os
import sys
import json
import sqlite3
import requests
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DB_PATH = "/home/jcorcuera/cerebro_data"
COLLECTION = "memorias"
DIM = 768

class Cerebro:
    def __init__(self):
        os.makedirs(DB_PATH, exist_ok=True)
        self.qdrant = QdrantClient(path=f"{DB_PATH}/vectores")
        self._ensure_collection()
        self.sql = sqlite3.connect(f"{DB_PATH}/textos.db")
        self._ensure_sql_table()

    def _ensure_collection(self):
        collections = [c.name for c in self.qdrant.get_collections().collections]
        if COLLECTION not in collections:
            self.qdrant.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=DIM, distance=Distance.COSINE)
            )
            print(f"[✅] Colección '{COLLECTION}' creada")

    def _ensure_sql_table(self):
        self.sql.execute("""
            CREATE TABLE IF NOT EXISTS textos (
                id TEXT PRIMARY KEY,
                texto TEXT NOT NULL,
                categoria TEXT,
                source TEXT,
                tags TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.sql.commit()

    def _embed(self, texto: str) -> list:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text:latest", "prompt": texto},
            timeout=60
        )
        r.raise_for_status()
        return r.json()["embedding"]

    def _id(self, texto: str) -> str:
        return str(uuid.uuid4())

    def guardar(self, texto: str, categoria: str = "general", source: str = None, tags: list = None) -> str:
        mid = self._id(texto)
        vector = self._embed(texto)
        tag_str = json.dumps(tags) if tags else None

        # Qdrant (Base Vectorial)
        self.qdrant.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=mid, 
                vector=vector, 
                payload={"cat": categoria, "source": source, "tags": tag_str}
            )]
        )

        # SQLite (Base Relacional para búsqueda y metadatos)
        try:
            self.sql.execute(
                "INSERT OR REPLACE INTO textos (id, texto, categoria, source, tags) VALUES (?, ?, ?, ?, ?)",
                (mid, texto, categoria, source, tag_str)
            )
            self.sql.commit()
        except Exception as e:
            print(f"[⚠️] SQLite warning: {e}")

        return mid

    def buscar(self, query: str, top_k: int = 5, source: str = None, tags: list = None) -> list:
        vector = self._embed(query)
        
        # Por ahora la búsqueda en Qdrant es solo semántica. 
        # Los filtros (source, tags) se podrían implementar aquí con un objeto Filter.
        filters = None
        if source or tags:
            must_conditions = []
            if source:
                must_conditions.append(FieldCondition(key="source", match=MatchValue(value=source)))
            if tags:
                must_conditions.append(FieldCondition(key="tags", match=MatchAny(any=tags)))
            
            if must_conditions:
                filters = Filter(must=must_conditions)
        
        results = self.qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k,
            query_filter=filters
        ).points
        results = self.qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k
        ).points

        out = []
        for r in results:
            cursor = self.sql.execute("SELECT texto, source, tags FROM textos WHERE id = ?", (r.id,))
            row = cursor.fetchone()
            if row:
                texto, source_val, tags_val = row
                tags_list = json.loads(tags_val) if tags_val else []
                out.append({
                    "id": r.id,
                    "score": round(r.score, 4),
                    "texto": texto,
                    "categoria": r.payload.get("cat", "general"),
                    "source": source_val,
                    "tags": tags_list
                })
        return out

    def contar(self) -> int:
        return self.qdrant.count(collection_name=COLLECTION).count


def main():
    cerebro = Cerebro()

    if len(sys.argv) < 2:
        print("Uso: cerebro.py <comando> [args]")
        print("")
        print("COMANDOS:")
        print("  guardar '<texto>' [categoria] [source] [tags_json]  - Guarda una memoria")
        print("  buscar '<query>' [top_k] [source] [tags_json]       - Busca memorias")
        print("  contar                                              - Cuenta memorias")
        print("")
        print("EJEMPLOS:")
        print('  ./cerebro.py guardar "Memoria de prueba con metadatos" "test" "terminal" \'["final", "v2"]\'')
        print('  ./cerebro.py buscar "Prueba final de Cerebro" 2')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "guardar":
        if len(sys.argv) < 3:
            print("❌ Falta texto. Uso: guardar '<texto>' [categoria] [source] [tags_json]")
            sys.exit(1)
        texto = sys.argv[2]
        cat = sys.argv[3] if len(sys.argv) > 3 else "general"
        source = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = json.loads(tags_str) if tags_str else None
        
        mid = cerebro.guardar(texto, cat, source=source, tags=tags)
        print(f"✅ Guardado [id={mid}] cat={cat}, source={source}, tags={tags}")
        print(f"   {texto[:80]}...")

    elif cmd == "buscar":
        if len(sys.argv) < 3:
            print("❌ Falta query. Uso: buscar '<query>' [top_k] [source] [tags_json]")
            sys.exit(1)
        query = sys.argv[2]
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        source = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = json.loads(tags_str) if tags_str else None

        print(f"🔍 Buscando: '{query}' (top {top_k}, source={source}, tags={tags})\n")
        results = cerebro.buscar(query, top_k, source=source, tags=tags)
        if not results:
            print("❌ No se encontraron memorias.")
            sys.exit(0)
        for i, r in enumerate(results, 1):
            tag_display = ", ".join(r['tags']) if r.get('tags') else 'Ninguno'
            source_display = r.get('source', 'N/A')
            print(f"{i}. [⭐ {r['score']}] [{r['categoria']}] (Src: {source_display}, Tags: {tag_display}) {r['texto'][:120]}...")

    elif cmd == "contar":
        n = cerebro.contar()
        print(f"📊 Total memorias: {n}")

    else:
        print(f"❌ Comando desconocido: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
