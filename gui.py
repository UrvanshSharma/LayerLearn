"""
LayerLearn GUI — Native Window Voice Agent
===========================================
Run:  python3 gui.py
Opens a native window (NOT a browser tab).
"""

from __future__ import annotations

import asyncio
import json
import threading
import traceback
import time

import webview  # pywebview — native OS window

from core.agent import Agent
from core.voice_controller import VoiceController
from core.logger import get_logger

log = get_logger(__name__)


# ── Shared state ─────────────────────────────────────────────────────────

agent: Agent | None = None
messages: list[dict] = []
status_state = {"text": "Starting…", "color": "#ffaa33"}
_window: webview.Window | None = None


def add_msg(role: str, text: str):
    messages.append({"role": role, "text": text, "ts": time.time()})
    # Push to UI
    if _window:
        safe = json.dumps(text)
        try:
            _window.evaluate_js(f'addMsg("{role}", {safe})')
        except Exception:
            pass


def set_status(text: str, color: str = "#7cffb2"):
    status_state["text"] = text
    status_state["color"] = color
    if _window:
        try:
            _window.evaluate_js(f'setStatus("{text}", "{color}")')
        except Exception:
            pass


# ── JS API exposed to the webview ────────────────────────────────────────

class Api:
    def send(self, text: str) -> str:
        if not text.strip() or agent is None:
            return json.dumps({"response": "Agent not ready."})

        if text.strip().lower() in {"reset", "clear"}:
            agent.reset()
            messages.clear()
            return json.dumps({"response": "__RESET__"})

        add_msg("user", text)
        set_status("Thinking…", "#ffaa33")

        try:
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(agent.process(text))
            loop.close()
        except Exception as e:
            response = f"Error: {e}"
            traceback.print_exc()

        add_msg("ai", response)
        set_status("Ready", "#7cffb2")

        # TTS in background
        threading.Thread(target=_speak_bg, args=(response,), daemon=True).start()

        return json.dumps({"response": response})


def _speak_bg(text: str):
    try:
        from core.tts import speak
        asyncio.run(speak(text))
    except Exception:
        pass


