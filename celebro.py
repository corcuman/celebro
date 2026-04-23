#!/usr/bin/env python3
"""
 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 ▓                                                                              ▓
 ▓   ▐█████░  ▐█████░ ▐██░     ▐██████░ ▐███████░ ▐██████░  ▐█████░  ▓
 ▓  ▐█░      ▐█░     ▐█░     ▐█░▀▀▀▀░ ▐█░▀▀▀▀░ ▐█░▀▀▀▀░ ▐█░   █░  ▓
 ▓  ▐█░      ▐█████░ ▐█░     ▐█████░  ▐█████░  ▐█████░ ▐███████░  ▓
 ▓  ▐█░      ▐█░     ▐█░     ▐█░▀▀▀▀░ ▐█░▀▀▀░  ▐█░▀▀░  ▐█░   █░  ▓
 ▓   ▐█████░ ▐██████░▐██████░ ▐██████░ ▐█░     ▐█░  ▐█░ ▐█░   █░  ▓
 ▓                                                                              ▓
 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

CELEBRO - Memoria persistente, privada y ultrarrápida para agentes IA.

Un cerebro que CELEBRA tener memoria 🎉

Embeddings vía Ollama + Qdrant local + SQLite.
Sin generación LLM = 2-5 segundos por operación, no minutos.

Repo: https://github.com/jcorcuera/celebro
Autor: @jcorcuera + NeoIA
"""

import os
import sys
import json
import sqlite3
import uuid
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# --- Configuración ---
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DB_PATH = os.environ.get("CELEBRO_PATH", os.path.expanduser("~/.celebro"))
COLLECTION = "memorias"
EMBEDDING_DIMS = 768
DEFAULT_MODEL = "nomic-embed-text:latest"


