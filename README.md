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

**Memoria persistente, privada y ultrarrápida para cualquier agente IA.**

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

## 🏗️ Arquitectura

```
Texto ──► Ollama (nomic-embed-text) ──► Vector (768 dims)
                                              │
                                              ▼
                                       Qdrant local (vectores + metadatos)
                                              │
                                              ▼
                                       SQLite (texto + metas + tags)
```

**🔑 Clave:** No usamos LLM para generar texto. Solo embeddings. Eso hace que sea **ultrarrápido**. Ahora incluye almacenamiento persistente de **fuente** y **etiquetas** para un filtrado y organización superior.

## 🛠️ Stack Tecnológico

CELEBRO no es solo un script; es una orquestación ligera de tres tecnologías fundamentales:

1.  **[Ollama](https://ollama.com/):** Generación de **embeddings** con el modelo `nomic-embed-text`.
2.  **[Qdrant](https://qdrant.tech/):** Búsqueda vectorial local con soporte para payload enriquecido (`cat`, `source`, `tags`).
3.  **[SQLite](https://sqlite.org/):** Base relacional para texto, metadatos estructurados y registro histórico.

## 📦 Instalación

### 1. Preparar el entorno (Ollama)

```bash
ollama pull nomic-embed-text
```

### 2. Clonar y configurar CELEBRO

```bash
git clone https://github.com/corcuman/celebro.git
cd celebro

# Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x celebro.py
```

## 🎯 Uso

### CLI (Mejorado)

```bash
# Guardar memoria con categoría, fuente y tags (formato JSON)
./celebro.py guardar "Agente Smith es OSINT" homelab terminal '["seguridad", "verificado"]'

# Buscar memorias (muestra score y metadatos)
./celebro.py buscar "Agente Smith" 3
```

### Librería Python

```python
from celebro import Celebro

cb = Celebro()

# Guardar con metadatos opcionales
cb.guardar(
    texto="Usuario prefiere español", 
    categoria="preferencias", 
    source="chat_telegram", 
    tags=["idioma", "personal"]
)

# Buscar (devuelve diccionario con texto, score, source y tags)
resultados = cb.buscar("idioma del usuario", top_k=3)
for r in resultados:
    print(f"[{r['score']:.3f}] Source: {r['source']} | Tags: {r['tags']} | {r['texto']}")
```

## 🧪 Tests

```bash
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

## 🙏 Créditos

- **Autor:** [@corcuman](https://github.com/corcuman)
- **Co-creador:** NeoIA (agente local que sufría con Mem0)
- **Inspiración:** Hardware humilde que no merecía quedarse sin memoria
