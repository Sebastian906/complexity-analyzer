# scripts/diagnose_server.py
"""Diagnostica problemas de conexión con el servidor"""

import httpx
import time

def diagnose():
    """Diagnóstico completo"""
    
    print("DIAGNÓSTICO DEL SERVIDOR")
    print("=" * 50)
    
    # 1. Verificar conectividad básica
    print("\n1. Probando conectividad básica...")
    try:
        response = httpx.get("http://localhost:8000/", timeout=5.0)
        print(f"✓ Root endpoint responde: {response.status_code}")
    except httpx.ConnectTimeout:
        print("✗ TIMEOUT en root endpoint!")
        print("  El servidor no responde a tiempo.")
        return
    except httpx.ConnectError as e:
        print(f"✗ ERROR de conexión: {e}")
        print("  El servidor no está corriendo en el puerto 8000")
        return
    
    # 2. Verificar health endpoint
    print("\n2. Probando health endpoint...")
    try:
        start = time.time()
        response = httpx.get("http://localhost:8000/api/v1/health", timeout=10.0)
        elapsed = time.time() - start
        
        print(f"✓ Health endpoint OK: {response.status_code}")
        print(f"  Tiempo de respuesta: {elapsed:.2f}s")
        
        if elapsed > 5:
            print("  ⚠ ADVERTENCIA: Respuesta lenta (>5s)")
            print("     Posible problema con MongoDB/Redis")
    except httpx.ConnectTimeout:
        print("✗ TIMEOUT en health endpoint!")
        print("  Posible problema con inicialización de DB")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 3. Verificar OpenAPI
    print("\n3. Probando OpenAPI schema...")
    try:
        response = httpx.get("http://localhost:8000/openapi.json", timeout=5.0)
        print(f"✓ OpenAPI schema OK: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 4. Probar análisis rápido
    print("\n4. Probando análisis simple...")
    try:
        code = "algorithm test(n)\nbegin\n    x ← 1\nend"
        
        start = time.time()
        response = httpx.post(
            "http://localhost:8000/api/v1/analysis/quick",
            params={"code": code},
            timeout=15.0
        )
        elapsed = time.time() - start
        
        print(f"✓ Quick analysis OK: {response.status_code}")
        print(f"  Tiempo de respuesta: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Big O detectado: {data.get('big_o')}")
    except httpx.ConnectTimeout:
        print("✗ TIMEOUT en quick analysis!")
        print("  El parser/analyzer está tardando demasiado")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    diagnose()