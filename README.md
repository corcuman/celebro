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

**🔑 Clave:** No usamos LLM para generar texto. Solo embeddings. Eso hace que sea **ultrarrápido**.

## 🛠️ Stack Tecnológico

CELEBRO no es solo un script; es una orquestación ligera de tres tecnologías fundamentales:

1.  **[Ollama](https://ollama.com/):** El motor de IA. Lo usamos exclusivamente para generar **embeddings** (vectores numéricos que representan el significado del texto).
    - **Modelo:** `nomic-embed-text` (768 dimensiones). Elegido por su equilibrio entre velocidad y precisión semántica.
2.  **[Qdrant](https://qdrant.tech/):** El motor de búsqueda vectorial. 
    - **Modo:** Local Storage. CELEBRO configura Qdrant para persistir los vectores directamente en disco (`~/.celebro/vectores`), permitiendo búsquedas por similitud de coseno ultrarrápidas sin necesidad de un servidor externo.
3.  **[SQLite](https://sqlite.org/):** La base de datos relacional.
    - **Propósito:** Qdrant es excelente con vectores, pero SQLite es mejor para manejar el texto original, metadatos (categorías) y fechas. CELEBRO sincroniza ambos mediante un ID único (UUID).

## 📦 Instalación

### 1. Preparar el entorno (Ollama)

Primero, necesitas tener Ollama instalado y funcionando en tu máquina.

```bash
# Descargar el modelo de embeddings (esencial)
ollama pull nomic-embed-text
```

### 2. Clonar y configurar CELEBRO

```bash
git clone https://github.com/corcuman/celebro.git
cd celebro

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Hacer el script ejecutable
chmod +x celebro.py
```

### 3. Variables de Entorno (Opcional)

Si necesitas cambiar las rutas por defecto:
- `OLLAMA_URL`: URL de tu instancia de Ollama (def: `http://localhost:11434`).
- `CELEBRO_PATH`: Carpeta donde se guardarán las bases de datos (def: `~/.celebro`).

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
