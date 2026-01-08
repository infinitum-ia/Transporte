"""
Test script for unified conversation endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8081/api/v1"

def test_unified_endpoint():
    """Test the unified conversation endpoint"""

    print("=" * 60)
    print("TESTING UNIFIED CONVERSATION ENDPOINT")
    print("=" * 60)
    print()

    # Test 1: Start outbound call
    print("TEST 1: Starting outbound call")
    print("-" * 60)

    payload1 = {
        "patient_phone": "3001234567",
        "message": "START",
        "is_outbound": True,
        "agent_name": "María"
    }

    print(f"Request: POST {BASE_URL}/conversation/unified")
    print(f"Body: {json.dumps(payload1, indent=2)}")
    print()

    try:
        response1 = requests.post(
            f"{BASE_URL}/conversation/unified",
            json=payload1,
            timeout=30
        )

        print(f"Status Code: {response1.status_code}")
        print(f"Response: {json.dumps(response1.json(), indent=2, ensure_ascii=False)}")
        print()

        if response1.status_code == 200:
            data1 = response1.json()
            session_id = data1.get("session_id")
            print(f"✓ SUCCESS - Session created: {session_id}")
            print(f"✓ Agent message: {data1.get('agent_response')[:100]}...")
            print()

            # Test 2: Continue conversation
            print("TEST 2: Continuing conversation")
            print("-" * 60)

            payload2 = {
                "patient_phone": "3001234567",
                "message": "Sí, con él habla",
                "is_outbound": True
            }

            print(f"Request: POST {BASE_URL}/conversation/unified")
            print(f"Body: {json.dumps(payload2, indent=2)}")
            print()

            response2 = requests.post(
                f"{BASE_URL}/conversation/unified",
                json=payload2,
                timeout=30
            )

            print(f"Status Code: {response2.status_code}")
            print(f"Response: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
            print()

            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✓ SUCCESS - Conversation continued")
                print(f"✓ Session ID: {data2.get('session_id')}")
                print(f"✓ Session created: {data2.get('session_created')} (should be False)")
                print(f"✓ Agent message: {data2.get('agent_response')[:100]}...")
                print()

                # Test 3: Accept legal notice
                print("TEST 3: Accepting legal notice")
                print("-" * 60)

                payload3 = {
                    "patient_phone": "3001234567",
                    "message": "Sí, acepto",
                    "is_outbound": True
                }

                print(f"Request: POST {BASE_URL}/conversation/unified")
                print(f"Body: {json.dumps(payload3, indent=2)}")
                print()

                response3 = requests.post(
                    f"{BASE_URL}/conversation/unified",
                    json=payload3,
                    timeout=30
                )

                print(f"Status Code: {response3.status_code}")
                print(f"Response: {json.dumps(response3.json(), indent=2, ensure_ascii=False)}")
                print()

                if response3.status_code == 200:
                    data3 = response3.json()
                    print(f"✓ SUCCESS - Legal notice accepted")
                    print(f"✓ Phase: {data3.get('conversation_phase')}")
                    print(f"✓ Agent message: {data3.get('agent_response')[:100]}...")
                    print()
            else:
                print(f"✗ FAILED - Test 2")
                print(f"Error: {response2.json()}")
        else:
            print(f"✗ FAILED - Test 1")
            print(f"Error: {response1.json()}")

    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to server")
        print("Make sure the server is running on http://localhost:8081")
        print()
        print("Start the server with:")
        print("  uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8081")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")

    print()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_unified_endpoint()
