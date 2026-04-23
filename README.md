# 🎉 CELEBRO

```
  _____ ______ _      ______ ____  _____   ____  
 / ____|  ____| |    |  ____|  _ \|  __ \ / __ \ 
| |    | |__  | |    | |__  | |_) | |__) | |  | |
| |    |  __| | |    |  __| |  _ <|  _  /| |  | |
| |____| |____| |____| |____| |_) | | \ \| |__| |
 \_____|______|______|______|____/|_|  \_\\____/ 
```

> **Un cerebro que CELEBRA tener memoria.** 🧠🎊

**CELEBRO** es un sistema de memoria persistente, privada y ultrarrápida para **cualquier agente IA**: Hermes, OpenClaw, LangChain, CrewAI, AutoGPT... o el tuyo propio.

---

## 🚀 ¿Por qué CELEBRO?

| Problema con Mem0/Chroma | Solución CELEBRO |
|---|---|
| 🐌 Lento: LLM interno para cada `add()` | ⚡ Solo embeddings: **2-5 segundos** por guardado |
| 🔒 Requiere claves API externas | 🔓 **100% local**, cero APIs |
| 📦 Dependencias pesadas (spaCy, etc.) | 🪶 Solo `qdrant-client` + `requests` |
| 🕳️ Caja negra difícil de auditar | 📖 **~150 líneas**, código legible |
| 🔄 Bloqueos de base de datos | 🎯 Qdrant local **sin servicios** de fondo |

---

## 🏗️ Arquitectura

```
    ┌─────────────┐      ┌──────────────┐      ┌─────────────┐
    │   Agente    │─────▶│   Ollama     │─────▶│   Vector    │
    │   IA        │      │ nomic-embed  │      │   (Qdrant)  │
    │             │◀─────│   (768d)     │◀─────│   (cosine)  │
    └─────────────┘      └──────────────┘      └──────┬──────┘
                                                       │
                                              ┌────────▼────────┐
                                              │    SQLite       │
                                              │  (texto real)   │
                                              └─────────────────┘
```

**Flujo:**
1. Texto → embedding vía **Ollama** (nomic-embed-text)
2. Vector → indexado en **Qdrant** local (búsqueda por similitud)
3. Texto original → guardado en **SQLite** (siempre legible)

---

## ⚡ Instalación Rápida

### 1. Prerrequisitos

```bash
# Instalar Ollama (si no lo tienes)
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo de embeddings
ollama pull nomic-embed-text
```

### 2. Instalar CELEBRO

```bash
git clone https://github.com/jcorcuera/celebro.git
cd celebro
pip install -r requirements.txt
chmod +x celebro.py
```

### 3. ¡Probar!

```bash
./celebro.py guardar "Mi servidor web está en 10.0.0.50" infra
./celebro.py buscar "¿dónde está el servidor?" 3
```

---

## 📖 Uso

### CLI

```bash
# Guardar memoria
./celebro.py guardar "<texto>" [categoría]

# Buscar por similitud semántica
./celebro.py buscar "<consulta>" [top_k]

# Listar memorias
./celebro.py listar [categoría] [límite]

# Contar
./celebro.py contar

# Borrar por ID
./celebro.py borrar <uuid>
```

### Como librería Python

```python
from celebro import Celebro

cb = Celebro()

# Guardar información
cb.guardar("El Agente Smith es experto en OSINT", categoria="seguridad")

# Recuperar por similitud
for resultado in cb.buscar("¿Qué hace Smith?", top_k=3):
    print(f"[{resultado['score']}] {resultado['texto']}")
```

---

## 🔧 Configuración

| Variable | Descripción | Default |
|---|---|---|
| `OLLAMA_URL` | URL del servidor Ollama | `http://localhost:11434` |
| `CELEBRO_PATH` | Directorio de datos | `~/.celebro` |

```bash
export OLLAMA_URL="http://192.168.1.50:11434"
export CELEBRO_PATH="/mnt/nas/celebro_data"
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🤝 Integración con agentes

### LangChain
```python
from langchain.tools import Tool
from celebro import Celebro

cb = Celebro()

tool = Tool(
    name="memoria",
    func=lambda q: str(cb.buscar(q, top_k=3)),
    description="Busca en la memoria persistente del agente"
)
```

### CrewAI
```python
from crewai.tools import tool
from celebro import Celebro

cb = Celebro()

@tool
def recuerdos(query: str) -> str:
    """Recupera información de la memoria del agente."""
    return str(cb.buscar(query, top_k=3))
```

---

## 🎭 Origen del nombre

> **CELEBRO** = **CEREBRO** que **CELEBRA** tener memoria.

Nacido de la frustración con Mem0 en hardware modesto, celebramos cada `add()` que tarda 3 segundos en vez de 10 minutos 🎉

---

## 📜 Licencia

MIT License — ver [LICENSE](LICENSE).

---

## 🙏 Créditos

- **Autor:** [@corcuman](https://github.com/corcuman)
- **Co-creador:** NeoIA (agente local que sufría con Mem0)
- **Inspiración:** Hardware humilde que no merecía quedarse sin memoria