# ── HTML ─────────────────────────────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #0d0d0d; color: #e0e0e0;
    height: 100vh; display: flex; flex-direction: column; overflow: hidden;
  }
  .header {
    background: linear-gradient(135deg, #141414, #1a1a2e);
    border-bottom: 1px solid #2a2a2a;
    padding: 12px 20px; display: flex; align-items: center; justify-content: space-between;
    -webkit-app-region: drag;
  }
  .logo { font-size: 18px; font-weight: 700; color: #4ea1ff; }
  .status { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #7cffb2; -webkit-app-region: no-drag; }
  .status-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #7cffb2;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .voice-hint { color:#555; font-size:11px; background:#1a1a1a; padding:3px 8px; border-radius:10px; border:1px solid #2a2a2a; -webkit-app-region: no-drag; }

  .chat {
    flex:1; overflow-y:auto; padding:16px 20px;
    display:flex; flex-direction:column; gap:10px; scroll-behavior:smooth;
  }
  .chat::-webkit-scrollbar{width:5px}
  .chat::-webkit-scrollbar-thumb{background:#333;border-radius:3px}

  .msg {
    max-width:82%; padding:10px 14px; border-radius:14px;
    font-size:13px; line-height:1.55; white-space:pre-wrap;
    animation: fadeIn .25s ease;
  }
  @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
  .msg.user{align-self:flex-end;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border-bottom-right-radius:4px}
  .msg.ai{align-self:flex-start;background:#1a1a2e;border:1px solid #2a2a3e;border-bottom-left-radius:4px}
  .msg.system{align-self:center;background:transparent;color:#555;font-size:11px;padding:3px 10px}
  .msg.thinking{align-self:flex-start;background:#1a1a1a;border:1px solid #333;color:#ffaa33;font-size:12px}
  .msg.error{align-self:flex-start;background:#2a1515;border:1px solid #4a2020;color:#ff6b6b}
  .msg-label{font-size:10px;font-weight:600;margin-bottom:3px;opacity:.7}
  .msg.user .msg-label{color:#93c5fd} .msg.ai .msg-label{color:#7cffb2}

  .input-bar {
    padding:12px 20px; background:#111; border-top:1px solid #222;
    display:flex; gap:8px;
  }
  .input-bar input {
    flex:1; background:#1a1a1a; border:1px solid #2a2a2a; color:#fff;
    padding:12px 16px; border-radius:10px; font-size:13px;
    font-family:'Inter',sans-serif; outline:none; transition:border-color .2s;
  }
  .input-bar input:focus{border-color:#4ea1ff}
  .input-bar input::placeholder{color:#444}
  .input-bar button {
    background:linear-gradient(135deg,#4ea1ff,#2563eb); color:#fff; border:none;
    padding:12px 20px; border-radius:10px; font-size:13px; font-weight:600;
    cursor:pointer; font-family:'Inter',sans-serif; transition:transform .1s;
  }
  .input-bar button:hover{opacity:.9} .input-bar button:active{transform:scale(.97)}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🧠 LayerLearn</div>
  <div style="display:flex;align-items:center;gap:12px">
    <div class="voice-hint">🎤 Hold SHIFT to talk</div>
    <div class="status"><div class="status-dot" id="dot"></div><span id="stxt">Starting…</span></div>
  </div>
</div>
<div class="chat" id="chat"></div>
<div class="input-bar">
  <input id="inp" placeholder="Type a message…" autocomplete="off"/>
  <button onclick="send()">Send ⏎</button>
</div>
<script>
const chat=document.getElementById('chat'), inp=document.getElementById('inp');
inp.addEventListener('keydown',e=>{if(e.key==='Enter')send()});

function addMsg(role,text){
  const d=document.createElement('div');d.className='msg '+role;
  const labels={user:'You',ai:'🧠 LayerLearn',system:'System',thinking:'🧠',error:'Error'};
  if(role!=='system'){const l=document.createElement('div');l.className='msg-label';l.textContent=labels[role]||role;d.appendChild(l)}
  const c=document.createElement('div');c.textContent=text;d.appendChild(c);
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;
  return d;
}
function setStatus(t,c){document.getElementById('stxt').textContent=t;document.getElementById('dot').style.background=c}

let thinkEl=null;
function send(){
  const t=inp.value.trim();if(!t)return;inp.value='';
  if(t.toLowerCase()==='reset'||t.toLowerCase()==='clear'){
    pywebview.api.send(t);addMsg('system','Memory cleared ✓');return;
  }
  addMsg('user',t);
  thinkEl=addMsg('thinking','Thinking…');
  setStatus('Thinking…','#ffaa33');

  pywebview.api.send(t).then(r=>{
    if(thinkEl){thinkEl.remove();thinkEl=null}
    const d=JSON.parse(r);
    if(d.response!=='__RESET__') addMsg('ai',d.response);
    setStatus('Ready','#7cffb2');
  }).catch(e=>{
    if(thinkEl){thinkEl.remove();thinkEl=null}
    addMsg('error','Failed: '+e);setStatus('Error','#ff6b6b');
  });
}

addMsg('system','LayerLearn ready. Type or hold SHIFT to talk.');
setTimeout(()=>inp.focus(),100);
</script>
</body>
</html>
"""


# ── Voice thread ─────────────────────────────────────────────────────────

def start_voice_thread():
    async def voice_loop():
        async def on_transcript(text: str) -> str:
            add_msg("user", text)
            set_status("Thinking…", "#ffaa33")
            try:
                response = await agent.process(text)
            except Exception as e:
                response = f"Error: {e}"
                traceback.print_exc()
            add_msg("ai", response)
            set_status("Ready", "#7cffb2")
            return response

        vc = VoiceController(on_transcript=on_transcript)
        log.info("Voice controller started")
        await vc.run()

    try:
        asyncio.run(voice_loop())
    except Exception:
        traceback.print_exc()
        log.warning("Voice system stopped")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    global agent, _window

    print("\n  🧠 LayerLearn Voice Agent")
    print("  ─────────────────────────\n")

    print("  Loading Whisper model…")
    from core.stt import _get_model
    _get_model()

    print("  Initialising agent…")
    agent = Agent()

    print("  Starting voice system…")
    threading.Thread(target=start_voice_thread, daemon=True).start()

    print("  ✅ Ready!\n")

    api = Api()
    _window = webview.create_window(
        "LayerLearn Voice Agent",
        html=HTML,
        js_api=api,
        width=680,
        height=540,
        min_size=(450, 350),
        background_color="#0d0d0d",
    )

    # After window loads, update status
    def on_loaded():
        set_status("Ready", "#7cffb2")

    _window.events.loaded += on_loaded
    webview.start(debug=False)


if __name__ == "__main__":
    main()
