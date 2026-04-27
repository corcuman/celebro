#!/usr/bin/env /home/jcorcuera/cerebro_env/bin/python
"""
CEREBRO - Sistema de memoria persistente propio.
Embeddings via Ollama (nomic-embed-text) + Qdrant local + SQLite.
Versión mejorada con metadatos y sistema de relaciones.
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
        # Fase 2: Tabla de relaciones
        self.sql.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_src TEXT NOT NULL,
                type TEXT NOT NULL,
                id_dst TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_src) REFERENCES textos(id),
                FOREIGN KEY (id_dst) REFERENCES textos(id)
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
            print(f"[⚠️] SQLite error al guardar: {e}")

        return mid

    def add_relation(self, id_src: str, relation_type: str, id_dst: str) -> bool:
        # Validar existencia de ambos IDs
        cursor = self.sql.execute("SELECT id FROM textos WHERE id IN (?, ?)", (id_src, id_dst))
        found = [row[0] for row in cursor.fetchall()]
        
        if id_src not in found:
            print(f"❌ Error: El ID de origen {id_src} no existe.")
            return False
        if id_dst not in found:
            print(f"❌ Error: El ID de destino {id_dst} no existe.")
            return False
            
        try:
            self.sql.execute(
                "INSERT INTO relationships (id_src, type, id_dst) VALUES (?, ?, ?)",
                (id_src, relation_type, id_dst)
            )
            self.sql.commit()
            return True
        except Exception as e:
            print(f"⚠️ Error al crear relación: {e}")
            return False

    def get_relations(self, memory_id: str) -> list:
        # Relaciones salientes (outbound) y entrantes (inbound)
        # Salientes: memory_id -> destino
        # Entrantes: origen -> memory_id
        
        query = """
            SELECT r.type, r.id_dst as target_id, t.texto as target_texto, 'out' as direction, r.fecha
            FROM relationships r
            JOIN textos t ON r.id_dst = t.id
            WHERE r.id_src = ?
            UNION ALL
            SELECT r.type, r.id_src as target_id, t.texto as target_texto, 'in' as direction, r.fecha
            FROM relationships r
            JOIN textos t ON r.id_src = t.id
            WHERE r.id_dst = ?
        """
        cursor = self.sql.execute(query, (memory_id, memory_id))
        rows = cursor.fetchall()
        
        return [
            {
                "type": r[0],
                "target_id": r[1],
                "target_texto": r[2],
                "direction": r[3],
                "fecha": r[4]
            }
            for r in rows
        ]

    def buscar(self, query: str, top_k: int = 5, source: str = None, tags: list = None) -> list:
        vector = self._embed(query)
        
        filters = None
        if source or tags:
            must_conditions = []
            if source:
                must_conditions.append(FieldCondition(key="source", match=MatchValue(value=source)))
            if tags:
                must_conditions.append(FieldCondition(key="tags", match=MatchAny(any=tags)))
            
            if must_conditions:
                filters = Filter(must=must_conditions)
        
        results = self.qdrant.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=top_k,
            query_filter=filters
        )

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
        print("  guardar '<texto>' [cat] [src] [tags_json]  - Guarda una memoria")
        print("  buscar '<query>' [top_k] [src] [tags_json] - Busca memorias")
        print("  relacionar <id_src> <tipo> <id_dst>        - Crea una relación entre memorias")
        print("  relaciones <id>                           - Lista relaciones de una memoria")
        print("  contar                                     - Cuenta memorias")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "guardar":
        if len(sys.argv) < 3:
            print("❌ Falta texto.")
            sys.exit(1)
        texto = sys.argv[2]
        cat = sys.argv[3] if len(sys.argv) > 3 else "general"
        source = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = json.loads(tags_str) if tags_str else None
        
        mid = cerebro.guardar(texto, cat, source=source, tags=tags)
        print(f"✅ Guardado [id={mid}]")

    elif cmd == "buscar":
        if len(sys.argv) < 3:
            print("❌ Falta query.")
            sys.exit(1)
        query = sys.argv[2]
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        source = sys.argv[4] if len(sys.argv) > 4 else None
        tags_str = sys.argv[5] if len(sys.argv) > 5 else None
        tags = json.loads(tags_str) if tags_str else None

        results = cerebro.buscar(query, top_k, source=source, tags=tags)
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['id']}] [{r['score']}] {r['texto'][:100]}...")

    elif cmd == "relacionar":
        if len(sys.argv) < 4:
            print("❌ Uso: relacionar <id_src> <tipo> <id_dst>")
            sys.exit(1)
        if cerebro.add_relation(sys.argv[2], sys.argv[3], sys.argv[4]):
            print(f"✅ Relación '{sys.argv[3]}' creada.")

    elif cmd == "relaciones":
        if len(sys.argv) < 3:
            print("❌ Uso: relaciones <id>")
            sys.exit(1)
        rels = cerebro.get_relations(sys.argv[2])
        if not rels:
            print("No se encontraron relaciones.")
        else:
            for r in rels:
                arrow = "->" if r['direction'] == 'out' else "<-"
                print(f"[{r['direction']}] {sys.argv[2]} {arrow} ({r['type']}) {arrow} {r['target_id']}")
                print(f"      Texto: {r['target_texto'][:80]}...")

    elif cmd == "contar":
        print(f"📊 Total: {cerebro.contar()}")

    else:
        print(f"❌ Comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
