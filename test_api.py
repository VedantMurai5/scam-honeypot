#!/usr/bin/env python3
"""
Test script for the Scam Honeypot API
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5001"  # Change to your deployed URL when testing production
API_KEY = "my-super-secret-key-2026"  # Change to match your .env

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_scam_conversation():
    """Test a full scam conversation"""
    print("Testing scam detection and conversation...")
    
    session_id = f"test-session-{int(time.time())}"
    
    # Test messages simulating a scam conversation
    messages = [
        {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately."
        },
        {
            "sender": "scammer", 
            "text": "Share your UPI ID to avoid account suspension."
        },
        {
            "sender": "scammer",
            "text": "Please send payment to this account: 1234567890123456"
        },
        {
            "sender": "scammer",
            "text": "Use this link to verify: http://fake-bank-verify.com/login"
        },
        {
            "sender": "scammer",
            "text": "Contact us on +919876543210 if you have issues"
        }
    ]
    
    conversation_history = []
    
    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1} ---")
        print(f"Scammer: {msg['text']}")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": msg["sender"],
                "text": msg["text"],
                "timestamp": "2026-01-21T10:15:30Z"
            },
            "conversationHistory": conversation_history.copy(),
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/message",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Agent: {result.get('reply', 'No reply')}")
            if 'extracted_intelligence' in result:
                print(f"Intel So Far: {json.dumps(result['extracted_intelligence'], indent=2)}")
            
            # Add to conversation history
            conversation_history.append({
                "sender": msg["sender"],
                "text": msg["text"],
                "timestamp": "2026-01-21T10:15:30Z"
            })
            conversation_history.append({
                "sender": "user",
                "text": result.get('reply', ''),
                "timestamp": "2026-01-21T10:16:00Z"
            })
        else:
            print(f"Error: {response.text}")
            break
        
        time.sleep(1)  # Wait between messages
    
    # Check session details
    print(f"\n--- Session Details ---")
    response = requests.get(
        f"{BASE_URL}/api/session/{session_id}",
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code == 200:
        session_data = response.json()
        print(f"Scam Detected: {session_data.get('scam_detected')}")
        print(f"Confidence: {session_data.get('confidence', 0)*100:.1f}%")
        print(f"Total Messages: {len(session_data.get('messages', []))}")
        print(f"\nExtracted Intelligence:")
        intel = session_data.get('intelligence', {})
        for key, value in intel.items():
            if value:
                print(f"  {key}: {value}")
        print(f"\nAgent Notes: {session_data.get('agent_notes', 'None')}")
    else:
        print(f"Could not retrieve session: {response.status_code}")

def test_non_scam():
    """Test with a legitimate message"""
    print("\n\nTesting non-scam message...")
    
    payload = {
        "sessionId": f"test-legit-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": "Hello, how are you today?",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/message",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("=" * 60)
    print("Scam Honeypot API Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Scam conversation
        test_scam_conversation()
        
        # Test 3: Non-scam message
        test_non_scam()
        
        print("\n" + "=" * 60)
        print("Testing Complete!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server.")
        print("Make sure the server is running: python app.py")
    except Exception as e:
        print(f"ERROR: {e}")
