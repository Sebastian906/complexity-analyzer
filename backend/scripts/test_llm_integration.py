"""
Test de integración de LLMs - USA CRÉDITOS DE API

Ejecutar SOLO cuando quieras verificar que los LLMs funcionan.
"""

import asyncio

# Ensure project root is on sys.path so `app` package is importable
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.infrastructure.llm import LLMFactory, ClaudeAdapter, GeminiAdapter
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_claude():
    """Test Claude (usa créditos)"""
    print("\n" + "="*50)
    print("TESTING CLAUDE API")
    print("="*50)
    
    if not settings.ANTHROPIC_API_KEY:
        print("✗ Claude API Key not configured")
        return False
    
    try:
        claude = ClaudeAdapter()
        
        # Test simple
        response = await claude.generate(
            prompt="Responde SOLO con: OK",
            system_prompt="Eres un asistente conciso."
        )
        
        print(f"✓ Claude responded: {response.content}")
        print(f"  Model: {response.model}")
        print(f"  Tokens: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"✗ Claude test failed: {e}")
        return False

async def test_gemini():
    """Test Gemini (usa créditos)"""
    print("\n" + "="*50)
    print("TESTING GEMINI API")
    print("="*50)
    
    if not settings.GOOGLE_API_KEY:
        print("✗ Gemini API Key not configured")
        return False
    
    try:
        gemini = GeminiAdapter()
        
        # Test simple
        response = await gemini.generate(
            prompt="Responde SOLO con: OK",
            system_prompt="Eres un asistente conciso."
        )
        
        print(f"✓ Gemini responded: {response.content}")
        print(f"  Model: {response.model}")
        print(f"  Tokens: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"✗ Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complexity_validation():
    """Test validación de complejidad con LLM"""
    print("\n" + "="*50)
    print("TESTING COMPLEXITY VALIDATION")
    print("="*50)
    
    try:
        llm = LLMFactory.create_primary()
        
        code = """algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                swap(A[j], A[j + 1])
            end
        end
    end
end"""
        
        from app.infrastructure.llm.prompt_templates import COMPLEXITY_VALIDATION_PROMPT
        
        prompt = COMPLEXITY_VALIDATION_PROMPT.format(
            algorithm_code=code,
            big_o="O(n²)",
            omega="Ω(n²)",
            theta="Θ(n²)"
        )
        
        response = await llm.generate_json(prompt)
        
        print(f"✓ LLM validation complete")
        print(f"  Matches our analysis: {response.get('matches_our_analysis')}")
        print(f"  LLM Big O: {response.get('big_o')}")
        print(f"  Reasoning: {response.get('reasoning', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Complexity validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all LLM tests"""
    print("\n" + "="*60)
    print("⚠️  LLM INTEGRATION TESTS - THESE USE API CREDITS ⚠️")
    print("="*60)
    
    input("\nPress ENTER to continue or CTRL+C to cancel...")
    
    results = {
        "claude": await test_claude(),
        "gemini": await test_gemini(),
        "validation": await test_complexity_validation(),
    }
    
    print("\n" + "="*50)
    print("RESULTS SUMMARY")
    print("="*50)
    
    for name, success in results.items():
        icon = "✓" if success else "✗"
        print(f"{icon} {name.title()}: {'PASS' if success else 'FAIL'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ ALL LLM TESTS PASSED!")
    else:
        print("\n⚠ SOME LLM TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)