# 🚀 Gemma 4 Integration Setup Guide

LayerLearn now uses **Google's Gemini/Gemma API** for superior speed, accuracy, and code generation capabilities!

## What's New

✨ **Instant code analysis & generation**  
✨ **Real-time screen understanding**  
✨ **Build websites from voice commands**  
✨ **JARVIS-like automation**  
✨ **Falls back to Ollama if Gemma is unavailable**

---

## Quick Setup (2 Steps)

### Step 1: Get a FREE Google API Key

1. Go to **https://makersuite.google.com/app/apikey**
2. Click **"Create API Key"**
3. Copy the API key (looks like: `AIza...`)

### Step 2: Add API Key to `.env`

```bash
# Create .env from the example
cp .env.example .env

# Edit .env and add your API key:
nano .env
```

Find this section:
```env
GOOGLE_API_KEY=
```

Replace with:
```env
GOOGLE_API_KEY=your_api_key_here
```

**That's it!** LayerLearn will now use Gemma 4 automatically.

---

## Configuration

### Default Configuration
```env
LLM_BACKEND=gemma                    # Uses Gemma by default
GEMMA_MODEL=gemini-2.0-flash         # Latest, fastest model
LLM_TEMPERATURE=0.3                  # Low for precise responses
LLM_MAX_TOKENS=512                   # Fast inference
```

### Switch Back to Ollama (Optional)
If you want to use Ollama instead:

```env
LLM_BACKEND=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_TEXT_MODEL=llama3.2
OLLAMA_VISION_MODEL=llama3.2-vision
```

### Fine-Tuning Performance
```env
# For faster responses (less accurate)
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=256

# For better accuracy (slower)
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1024
```

---

## Gemma 4 Models Available

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `gemini-2.0-flash` | ⚡⚡⚡ Fastest | ✅ Excellent | **Recommended** |
| `gemini-1.5-flash` | ⚡⚡ Fast | ✅ Great | Good alternative |
| `gemini-1.5-pro` | ⚡ Standard | ⭐ Best | Complex tasks |

---

## What Gemma Can Do

### Code Analysis (Real-time from Screen)
```
"what's wrong with my code"
→ Gemma captures screen, analyzes code, suggests fixes
```

### Code Generation
```
"write a Python function to sort a list"
→ Instant, production-ready code
```

### Website Generation
```
"create a landing page for a coffee shop"
→ Gemma generates HTML/CSS/JS in seconds
```

### Screen Understanding
```
"what's on my screen"
→ Perfect text extraction and UI analysis
```

### Debugging
```
"help me debug this error"
→ Gemma reads the error, suggests solutions
```

---

## Troubleshooting

### ❌ "API key not found"
- Check `.env` file exists
- Verify `GOOGLE_API_KEY=` is filled (not empty)
- Restart LayerLearn after editing `.env`

### ❌ "API key invalid"
- Get a new key from **https://makersuite.google.com/app/apikey**
- Ensure no spaces in the key
- Check key hasn't been revoked

### ❌ "Rate limit exceeded"
- Free tier has limits (~60 requests/minute)
- Wait a few minutes or upgrade your API quota
- See: **https://console.cloud.google.com/billing**

### ❌ "Connection failed, using Ollama"
- Gemma API is down (rare) or network issue
- LayerLearn automatically falls back to Ollama
- Ensure Ollama is running: `ollama serve`

### ✅ "How do I know it's working?"
- Check logs: `logs/layerlearn_*.log`
- Look for: `✅ Gemma client initialized` or `📝 Gemma text:`
- Voice mode: Should respond faster than before

---

## API Quota & Pricing

### Free Tier
- ✅ **60 requests per minute** (plenty for voice assistant)
- ✅ Unlimited usage (within rate limits)
- ✅ No credit card needed

### Paid Tier (Optional)
- Upgrade at: **https://console.cloud.google.com/billing**
- Higher rate limits if needed
- Pay-as-you-go pricing

---

## Fallback to Ollama

If Gemma is unavailable, LayerLearn **automatically falls back to Ollama**:

1. Vision tasks → Tries Gemma → Falls back to Ollama
2. Text tasks → Tries Gemma → Falls back to Ollama

No manual action needed!

---

## Running LayerLearn

### Voice Mode
```bash
python3 main.py
```

### Text Mode
```bash
python3 main.py --text
```

### Debug Mode (See What's Happening)
```bash
python3 main.py --debug
```

---

## Example Commands

Now you can say:

- **"Analyze my code"** → Gemma reads screen & debugs
- **"Write a Python script to"** → Instant code generation
- **"Create a website for"** → HTML/CSS generation
- **"Help me with this error"** → Gemma fixes it
- **"What's on my screen"** → Perfect screen analysis
- **"Generate a function to"** → Production-ready code

---

## Need Help?

- **API Key Issues?** → https://makersuite.google.com/app/apikey
- **Rate Limits?** → https://console.cloud.google.com/billing
- **Gemma Docs?** → https://ai.google.dev/gemini-api/docs

---

**Happy coding with Gemma! 🚀**
