# AI-Powered Scam Honeypot System 🍯

An intelligent honeypot system that detects scam messages, engages scammers autonomously, and extracts actionable intelligence.

## 🌟 Features

- **Scam Detection**: Automatically identifies fraudulent messages using pattern matching and heuristics
- **AI Agent**: Uses Claude AI to engage scammers with human-like responses
- **Intelligence Extraction**: Automatically extracts:
  - Bank account numbers
  - UPI IDs
  - Phishing links
  - Phone numbers
  - Suspicious keywords
- **Multi-turn Conversations**: Handles extended conversations to extract maximum intel
- **API-First Design**: RESTful API with authentication
- **Automatic Reporting**: Sends final results to GUVI evaluation endpoint

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key (get from https://console.anthropic.com)

### Local Setup

1. **Clone/Download the files**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `API_KEY`: Your custom API key for authentication (change from default!)

4. **Run the server**
```bash
python app.py
```

The server will start on `http://localhost:5000`

### Testing Locally

```bash
curl -X POST http://localhost:5000/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-api-key-change-this" \
  -d '{
    "sessionId": "test-session-123",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": "2026-01-21T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

## 🌐 Deployment Options

### Option 1: Railway.app (Recommended - Free Tier Available)

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `API_KEY`
   - `PORT` (Railway auto-sets this)
6. Railway will auto-detect Python and deploy!

Your API will be available at: `https://your-app.railway.app`

### Option 2: Render.com (Free Tier)

1. Go to [render.com](https://render.com)
2. Sign up and click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Add environment variables in the dashboard
6. Deploy!

Your API will be available at: `https://your-app.onrender.com`

### Option 3: Heroku

1. Install Heroku CLI
2. Create a `Procfile`:
```
web: gunicorn app:app
```
3. Deploy:
```bash
heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=your-key
heroku config:set API_KEY=your-api-key
git push heroku main
```

## 📡 API Endpoints

### POST /api/message
Main endpoint for processing scam messages.

**Headers:**
- `x-api-key`: Your authentication key
- `Content-Type`: application/json

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Message content",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "AI-generated response"
}
```

### GET /health
Health check endpoint.

### GET /api/sessions
Get all active sessions (debugging).

### GET /api/session/{sessionId}
Get specific session details (debugging).

## 🔐 Security

- API key authentication required for all endpoints
- Environment variables for sensitive data
- No data persistence (uses in-memory storage)
- Rate limiting recommended for production

## 🧪 How It Works

1. **Receive Message**: Platform sends suspected scam message
2. **Scam Detection**: System analyzes message for scam indicators
3. **Agent Activation**: If scam detected, AI agent takes over
4. **Engagement**: Agent responds naturally to extract information
5. **Intelligence Extraction**: System extracts account numbers, links, etc.
6. **Session Management**: Continues conversation until enough intel gathered
7. **Final Report**: Sends results to GUVI evaluation endpoint

## 📊 Evaluation Criteria

- ✅ Scam detection accuracy
- ✅ Quality of AI engagement (natural responses)
- ✅ Intelligence extraction effectiveness
- ✅ API stability and response time
- ✅ Ethical behavior (no impersonation of real people)

## 🔧 Configuration

### Scam Detection Tuning

Edit `ScamDetector.SCAM_INDICATORS` in `app.py` to add more patterns.

### AI Agent Behavior

Modify the `system_prompt` in `AIAgent.generate_response()` to adjust agent personality.

### Session Ending Conditions

Adjust in `SessionManager.should_end_session()`:
- Maximum messages
- Minimum intel required
- Time limits

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `API_KEY` | Your API authentication key | Yes |
| `PORT` | Server port (default: 5000) | No |

## 🐛 Troubleshooting

**Issue**: "Unauthorized" error
- **Solution**: Check your `x-api-key` header matches `API_KEY` in `.env`

**Issue**: No AI responses
- **Solution**: Verify `ANTHROPIC_API_KEY` is set correctly

**Issue**: Callback not working
- **Solution**: Check GUVI endpoint URL is correct

## 📞 Support

For issues or questions:
1. Check the logs
2. Test with `/health` endpoint
3. Verify environment variables
4. Check API key validity

## 📄 License

MIT License - feel free to use for the hackathon!

## 🏆 Hackathon Submission Checklist

- [ ] API deployed and publicly accessible
- [ ] Environment variables configured
- [ ] API key authentication working
- [ ] Scam detection functional
- [ ] AI agent responding naturally
- [ ] Intelligence extraction working
- [ ] Final callback to GUVI endpoint implemented
- [ ] Tested with sample scam messages
- [ ] Documented API endpoint URL
- [ ] API key shared with evaluators

Good luck! 🚀
