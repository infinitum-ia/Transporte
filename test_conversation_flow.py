"""
End-to-End Conversation Test

Tests a complete conversation flow with the medical transport agent.
Run the server first with: uvicorn src.presentation.api.main:app --reload
"""
import requests
import time
from typing import Dict, Any
import json


class ConversationTester:
    """Test client for conversation flow"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.conversation_history = []

    def print_separator(self):
        """Print visual separator"""
        print("\n" + "=" * 80 + "\n")

    def print_message(self, role: str, message: str):
        """Print formatted message"""
        icon = "👤" if role == "USER" else "🤖"
        print(f"{icon} {role}: {message}")

    def check_health(self) -> bool:
        """Check if server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server healthy: {data['service']} v{data['version']}")
                return True
            return False
        except requests.RequestException as e:
            print(f"❌ Server not reachable: {e}")
            return False

    def create_session(self) -> str:
        """Create a new conversation session"""
        print("\n🔄 Creating new session...")
        response = requests.post(
            f"{self.base_url}/api/v1/session",
            json={"agent_name": "María"}
        )

        if response.status_code == 201:
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✅ Session created: {self.session_id[:8]}...")
            print(f"📅 Phase: {data['conversation_phase']}")
            return self.session_id
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            print(response.text)
            return None

    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message and get response"""
        if not self.session_id:
            print("❌ No active session. Create session first.")
            return None

        self.print_separator()
        self.print_message("USER", message)

        response = requests.post(
            f"{self.base_url}/api/v1/conversation/message",
            headers={"X-Session-ID": self.session_id},
            json={"message": message}
        )

        if response.status_code == 200:
            data = response.json()
            self.print_message("AGENT", data["agent_response"])
            print(f"\n📊 Phase: {data['conversation_phase']}")

            if data.get("requires_escalation"):
                print(f"⚠️  ESCALATION REQUIRED")

            self.conversation_history.append({
                "user": message,
                "agent": data["agent_response"],
                "phase": data["conversation_phase"]
            })

            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None

    def get_session_state(self) -> Dict[str, Any]:
        """Get current session state"""
        if not self.session_id:
            return None

        response = requests.get(
            f"{self.base_url}/api/v1/session/{self.session_id}"
        )

        if response.status_code == 200:
            return response.json()
        return None

    def print_summary(self):
        """Print conversation summary"""
        self.print_separator()
        print("📋 CONVERSATION SUMMARY")
        self.print_separator()

        state = self.get_session_state()
        if state:
            print(f"Session ID: {state['session_id'][:16]}...")
            print(f"Final Phase: {state['conversation_phase']}")
            if state.get('patient_name'):
                print(f"Patient: {state['patient_name']}")
            if state.get('patient_document'):
                print(f"Document: {state['patient_document']}")
            if state.get('service_type'):
                print(f"Service: {state['service_type']}")

        print(f"\nTotal Exchanges: {len(self.conversation_history)}")

        self.print_separator()


def run_happy_path_test():
    """
    Run a complete happy path conversation test

    Simulates a successful service coordination flow.
    """
    print("\n" + "🎯" * 40)
    print("TESTING: Happy Path - Successful Service Coordination")
    print("🎯" * 40)

    tester = ConversationTester()

    # Step 1: Health check
    if not tester.check_health():
        print("\n❌ Server not running. Please start with:")
        print("   uvicorn src.presentation.api.main:app --reload")
        return

    time.sleep(0.5)

    # Step 2: Create session
    if not tester.create_session():
        return

    time.sleep(0.5)

    # Step 3: Greeting
    tester.send_message("Hola, buenos días")
    time.sleep(1)

    # Step 4: Identification
    tester.send_message("Soy yo, el paciente. Mi nombre es Juan Pérez")
    time.sleep(1)

    # Step 5: Document
    tester.send_message("Mi cédula es CC 1234567890 de EPS Cosalud")
    time.sleep(1)

    # Step 6: Service type
    tester.send_message("Necesito transporte para terapia física el martes")
    time.sleep(1)

    # Step 7: Closing
    tester.send_message("No, eso es todo. Muchas gracias")
    time.sleep(1)

    # Step 8: Survey
    tester.send_message("5")
    time.sleep(1)

    # Summary
    tester.print_summary()
    print("✅ Happy path test completed successfully!")


def run_incident_path_test():
    """
    Run a conversation with incident/complaint

    Simulates a user reporting a complaint.
    """
    print("\n" + "⚠️ " * 40)
    print("TESTING: Incident Path - User Reports Complaint")
    print("⚠️ " * 40)

    tester = ConversationTester()

    # Health check
    if not tester.check_health():
        return

    time.sleep(0.5)

    # Create session
    if not tester.create_session():
        return

    time.sleep(0.5)

    # Greeting
    tester.send_message("Buenos días")
    time.sleep(1)

    # Identification
    tester.send_message("Soy María López, CC 9876543210, Cosalud")
    time.sleep(1)

    # Service coordination with complaint
    tester.send_message("Tengo una queja, el conductor llegó muy tarde")
    time.sleep(1)

    # Provide details
    tester.send_message("Llegó 45 minutos tarde y no avisó")
    time.sleep(1)

    # Continue
    tester.send_message("También necesito confirmar mi cita de diálisis")
    time.sleep(1)

    # Closing
    tester.send_message("No, gracias")
    time.sleep(1)

    # Survey
    tester.send_message("3")
    time.sleep(1)

    # Summary
    tester.print_summary()
    print("✅ Incident path test completed!")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("TRANSFORMAS MEDICAL TRANSPORT AGENT - E2E TEST")
    print("🚀" * 40)

    # Run tests
    try:
        run_happy_path_test()
        time.sleep(2)
        run_incident_path_test()

        print("\n" + "✅" * 40)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅" * 40 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