class Celebro:
    """CELEBRO: memoria vectorial local con Ollama + Qdrant + SQLite."""

    def __init__(self, ollama_url: str = None, db_path: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.db_path = db_path or DB_PATH
        os.makedirs(self.db_path, exist_ok=True)

        self.qdrant = QdrantClient(path=f"{self.db_path}/vectores")
        self._ensure_collection()

        self.sql = sqlite3.connect(f"{self.db_path}/textos.db")
        self._ensure_sql_table()

    def _ensure_collection(self):
        collections = [c.name for c in self.qdrant.get_collections().collections]
        if COLLECTION not in collections:
            self.qdrant.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIMS, distance=Distance.COSINE)
            )

    def _ensure_sql_table(self):
        self.sql.execute("""
            CREATE TABLE IF NOT EXISTS textos (
                id TEXT PRIMARY KEY,
                texto TEXT NOT NULL,
                categoria TEXT DEFAULT 'general',
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.sql.commit()

    def embed(self, texto: str, model: str = None) -> list:
        """Genera embedding vía Ollama."""
        r = requests.post(
            f"{self.ollama_url}/api/embeddings",
            json={"model": model or DEFAULT_MODEL, "prompt": texto},
            timeout=60
        )
        r.raise_for_status()
        return r.json()["embedding"]

    def guardar(self, texto: str, categoria: str = "general", model: str = None) -> str:
        """Guarda una memoria. Retorna el ID generado."""
        mid = str(uuid.uuid4())
        vector = self.embed(texto, model)

        # Qdrant
        self.qdrant.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(id=mid, vector=vector, payload={"cat": categoria})]
        )

        # SQLite
        self.sql.execute(
            "INSERT INTO textos (id, texto, categoria) VALUES (?, ?, ?)",
            (mid, texto, categoria)
        )
        self.sql.commit()
        return mid

    def buscar(self, query: str, top_k: int = 5, model: str = None) -> list:
        """Búsqueda semántica. Retorna lista de dicts."""
        vector = self.embed(query, model)
        results = self.qdrant.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k
        ).points

        out = []
        for r in results:
            cursor = self.sql.execute(
                "SELECT texto, categoria FROM textos WHERE id = ?", (r.id,)
            )
            row = cursor.fetchone()
            if row:
                out.append({
                    "id": r.id,
                    "score": round(r.score, 4),
                    "texto": row[0],
                    "categoria": row[1]
                })
        return out

    def borrar(self, mem_id: str) -> bool:
        """Borra una memoria por ID."""
        self.qdrant.delete(collection_name=COLLECTION, points_selector=[mem_id])
        self.sql.execute("DELETE FROM textos WHERE id = ?", (mem_id,))
        self.sql.commit()
        return True

    def contar(self) -> int:
        """Cuenta memorias totales."""
        return self.qdrant.count(collection_name=COLLECTION).count

    def listar(self, categoria: str = None, limite: int = 100) -> list:
        """Lista memorias (opcionalmente filtradas por categoría)."""
        if categoria:
            cursor = self.sql.execute(
                "SELECT id, texto, categoria, fecha FROM textos WHERE categoria = ? LIMIT ?",
                (categoria, limite)
            )
        else:
            cursor = self.sql.execute(
                "SELECT id, texto, categoria, fecha FROM textos LIMIT ?", (limite,)
            )
        return [
            {"id": row[0], "texto": row[1], "categoria": row[2], "fecha": row[3]}
            for row in cursor.fetchall()
        ]


def print_banner():
    print(r"""
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  ▓                                                                        ▓
  ▓   ▐█████░  ▐█████░ ▐██░     ▐██████░ ▐███████░ ▐██████░  ▐█████░  ▓
  ▓  ▐█░      ▐█░     ▐█░     ▐█░▀▀▀▀░ ▐█░▀▀▀▀░ ▐█░▀▀▀▀░ ▐█░   █░  ▓
  ▓  ▐█░      ▐█████░ ▐█░     ▐█████░  ▐█████░  ▐█████░ ▐███████░  ▓
  ▓  ▐█░      ▐█░     ▐█░     ▐█░▀▀▀▀░ ▐█░▀▀▀░  ▐█░▀▀░  ▐█░   █░  ▓
  ▓   ▐█████░ ▐██████░▐██████░ ▐██████░ ▐█░     ▐█░  ▐█░ ▐█░   █░  ▓
  ▓                                                                        ▓
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
    """)


def main():
    celebro = Celebro()

    if len(sys.argv) < 2:
        print_banner()
        print("Uso: celebro.py <comando> [args...]")
        print()
        print("COMANDOS:")
        print("  guardar '<texto>' [categoria]     Guarda una memoria")
        print("  buscar '<query>' [top_k]          Busca por similitud semántica")
        print("  listar [categoria] [limite]       Lista memorias almacenadas")
        print("  contar                            Total de memorias")
        print("  borrar <id>                       Borra una memoria por ID")
        print()
        print("EJEMPLOS:")
        print('  ./celebro.py guardar "Servidor web en 192.168.1.10" infra')
        print('  ./celebro.py buscar "¿dónde está el servidor?" 3')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "guardar":
        if len(sys.argv) < 3:
            print("❌ Falta texto. Uso: guardar '<texto>' [categoria]")
            sys.exit(1)
        texto = sys.argv[2]
        cat = sys.argv[3] if len(sys.argv) > 3 else "general"
        mid = celebro.guardar(texto, cat)
        print(f"✅ Guardado [id={mid}] cat={cat}")
        print(f"   {texto[:80]}...")

    elif cmd == "buscar":
        if len(sys.argv) < 3:
            print("❌ Falta query. Uso: buscar '<query>' [top_k]")
            sys.exit(1)
        query = sys.argv[2]
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print(f"🔍 Buscando: '{query}' (top {top_k})\n")
        results = celebro.buscar(query, top_k)
        if not results:
            print("❌ No se encontraron memorias.")
            sys.exit(0)
        for i, r in enumerate(results, 1):
            print(f"{i}. [⭐ {r['score']}] [{r['categoria']}] {r['texto'][:120]}...")

    elif cmd == "listar":
        cat = sys.argv[2] if len(sys.argv) > 2 else None
        limite = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        results = celebro.listar(cat, limite)
        print(f"📊 {len(results)} memorias:\n")
        for r in results:
            cat_str = f"[{r['categoria']}] " if r['categoria'] else ""
            print(f"  {r['id'][:8]}... {cat_str}{r['texto'][:80]}...")

    elif cmd == "contar":
        n = celebro.contar()
        print(f"📊 Total memorias: {n}")

    elif cmd == "borrar":
        if len(sys.argv) < 3:
            print("❌ Falta ID. Uso: borrar <id>")
            sys.exit(1)
        celebro.borrar(sys.argv[2])
        print("🗑️ Memoria borrada.")

    else:
        print(f"❌ Comando desconocido: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
