from flask import Flask, request, jsonify
from datetime import datetime
import os
import json
import requests
from typing import Dict, List, Any
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
API_KEY = os.getenv('API_KEY', 'your-secret-api-key-change-this')
# Fallback to hardcoded key for hackathon deployment if env var is missing or empty
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    GEMINI_API_KEY = 'AIzaSyBRIzJ_SlPwH6Z5Vecrv5FmSqT9IVCxtWc'
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Session storage (in production, use Redis or a database)
sessions = {}

class IntelligenceExtractor:
    """Extract intelligence from conversation"""
    
    @staticmethod
    def extract_bank_accounts(text: str) -> List[str]:
        # Pattern for bank account numbers
        pattern = r'\b\d{9,18}\b'
        return list(set(re.findall(pattern, text)))
    
    @staticmethod
    def extract_upi_ids(text: str) -> List[str]:
        # Pattern for UPI IDs
        pattern = r'\b[\w\.-]+@[\w\.-]+\b'
        matches = re.findall(pattern, text)
        return [m for m in matches if any(provider in m.lower() for provider in ['paytm', 'phonepe', 'gpay', 'upi'])]
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        # Pattern for phone numbers
        patterns = [
            r'\+91[\s-]?\d{10}',
            r'\b\d{10}\b',
            r'\b\d{3}[\s-]\d{3}[\s-]\d{4}\b'
        ]
        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))
        return list(set(numbers))
    
    @staticmethod
    def extract_phishing_links(text: str) -> List[str]:
        # Pattern for URLs
        pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return list(set(re.findall(pattern, text)))
    
    @staticmethod
    def extract_suspicious_keywords(text: str) -> List[str]:
        keywords = [
            'urgent', 'verify', 'blocked', 'suspended', 'immediately',
            'account', 'bank', 'security', 'update', 'confirm',
            'click here', 'limited time', 'act now', 'expires',
            'verify now', 'confirm identity', 'unusual activity',
            'unauthorized', 'risk', 'fraud', 'alert'
        ]
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                found.append(keyword)
        return list(set(found))


class ScamDetector:
    """Detect scam intent from messages"""
    
    SCAM_INDICATORS = [
        'account blocked', 'verify immediately', 'urgent action',
        'suspended', 'upi', 'bank account', 'click here',
        'confirm your details', 'security alert', 'unusual activity',
        'verify your identity', 'account will be closed',
        'limited time', 'act now', 'prize', 'winner',
        'tax refund', 'government', 'claim now'
    ]
    
    @staticmethod
    def detect_scam(message: str) -> tuple[bool, float]:
        """
        Returns (is_scam, confidence_score)
        """
        message_lower = message.lower()
        score = 0
        matches = []
        
        # Check for scam indicators
        for indicator in ScamDetector.SCAM_INDICATORS:
            if indicator in message_lower:
                score += 1
                matches.append(indicator)
        
        # Additional heuristics
        if re.search(r'http[s]?://', message):
            score += 0.5
        
        if re.search(r'\d{10,}', message):  # Long numbers (accounts, etc)
            score += 0.5
        
        # Urgency words
        urgency_words = ['urgent', 'immediately', 'now', 'today', 'expires']
        for word in urgency_words:
            if word in message_lower:
                score += 0.3
        
        # Normalize score
        confidence = min(score / 3, 1.0)
        is_scam = confidence > 0.3
        
        return is_scam, confidence


class AIAgent:
    """AI Agent for engaging with scammers using Google Gemini"""
    
    def __init__(self, api_key: str):
        print(f"DEBUG: Gemini API Key loaded: {api_key[:20] if api_key else 'None'}...")
        # Use Gemini
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-flash-latest')
                self.use_ai = True
                print("DEBUG: Gemini model initialized successfully")
            except Exception as e:
                print(f"DEBUG: Error initializing Gemini: {e}")
                self.model = None
                self.use_ai = False
        else:
            self.model = None
            self.use_ai = False
    
    def generate_response(self, conversation_history: List[Dict], current_message: str, session_data: Dict) -> str:
        """Generate a believable human-like response"""
        
        print(f"DEBUG: generate_response called")
        print(f"DEBUG: Using AI = {self.use_ai}")
        
        if not self.use_ai:
            print("DEBUG: No API key - using fallback")
            return self._fallback_response(current_message, len(conversation_history))
        
        # Build context for Gemini
        system_prompt = """You are roleplaying as a potential scam victim to extract information from scammers.

Your objectives:
1. Act like a confused but cooperative person
2. Ask questions that make the scammer reveal more information
3. Never reveal you know it's a scam
4. Gradually show interest to keep them engaged
5. Ask for clarification on payment methods, account details, links
6. Express concern but willingness to comply
7. Keep responses natural, short (1-2 sentences usually)
8. Make occasional typos or informal language to seem human
9. Show urgency concern but ask questions that extract intel

IMPORTANT: Keep responses brief and natural. Don't be overly formal. Respond ONLY as the victim, nothing else."""

        # Format conversation for Gemini
        conversation_text = system_prompt + "\n\nConversation:\n"
        
        # Add history but limit to last 10 messages to avoid token limits
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        for msg in recent_history:
            sender = "Scammer" if msg["sender"] == "scammer" else "You"
            conversation_text += f"{sender}: {msg['text']}\n"
        
        # Add current message
        conversation_text += f"Scammer: {current_message}\nYou:"
        
        try:
            print("DEBUG: Calling Gemini API...")
            response = self.model.generate_content(conversation_text)
            reply = response.text.strip()
            
            # Clean up response (remove any labels)
            reply = reply.replace("You:", "").replace("Victim:", "").strip()
            
            print(f"DEBUG: Gemini responded: {reply[:50]}...")
            return reply
            
        except Exception as e:
            print(f"ERROR calling Gemini API: {e}")
            return self._fallback_response(current_message, len(conversation_history))
    
    def _fallback_response(self, message: str, turn_number: int) -> str:
        """Fallback responses when API is unavailable"""
        responses = [
            "Why is my account being suspended?",
            "What do I need to do?",
            "Can you explain more about this?",
            "How do I verify my account?",
            "What information do you need from me?",
            "Is this really from my bank?",
            "What happens if I don't do this?",
            "Can I call my bank instead?",
            "Where should I send the details?",
            "How long will this take?"
        ]
        
        if turn_number < len(responses):
            return responses[turn_number]
        return "I'm not sure I understand. Can you explain again?"


