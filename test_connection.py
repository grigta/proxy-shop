#!/usr/bin/env python3
"""Test connection from bot to backend."""
import asyncio
import httpx

async def test_connection():
    """Test backend connection."""
    backend_url = "http://backend:8000"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            print(f"Testing {backend_url}/health...")
            response = await client.get(f"{backend_url}/health")
            print(f"✅ Health check: {response.status_code}")
            print(f"   Response: {response.json()}")

            # Test products endpoint (no auth required)
            print(f"\nTesting {backend_url}/api/products/socks5/countries...")
            response = await client.get(f"{backend_url}/api/products/socks5/countries")
            print(f"✅ Countries endpoint: {response.status_code}")
            if response.status_code == 200:
                countries = response.json()
                print(f"   Countries: {countries}")
            else:
                print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
