<div align="center">

<pre>
  ██████╗███████╗██╗     ███████╗██████╗ ██████╗  ██████╗ 
 ██╔════╝██╔════╝██║     ██╔════╝██╔══██╗██╔══██╗██╔═══██╗
 ██║     █████╗  ██║     █████╗  ██████╔╝██████╔╝██║   ██║
 ██║     ██╔══╝  ██║     ██╔══╝  ██╔══██╗██╔══██╗██║   ██║
 ╚██████╗███████╗███████╗███████╗██████╔╝██║  ██║╚██████╔╝
  ╚═════╝╚══════╝╚══════╝╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 

       [ memoria persistente para agentes con boca cerrada ]
</pre>

**Memoria persistente, relacional, privada y ultrarrápida para cualquier agente IA.**

Hermes · OpenClaw · LangChain · CrewAI · AutoGPT · El tuyo propio

---

</div>

## 🚀 ¿Por qué CELEBRO?

| ❌ Problema con Mem0/Chroma | ✅ Solución CELEBRO |
|---|---|
| Requiere clave API de OpenAI | 100% local, cero APIs externas |
| Validaciones caprichosas | Código propio, control absoluto |
| `add()` tarda minutos | `add()` tarda 2-5 segundos |
| 200+ líneas de abstracción | ~150 líneas, auditable |
| Depende de spaCy, fastembed | Solo `qdrant-client` + `requests` |
| Sin metadatos estructurados | Soporte para `source` y `tags` |
| Búsqueda puramente plana | **Sistema de relaciones (Fase 2)** |

## 🏗️ Arquitectura (Mejorada)

```
Texto ──► Ollama (nomic-embed-text) ──► Vector (768 dims) ──► Qdrant (vectores + metas)
                                              │
                                              ▼
                                       SQLite (texto + metas + tags + RELACIONES)
```

**🔑 Clave:** No usamos LLM para generar texto. Solo embeddings. Eso hace que sea **ultrarrápido**. Ahora incluye almacenamiento persistente de **fuente**, **etiquetas** y un **sistema de relaciones** (grafo de conocimiento ligero) que permite conectar memorias de forma direccional y tipada.

## 🛠️ Stack Tecnológico

1.  **[Ollama](https://ollama.com/):** Generación de **embeddings** (`nomic-embed-text`).
2.  **[Qdrant](https://qdrant.tech/):** Búsqueda vectorial local con payload enriquecido (`cat`, `source`, `tags`).
3.  **[SQLite](https://sqlite.org/):** Base relacional para datos estructurados y **relaciones (relationships)** entre memorias (`id_src`, `type`, `id_dst`).

## 🎯 Uso

### CLI (Mejorado con Relaciones)

```bash
# 1. Guardar memoria con metadatos
./celebro.py guardar "Agente Smith es OSINT" homelab terminal '["seguridad"]'

# 2. Buscar memorias (con filtros opcionales de Qdrant)
./celebro.py buscar "Agente Smith" 3

# 3. Crear relaciones entre memorias (Fase 2)
./celebro.py relacionar <id_origen> "expands_on" <id_destino>

# 4. Listar relaciones de una memoria
./celebro.py relaciones <id_memoria>
```

### Librería Python

```python
from celebro import Celebro

cb = Celebro()

# Guardar con metadatos
id1 = cb.guardar("Usuario prefiere español", categoria="preferencias")
id2 = cb.guardar("Notificar en español siempre", categoria="protocolos")

# Crear relación
cb.add_relation(id2, "follows", id1)

# Consultar relaciones
relaciones = cb.get_relations(id2)
for r in relaciones:
    print(f"[{r['type']}] -> {r['texto'][:50]}...")
```

## 🧪 Tests

```bash
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

## 🙏 Créditos

- **Autor:** [@corcuman](https://github.com/corcuman)
- **Co-creador:** NeoIA
- **Inspiración:** Hardware humilde que no merecía quedarse sin memoria
