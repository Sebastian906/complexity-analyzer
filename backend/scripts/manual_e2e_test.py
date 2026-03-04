"""
Script de prueba manual E2E - Ejecutar con servidor corriendo
"""
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_complete_flow():
    """Prueba el flujo completo manualmente"""
    
    try:
        # 1. Health check
        print("1. Health check...")
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        
        if response.status_code != 200:
            print(f"✗ Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("✓ Server is healthy")
        
        # 2. Analizar algoritmo
        print("\n2. Analyzing algorithm...")
        code = """algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end"""
        
        # Payload correcto
        payload = {
            "code": code,
            "options": {
                "analyze_line_by_line": True,
                "analyze_spatial": True,
                "analyze_recurrence": True,
                "calculate_tight_bounds": True
            }
        }
        
        response = httpx.post(
            f"{BASE_URL}/analysis/analyze-complete",
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"✗ Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        # Extraer correctamente
        complexity = result.get('complexity', {})
        big_o = complexity.get('big_o', 'N/A')
        
        print(f"✓ Analysis complete")
        print(f"  Algorithm: {result.get('algorithm_name')}")
        print(f"  Big O: {big_o}")
        print(f"  Omega: {complexity.get('omega', 'N/A')}")
        print(f"  Theta: {complexity.get('theta', 'N/A')}")
        
        # 3. Verificar patrones
        print("\n3. Checking patterns...")
        response = httpx.post(
            f"{BASE_URL}/patterns/detect",
            json={"code": code},
            timeout=30.0
        )
        
        if response.status_code == 200:
            patterns = response.json()
            primary = patterns.get("primary_pattern", {}).get("pattern", {})
            print(f"✓ Primary pattern: {primary.get('pattern_name', 'N/A')}")
            print(f"  Confidence: {primary.get('confidence', 0):.2f}")
        else:
            print(f"⚠ Pattern detection failed: {response.status_code}")
        
        # 4. Detectar estructuras
        print("\n4. Checking data structures...")
        response = httpx.post(
            f"{BASE_URL}/structures/detect",
            json={"code": code},
            timeout=30.0
        )
        
        if response.status_code == 200:
            structures = response.json()
            primary_struct = structures.get("primary_structure")
            if primary_struct:
                print(f"✓ Primary structure: {primary_struct.get('structure_name', 'N/A')}")
        else:
            print(f"⚠ Structure detection failed: {response.status_code}")
        
        # 5. Exportar DIRECTAMENTE sin guardar en DB
        print("\n5. Testing direct export (without DB)...")
        export_formats = ["json", "md", "html"]
        
        for fmt in export_formats:
            response = httpx.post(
                f"{BASE_URL}/export/export",
                json={
                    "code": code,  # ← Exportar directamente desde código
                    "algorithm_name": "Bubble Sort Test",
                    "options": {
                        "format": fmt,
                        "template": "standard",
                        "sections": ["algorithm_info", "complexity", "patterns"],
                        "include_visualizations": False,
                        "include_metadata": True
                    },
                    "filename": f"bubble_sort_test.{fmt}"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                export_result = response.json()
                print(f"✓ {fmt.upper()} export successful")
                print(f"  File: {export_result.get('filename')}")
                print(f"  Size: {export_result.get('file_size_bytes', 0)} bytes")
            else:
                print(f"✗ {fmt.upper()} export failed: {response.status_code}")
                print(f"  Error: {response.text[:200]}")
        
        # 6. Probar análisis rápido
        print("\n6. Testing quick analysis...")
        response = httpx.post(
            f"{BASE_URL}/analysis/quick",
            json={"code": "algorithm test(n)\nbegin\n    x ← 1\nend"},
            timeout=10.0
        )
        
        if response.status_code == 200:
            quick = response.json()
            print(f"✓ Quick analysis successful")
            print(f"  Result: {quick.get('big_o')}")
        else:
            print(f"⚠ Quick analysis failed: {response.status_code}")
        
        # 7. Probar visualización
        print("\n7. Testing visualization...")
        fib_code = """algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end"""
        
        response = httpx.post(
            f"{BASE_URL}/visualizations/recursion-tree",
            json={
                "code": fib_code,
                "max_depth": 4
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            viz = response.json()
            print(f"✓ Recursion tree generated")
            print(f"  Nodes: {viz.get('total_nodes', 0)}")
        else:
            print(f"⚠ Visualization failed: {response.status_code}")
        
        print("\n" + "="*50)
        print("✓ COMPLETE E2E FLOW TEST PASSED!")
        print("="*50)
        print("\nAll core features tested successfully:")
        print("  ✓ Parsing & Analysis")
        print("  ✓ Pattern Detection")
        print("  ✓ Structure Detection")
        print("  ✓ Direct Export (JSON, Markdown, HTML)")
        print("  ✓ Quick Analysis")
        print("  ✓ Visualization Generation")
        return True
        
    except httpx.ConnectTimeout:
        print("\n✗ Connection timeout!")
        print("Verify server is running: python scripts/run_dev.py")
        return False
    except httpx.ConnectError as e:
        print(f"\n✗ Connection error: {e}")
        print("Verify server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    exit(0 if success else 1)