class SessionManager:
    """Manage conversation sessions"""
    
    @staticmethod
    def create_session(session_id: str) -> Dict:
        return {
            "session_id": session_id,
            "messages": [],
            "scam_detected": False,
            "confidence": 0.0,
            "intelligence": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            },
            "agent_notes": "",
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def update_intelligence(session: Dict, new_text: str):
        """Extract and update intelligence from new message"""
        intel = session["intelligence"]
        
        # Extract all types of intelligence
        intel["bankAccounts"].extend(IntelligenceExtractor.extract_bank_accounts(new_text))
        intel["upiIds"].extend(IntelligenceExtractor.extract_upi_ids(new_text))
        intel["phishingLinks"].extend(IntelligenceExtractor.extract_phishing_links(new_text))
        intel["phoneNumbers"].extend(IntelligenceExtractor.extract_phone_numbers(new_text))
        intel["suspiciousKeywords"].extend(IntelligenceExtractor.extract_suspicious_keywords(new_text))
        
        # Remove duplicates
        for key in intel:
            intel[key] = list(set(intel[key]))
    
    @staticmethod
    def should_end_session(session: Dict) -> bool:
        """Determine if we have enough intelligence to end the session"""
        intel = session["intelligence"]
        message_count = len(session["messages"])
        
        # End conditions
        has_significant_intel = (
            len(intel["bankAccounts"]) > 0 or
            len(intel["upiIds"]) > 0 or
            len(intel["phishingLinks"]) > 0 or
            len(intel["phoneNumbers"]) > 0
        )
        
        # End after 15 messages or if we have good intel after 5+ messages
        if message_count >= 15:
            return True
        
        if message_count >= 5 and has_significant_intel:
            return True
        
        return False


# Initialize AI Agent with Gemini
agent = AIAgent(GEMINI_API_KEY)


def send_final_result(session: Dict):
    """Send final results to GUVI callback endpoint"""
    payload = {
        "sessionId": session["session_id"],
        "scamDetected": session["scam_detected"],
        "totalMessagesExchanged": len(session["messages"]),
        "extractedIntelligence": session["intelligence"],
        "agentNotes": session["agent_notes"]
    }
    
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=5
        )
        print(f"Callback sent for session {session['session_id']}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending callback: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/api/message', methods=['POST'])
def handle_message():
    """Main endpoint for processing incoming messages"""
    
    # Verify API key
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        
        # Extract request data
        session_id = data.get('sessionId')
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        metadata = data.get('metadata', {})
        
        sender = message.get('sender')
        text = message.get('text')
        
        if not session_id or not text:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = SessionManager.create_session(session_id)
        
        session = sessions[session_id]
        
        # Add message to session
        session["messages"].append({
            "sender": sender,
            "text": text,
            "timestamp": message.get('timestamp', datetime.utcnow().isoformat())
        })
        
        # Detect scam on first message from scammer
        if sender == "scammer" and not session["scam_detected"]:
            is_scam, confidence = ScamDetector.detect_scam(text)
            session["scam_detected"] = is_scam
            session["confidence"] = confidence
            
            if is_scam:
                session["agent_notes"] = f"Scam detected with {confidence*100:.1f}% confidence. "
        
        # Extract intelligence from scammer message
        if sender == "scammer":
            SessionManager.update_intelligence(session, text)
        
        # Generate AI response if scam detected and sender is scammer
        if session["scam_detected"] and sender == "scammer":
            reply = agent.generate_response(conversation_history, text, session)
            
            # Add agent response to session
            session["messages"].append({
                "sender": "user",
                "text": reply,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check if we should end the session
            if SessionManager.should_end_session(session):
                # Enhance agent notes
                if "Session concluded" not in session["agent_notes"]:
                    session["agent_notes"] += f"Session concluded after {len(session['messages'])} messages. "
                    # Send final result to GUVI
                    send_final_result(session)
            
            return jsonify({
                "status": "success",
                "reply": reply,
                "scam_detected": session["scam_detected"],
                "confidence": session["confidence"],
                "extracted_intelligence": session["intelligence"]
            })
        
        # If not a scam or sender is user (shouldn't happen), return a neutral response
        return jsonify({
            "status": "success",
            "reply": "I see. Can you tell me more?"
        })
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions (for debugging)"""
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "sessions": list(sessions.keys()),
        "total": len(sessions)
    })


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get specific session details (for debugging)"""
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(sessions[session_id])


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)