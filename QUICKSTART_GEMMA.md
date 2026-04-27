# ⚡ LayerLearn + Gemma 4 — Quick Start

## In 60 Seconds ⏱️

### 1. Get API Key (1 min)
Visit: https://makersuite.google.com/app/apikey
- Click **"Create API Key"**
- Copy the key

### 2. Add to `.env` (30 sec)
```bash
cp .env.example .env
```

Edit `.env`, find:
```
GOOGLE_API_KEY=
```

Replace with:
```
GOOGLE_API_KEY=AIza...your...key...here
```

### 3. Run LayerLearn (30 sec)
```bash
python3 main.py --text
```

### 4. Test It! 🚀
Try these commands:

```
Text > what's on my screen
Text > write a python function to calculate fibonacci
Text > help me debug this error
Text > create a todo app in javascript
```

---

## What You Get

✨ **Instant Code Analysis**
```
"analyze my code" 
→ Gemma reads your screen + suggests fixes in seconds
```

✨ **Code Generation**
```
"write a function to sort a list"
→ Production-ready code instantly
```

✨ **Screen Understanding**
```
"what's on my screen"
→ Perfect text extraction & UI analysis
```

✨ **Website Building**
```
"create a landing page"
→ Full HTML/CSS/JS generated
```

---

## Example Session

```
🧠 LayerLearn Voice Agent 🧠

Text > what's on my screen
🤔 Thinking…

VS Code is open showing Python code.
The file "main.py" has a TypeError on line 15:
"'NoneType' object is not iterable"
You're trying to loop over a function result that returns None.

Text > fix it
Looking at the code...

Here's the fix - add a null check before the loop:

if result is None:
    result = []
for item in result:
    process(item)

This ensures result is always iterable.

Text > write a function to validate email addresses
Here's a robust email validation function:

import re

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Usage:
print(is_valid_email("user@example.com"))  # True
print(is_valid_email("invalid@"))          # False
```

---

## Commands That Work

### Screen & Vision
- "what's on my screen"
- "read what's visible"
- "analyze this code"
- "what's this error"
- "take a screenshot"

### Code Generation
- "write a function to..."
- "create a class for..."
- "generate a script that..."
- "write a regex for..."
- "fix this code"

### Websites
- "create a landing page"
- "generate a todo app"
- "build a portfolio website"
- "make a calculator"

### General Tasks
- "open chrome"
- "search for python tutorials"
- "create a file called script.py"
- "what time is it"

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `API key not found` | Make sure `.env` has `GOOGLE_API_KEY=your_key` |
| `API key invalid` | Get a new one from makersuite.google.com |
| `Rate limit exceeded` | Wait a few minutes (free tier: 60 req/min) |
| `Connection failed` | Falls back to Ollama automatically |
| Still getting errors | Check logs: `logs/layerlearn_*.log` |

---

## Switching Back to Ollama (Optional)

If you want to use Ollama instead:

Edit `.env`:
```
LLM_BACKEND=ollama
```

Make sure Ollama is running:
```bash
ollama serve
```

---

## Free Tier Limits

✅ **60 requests per minute** - More than enough!  
✅ **Unlimited usage** (within rate limits)  
✅ **No credit card required**

---

## API Key Safety

🔒 **Your key is private:**
- Never commit `.env` to Git
- `.env` is in `.gitignore`
- Keys are stored locally only
- Google doesn't track your queries

---

## Voice Mode (Optional)

Want voice instead of text?

```bash
python3 main.py
```

Then:
- **Hold SPACE** to talk
- **Release SPACE** to submit
- Get spoken response back

---

## Debug Mode

See what's happening under the hood:

```bash
python3 main.py --debug
```

Check logs:
```bash
tail -f logs/layerlearn_*.log
```

---

## Need Help?

- **Get API Key:** https://makersuite.google.com/app/apikey
- **Gemma Docs:** https://ai.google.dev/gemini-api/docs
- **LayerLearn Docs:** See `README.md`
- **Gemma Setup:** See `GEMMA_SETUP.md`

---

**You're all set! 🚀 Start asking LayerLearn to build things!**
