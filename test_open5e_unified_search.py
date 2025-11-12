#!/usr/bin/env python3
"""Test script to verify Open5e /v2/search/ endpoint behavior.

This script manually tests the unified search endpoint with different parameter
combinations to verify:
- Basic query searches
- Fuzzy matching with typos
- Vector/semantic search
- Cross-entity searches
- Parameter handling

Results are documented and saved to test_results.md
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://api.open5e.com/v2"


async def test_search(
    query: str,
    fuzzy: bool = False,
    vector: bool = False,
    object_model: str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Test a single search query.

    Args:
        query: Search term
        fuzzy: Enable fuzzy matching
        vector: Enable semantic/vector search
        object_model: Filter to specific content type
        strict: Only return explicitly requested search types

    Returns:
        Response data from the API
    """
    params: dict[str, Any] = {"query": query}

    if fuzzy:
        params["fuzzy"] = "true"
    if vector:
        params["vector"] = "true"
    if object_model:
        params["object_model"] = object_model
    if strict:
        params["strict"] = "true"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BASE_URL}/search/", params=params)
        response.raise_for_status()
        return response.json()


async def run_tests() -> None:
    """Run all test cases and document results."""
    results = {
        "base_url": BASE_URL,
        "endpoint": "/v2/search/",
        "tests": [],
        "summary": {},
    }

    # Test 1: Basic exact query search
    print("Test 1: Basic exact query search (Fireball)...")
    test1 = {
        "name": "Test 1: Basic Exact Query",
        "params": {"query": "Fireball"},
        "description": "Search for 'Fireball' spell with defaults",
    }
    try:
        response = await test_search("Fireball")
        test1["status"] = "success"
        test1["results_count"] = len(response.get("results", []))
        test1["first_result"] = (
            response.get("results", [{}])[0] if response.get("results") else None
        )
        test1["response_keys"] = list(response.keys())
        results["tests"].append(test1)
        print(f"  ✓ Found {test1['results_count']} results")
    except Exception as e:
        test1["status"] = "error"
        test1["error"] = str(e)
        results["tests"].append(test1)
        print(f"  ✗ Error: {e}")

    # Test 2: Fuzzy matching with typo
    print("\nTest 2: Fuzzy matching with typo ('firbal')...")
    test2 = {
        "name": "Test 2: Fuzzy Matching - Typo",
        "params": {"query": "firbal", "fuzzy": True},
        "description": "Search for 'firbal' (typo) with fuzzy=true",
    }
    try:
        response = await test_search("firbal", fuzzy=True)
        test2["status"] = "success"
        test2["results_count"] = len(response.get("results", []))
        test2["first_result"] = (
            response.get("results", [{}])[0] if response.get("results") else None
        )
        test2["response_keys"] = list(response.keys())
        results["tests"].append(test2)
        print(f"  ✓ Found {test2['results_count']} results")
        if test2["first_result"]:
            print(f"    First result: {test2['first_result'].get('name', 'Unknown')}")
    except Exception as e:
        test2["status"] = "error"
        test2["error"] = str(e)
        results["tests"].append(test2)
        print(f"  ✗ Error: {e}")

    # Test 3: Fuzzy matching without fuzzy flag
    print("\nTest 3: Same typo without fuzzy flag...")
    test3 = {
        "name": "Test 3: Typo without Fuzzy",
        "params": {"query": "firbal", "fuzzy": False},
        "description": "Search for 'firbal' (typo) with fuzzy=false",
    }
    try:
        response = await test_search("firbal", fuzzy=False)
        test3["status"] = "success"
        test3["results_count"] = len(response.get("results", []))
        test3["first_result"] = (
            response.get("results", [{}])[0] if response.get("results") else None
        )
        results["tests"].append(test3)
        print(f"  ✓ Found {test3['results_count']} results")
    except Exception as e:
        test3["status"] = "error"
        test3["error"] = str(e)
        results["tests"].append(test3)
        print(f"  ✗ Error: {e}")

    # Test 4: Vector/semantic search with concept
    print("\nTest 4: Vector/semantic search ('healing magic')...")
    test4 = {
        "name": "Test 4: Vector/Semantic Search",
        "params": {"query": "healing magic", "vector": True},
        "description": "Search for 'healing magic' concept with vector=true",
    }
    try:
        response = await test_search("healing magic", vector=True)
        test4["status"] = "success"
        test4["results_count"] = len(response.get("results", []))
        test4["first_results"] = response.get("results", [])[:3] if response.get("results") else []
        results["tests"].append(test4)
        print(f"  ✓ Found {test4['results_count']} results")
        for i, result in enumerate(test4["first_results"][:3], 1):
            print(f"    {i}. {result.get('name', 'Unknown')}")
    except Exception as e:
        test4["status"] = "error"
        test4["error"] = str(e)
        results["tests"].append(test4)
        print(f"  ✗ Error: {e}")

    # Test 5: Vector search without vector flag
    print("\nTest 5: Same concept without vector flag...")
    test5 = {
        "name": "Test 5: Concept without Vector",
        "params": {"query": "healing magic", "vector": False},
        "description": "Search for 'healing magic' with vector=false",
    }
    try:
        response = await test_search("healing magic", vector=False)
        test5["status"] = "success"
        test5["results_count"] = len(response.get("results", []))
        results["tests"].append(test5)
        print(f"  ✓ Found {test5['results_count']} results")
    except Exception as e:
        test5["status"] = "error"
        test5["error"] = str(e)
        results["tests"].append(test5)
        print(f"  ✗ Error: {e}")

    # Test 6: Object model filtering (Spell)
    print("\nTest 6: Object model filtering (Spell only)...")
    test6 = {
        "name": "Test 6: Object Model Filter - Spell",
        "params": {"query": "cure wounds", "object_model": "Spell"},
        "description": "Search for 'cure wounds' filtering to Spell only",
    }
    try:
        response = await test_search("cure wounds", object_model="Spell")
        test6["status"] = "success"
        test6["results_count"] = len(response.get("results", []))
        test6["first_result"] = (
            response.get("results", [{}])[0] if response.get("results") else None
        )
        results["tests"].append(test6)
        print(f"  ✓ Found {test6['results_count']} results")
    except Exception as e:
        test6["status"] = "error"
        test6["error"] = str(e)
        results["tests"].append(test6)
        print(f"  ✗ Error: {e}")

    # Test 7: Object model filtering (Creature)
    print("\nTest 7: Object model filtering (Creature only)...")
    test7 = {
        "name": "Test 7: Object Model Filter - Creature",
        "params": {"query": "dragon", "object_model": "Creature"},
        "description": "Search for 'dragon' filtering to Creature only",
    }
    try:
        response = await test_search("dragon", object_model="Creature")
        test7["status"] = "success"
        test7["results_count"] = len(response.get("results", []))
        test7["first_results"] = response.get("results", [])[:3] if response.get("results") else []
        results["tests"].append(test7)
        print(f"  ✓ Found {test7['results_count']} results")
        for i, result in enumerate(test7["first_results"][:3], 1):
            print(f"    {i}. {result.get('name', 'Unknown')}")
    except Exception as e:
        test7["status"] = "error"
        test7["error"] = str(e)
        results["tests"].append(test7)
        print(f"  ✗ Error: {e}")

    # Test 8: Combined fuzzy + vector
    print("\nTest 8: Combined fuzzy and vector search...")
    test8 = {
        "name": "Test 8: Fuzzy + Vector",
        "params": {"query": "damge spel", "fuzzy": True, "vector": True},
        "description": "Search for 'damge spel' (typo) with both fuzzy and vector",
    }
    try:
        response = await test_search("damge spel", fuzzy=True, vector=True)
        test8["status"] = "success"
        test8["results_count"] = len(response.get("results", []))
        results["tests"].append(test8)
        print(f"  ✓ Found {test8['results_count']} results")
    except Exception as e:
        test8["status"] = "error"
        test8["error"] = str(e)
        results["tests"].append(test8)
        print(f"  ✗ Error: {e}")

    # Test 9: Another typo - "cury wounds"
    print("\nTest 9: Fuzzy matching with typo ('cury wounds')...")
    test9 = {
        "name": "Test 9: Fuzzy Matching - Another Typo",
        "params": {"query": "cury wounds", "fuzzy": True},
        "description": "Search for 'cury wounds' (typo) with fuzzy=true",
    }
    try:
        response = await test_search("cury wounds", fuzzy=True)
        test9["status"] = "success"
        test9["results_count"] = len(response.get("results", []))
        test9["first_result"] = (
            response.get("results", [{}])[0] if response.get("results") else None
        )
        results["tests"].append(test9)
        print(f"  ✓ Found {test9['results_count']} results")
        if test9["first_result"]:
            print(f"    First result: {test9['first_result'].get('name', 'Unknown')}")
    except Exception as e:
        test9["status"] = "error"
        test9["error"] = str(e)
        results["tests"].append(test9)
        print(f"  ✗ Error: {e}")

    # Test 10: Strict mode test
    print("\nTest 10: Strict mode test...")
    test10 = {
        "name": "Test 10: Strict Mode",
        "params": {"query": "fireball", "fuzzy": True, "strict": True},
        "description": "Search with strict=true (only explicit match types)",
    }
    try:
        response = await test_search("fireball", fuzzy=True, strict=True)
        test10["status"] = "success"
        test10["results_count"] = len(response.get("results", []))
        results["tests"].append(test10)
        print(f"  ✓ Found {test10['results_count']} results")
    except Exception as e:
        test10["status"] = "error"
        test10["error"] = str(e)
        results["tests"].append(test10)
        print(f"  ✗ Error: {e}")

    # Save results
    print("\n" + "=" * 70)
    print("Saving detailed results to test_results.json...")
    with Path("test_results.json").open("w") as f:
        json.dump(results, f, indent=2)
    print("✓ Saved to test_results.json")

    # Generate summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    success_count = sum(1 for t in results["tests"] if t["status"] == "success")
    error_count = sum(1 for t in results["tests"] if t["status"] == "error")
    print(f"Total tests: {len(results['tests'])}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print()

    # Analyze fuzzy results
    print("FUZZY MATCHING ANALYSIS:")
    fuzzy_tests = [t for t in results["tests"] if "Fuzzy" in t["name"]]
    for test in fuzzy_tests:
        print(f"  {test['name']}: {test.get('results_count', 0)} results")
        if test.get("first_result"):
            print(f"    → Top result: {test['first_result'].get('name', 'Unknown')}")

    print("\nVECTOR/SEMANTIC SEARCH ANALYSIS:")
    vector_tests = [t for t in results["tests"] if "Vector" in t["name"]]
    for test in vector_tests:
        print(f"  {test['name']}: {test.get('results_count', 0)} results")
        if test.get("first_results"):
            print("    → Top 3 results:")
            for result in test["first_results"][:3]:
                print(f"       - {result.get('name', 'Unknown')}")

    print("\nOBJECT MODEL FILTERING ANALYSIS:")
    model_tests = [t for t in results["tests"] if "Object Model" in t["name"]]
    for test in model_tests:
        print(f"  {test['name']}: {test.get('results_count', 0)} results")

    # Write markdown report
    print("\nGenerating markdown report...")
    with Path("test_results.md").open("w") as f:
        f.write("# Open5e /v2/search/ Endpoint Test Results\n\n")
        f.write("**Date**: 2025-11-11\n")
        f.write(f"**Endpoint**: {BASE_URL}/search/\n")
        f.write(f"**Total Tests**: {len(results['tests'])}\n")
        f.write(f"**Successful**: {success_count}\n")
        f.write(f"**Errors**: {error_count}\n\n")

        f.write("## Test Details\n\n")
        for i, test in enumerate(results["tests"], 1):
            f.write(f"### Test {i}: {test['name']}\n\n")
            f.write(f"**Description**: {test['description']}\n\n")
            f.write("**Parameters**:\n```json\n")
            f.write(json.dumps(test["params"], indent=2))
            f.write("\n```\n\n")
            f.write(f"**Status**: {test['status'].upper()}\n\n")
            if test["status"] == "success":
                f.write(f"**Results Found**: {test.get('results_count', 0)}\n\n")
                if test.get("first_result"):
                    f.write("**Top Result**:\n```json\n")
                    f.write(json.dumps(test["first_result"], indent=2))
                    f.write("\n```\n\n")
                elif test.get("first_results"):
                    f.write("**Top 3 Results**:\n")
                    for j, result in enumerate(test["first_results"][:3], 1):
                        f.write(f"{j}. {result.get('name', 'Unknown')}\n")
                    f.write("\n")
            else:
                f.write(f"**Error**: {test.get('error', 'Unknown error')}\n\n")

        f.write("## Key Findings\n\n")
        f.write("### Fuzzy Matching\n")
        fuzzy_results = [
            t for t in results["tests"] if "Fuzzy" in t["name"] and t["status"] == "success"
        ]
        if fuzzy_results:
            f.write("✓ Fuzzy matching is supported\n")
            for test in fuzzy_results:
                f.write(f"- {test['params'].get('query')}: {test.get('results_count')} results\n")
        else:
            f.write("✗ Fuzzy matching tests failed\n")

        f.write("\n### Vector/Semantic Search\n")
        vector_results = [
            t for t in results["tests"] if "Vector" in t["name"] and t["status"] == "success"
        ]
        if vector_results:
            f.write("✓ Vector/semantic search is supported\n")
            for test in vector_results:
                f.write(f"- {test['params'].get('query')}: {test.get('results_count')} results\n")
        else:
            f.write("✗ Vector search tests failed\n")

        f.write("\n### Object Model Filtering\n")
        model_results = [
            t for t in results["tests"] if "Object Model" in t["name"] and t["status"] == "success"
        ]
        if model_results:
            f.write("✓ Object model filtering is supported\n")
            for test in model_results:
                f.write(
                    f"- {test['params'].get('object_model')}: {test.get('results_count')} results\n"
                )
        else:
            f.write("✗ Object model filtering tests failed\n")

    print("✓ Saved to test_results.md")

    print("\n" + "=" * 70)
    print("Test execution complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
