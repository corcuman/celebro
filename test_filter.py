import json
import os
import sys

# Asegurar que podemos importar el módulo celebro
sys.path.append('/home/jcorcuera/celebro_git_work_v3')
from celebro import Cerebro

def test():
    c = Cerebro()
    print("--- Guardando datos de prueba ---")
    
    # 1. Guardar memoria con source 'test_script' y tags ['importante', 'v3']
    c.guardar("Esta es una memoria de prueba para filtros", "test", "test_script", ["importante", "v3"])
    
    # 2. Guardar memoria con source 'manual' y tags ['basura']
    c.guardar("Otra memoria que no debería salir en el primer filtro", "test", "manual", ["basura"])

    print("\n--- Buscando con filtro source='test_script' ---")
    # Nota: Pasamos el query "memoria". Qdrant buscará semánticamente y luego filtrará.
    results = c.buscar("memoria", source="test_script")
    for r in results:
        print(f"ID: {r['id']}, Source: {r['source']}, Tags: {r['tags']}, Texto: {r['texto']}")
        if r['source'] != "test_script":
            print(f"❌ ERROR: Source {r['source']} no coincide con 'test_script'")
        else:
            print("✅ Source coincide")

    print("\n--- Buscando con filtro tags=['v3'] ---")
    results = c.buscar("memoria", tags=["v3"])
    for r in results:
        print(f"ID: {r['id']}, Source: {r['source']}, Tags: {r['tags']}, Texto: {r['texto']}")
        if "v3" not in r['tags']:
            print(f"❌ ERROR: Tag 'v3' no encontrado en {r['tags']}")
        else:
            print("✅ Tag coincide")

    print("\n--- Buscando con ambos filtros ---")
    results = c.buscar("memoria", source="test_script", tags=["v3"])
    for r in results:
        print(f"ID: {r['id']}, Source: {r['source']}, Tags: {r['tags']}, Texto: {r['texto']}")
        if r['source'] != "test_script" or "v3" not in r['tags']:
            print("❌ ERROR: Filtro combinado falló")
        else:
            print("✅ Filtros combinados coinciden")

if __name__ == "__main__":
    test()
