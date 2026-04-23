# 🎉 CELEBRO

<pre>
  _____ ______ _      ______ ____  _____   ____  
 / ____|  ____| |    |  ____|  _ \|  __ \ / __ \ 
| |    | |__  | |    | |__  | |_) | |__) | |  | |
| |    |  __| | |    |  __| |  _ <|  _  /| |  | |
| |____| |____| |____| |____| |_) | | \ \| |__| |
 \_____|______|______|______|____/|_|  \_\\____/ 
</pre>

> **Un cerebro que CELEBRA tener memoria.** 🧠🎊

**CELEBRO** es un sistema de memoria persistente, privada y ultrarrápida para **cualquier agente IA**: Hermes, OpenClaw, LangChain, CrewAI, AutoGPT... o el tuyo propio.

---

## 🚀 ¿Por qué CELEBRO?

| Problema con Mem0/Chroma | Solución CELEBRO |
|---|---|
| Requiere clave API de OpenAI | 100% local, cero APIs externas |
| Validaciones caprichosas | Código propio, control absoluto |
| `add()` tarda minutos | `add()` tarda 2-5 segundos |
| 200+ líneas de abstracción | ~150 líneas, auditable |
| Depende de spaCy, fastembed | Solo `qdrant-client` + `requests` |

## 🏗️ Arquitectura

```
Texto ──► Ollama (nomic-embed-text) ──► Vector (768 dims)
                                              │
                                              ▼
                                       Qdrant local (vectores)
                                              │
                                              ▼
                                       SQLite (texto original)
```

**Clave:** No usamos LLM para generar texto. Solo embeddings. Eso hace que sea ultrarrápido.

## 📦 Instalación

### Requisitos
- Python 3.10+
- Ollama corriendo localmente (`http://localhost:11434`)
- Modelo de embeddings: `nomic-embed-text` (pull con `ollama pull nomic-embed-text`)

### Desde GitHub
```bash
git clone https://github.com/corcuman/celebro.git
cd celebro
pip install -r requirements.txt
```

## 🎯 Uso

### CLI
```bash
# Guardar memoria
./celebro.py guardar "El Agente Smith es OSINT en CT102 ParrotOS" homelab

# Buscar memorias
./celebro.py buscar "Agente Smith OSINT" 3
```

### Librería Python
```python
from celebro import Celebro

cb = Celebro()

# Guardar
cb.guardar("Usuario prefiere español para comunicaciones", preferencias)

# Buscar
resultados = cb.buscar("idioma del usuario", top_k=3)
for r in resultados:
    print(f"[{r['score']:.3f}] {r['texto']}")
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
