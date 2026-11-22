"""Professional browser dashboard for NeuralNotes."""
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from study_pack import ENGINE_NAME, generate, markdown, preview, source_lines

HOST = "127.0.0.1"
PORT = 5050
ROOT = Path(__file__).resolve().parent

HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NeuralNotes — Study Workspace</title>
  <style>
    :root{--nav:#111827;--canvas:#f4f6fb;--card:#fff;--line:#e4e9f2;--ink:#172033;--muted:#718096;--violet:#5b4cf0;--violet-dark:#4338ca;--green:#15806d}
    *{box-sizing:border-box} body{margin:0;font-family:Inter,"Segoe UI",sans-serif;background:var(--canvas);color:var(--ink)}
    .app{display:grid;grid-template-columns:232px minmax(0,1fr);min-height:100vh}.sidebar{background:var(--nav);color:#fff;padding:24px 16px;display:flex;flex-direction:column}
    .brand{display:flex;align-items:center;gap:11px;padding:0 8px 28px}.logo{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:linear-gradient(135deg,#7c6df7,#5144df);font-weight:800}
    .brand strong{font-size:17px}.eyebrow{font-size:10px;font-weight:800;letter-spacing:.12em;color:#8e9baa;padding:16px 12px 8px}.nav a{display:flex;align-items:center;gap:10px;color:#aeb9c7;text-decoration:none;padding:11px 12px;border-radius:8px;font-size:13px;margin:3px 0}
    .nav a.active{background:#202e43;color:#fff}.nav a:hover{background:#1c293b}.engine{margin-top:auto;background:#1c2940;border:1px solid #293955;border-radius:12px;padding:14px}.engine-row{display:flex;align-items:center;gap:8px}.dot{width:8px;height:8px;border-radius:50%;background:#7d8898}.dot.online{background:#32c59d}.engine small{color:#98a6b8}.engine strong{display:block;margin:7px 0 3px;font-size:13px}
    main{min-width:0;padding:22px 28px 28px}.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.topbar h1{margin:0;font-size:24px}.status{border-radius:999px;background:#e7edf6;color:#64748b;font-size:11px;font-weight:700;padding:8px 12px}.status.error{background:#fde8e8;color:#b42318}.status.success{background:#def4ed;color:#0b735f}
    .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}.metric{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.metric span{display:block;color:var(--muted);font-size:9px;font-weight:800;letter-spacing:.08em}.metric strong{display:block;font-size:20px;margin-top:5px}
    .pipeline{display:flex;align-items:center;gap:8px;margin-bottom:12px}.pipeline-label{font-size:9px;font-weight:800;letter-spacing:.08em;color:var(--muted);margin-right:5px}.step{font-size:11px;font-weight:700;color:#7b8798;background:#e8edf4;border-radius:6px;padding:7px 10px}.step.active{color:var(--violet);background:#e8e6ff}.step.done{color:var(--green);background:#daf3eb}
    .workspace{display:grid;grid-template-columns:minmax(300px,.9fr) minmax(360px,1.1fr);gap:16px;height:calc(100vh - 260px);min-height:480px}.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;min-height:0}.panel-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}.panel h2{font-size:14px;margin:0}.tabs{display:flex;gap:3px}.tab{border:0;background:transparent;color:var(--muted);border-radius:7px;padding:7px 8px;font-size:10px;font-weight:800;cursor:pointer}.tab.active{background:#eceaff;color:#5144ce}
    textarea{resize:none;width:100%;flex:1;border:1px solid var(--line);border-radius:10px;background:#f8fafc;color:#26364e;padding:14px;font:12px/1.7 "Segoe UI",sans-serif;outline:none}.content{overflow:auto;flex:1;border:1px solid var(--line);border-radius:10px;background:#f8fafc;padding:14px;font-size:12px;line-height:1.65}.content h3{margin:0 0 8px}.content ul,.content ol{padding-left:19px}.content li{margin:7px 0}.empty{height:100%;display:grid;place-items:center;text-align:center;color:#8793a5}.empty span{display:block;font-size:30px;margin-bottom:8px}
    .controls{display:flex;align-items:center;gap:8px;padding-top:11px}.controls select{height:36px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);padding:0 9px;font-size:11px}.spacer{flex:1}.btn{border:0;border-radius:8px;height:36px;padding:0 13px;font-size:11px;font-weight:800;cursor:pointer}.btn.secondary{background:#fff;border:1px solid var(--line);color:var(--ink)}.btn.primary{background:var(--violet);color:#fff}.btn.primary:hover{background:var(--violet-dark)}.btn:disabled{opacity:.55;cursor:not-allowed}.answer{height:28px;display:flex;align-items:center;font-size:10px;color:var(--muted)}
    @media(max-width:900px){.app{grid-template-columns:1fr}.sidebar{display:none}main{padding:16px}.workspace{grid-template-columns:1fr;height:auto}.panel{min-height:420px}.metrics{grid-template-columns:repeat(2,1fr)}}
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand"><div class="logo">NN</div><strong>NeuralNotes</strong></div>
    <div class="eyebrow">WORKSPACE</div>
    <nav class="nav"><a class="active" href="#">⌘ &nbsp; Study workspace</a><a href="#sources" onclick="setTab('Sources')">▱ &nbsp; Sources</a><a href="#" onclick="exportMarkdown()">↓ &nbsp; Export study pack</a></nav>
    <div class="engine"><div class="engine-row"><div class="dot" id="engineDot"></div><small id="engineLabel">Checking Gemini</small></div><strong id="engineModel"></strong><small id="engineModelLabel">Google Gemini API</small></div>
  </aside>
  <main>
    <div class="topbar"><h1>Study workspace</h1><div class="status" id="status">Ready</div></div>
    <div class="metrics">
      <div class="metric"><span>WORDS</span><strong id="words">0</strong></div><div class="metric"><span>SOURCE LINES</span><strong id="lines">0</strong></div><div class="metric"><span>KEY TERMS</span><strong id="terms">0</strong></div><div class="metric"><span>QUESTIONS</span><strong id="questions">0</strong></div>
    </div>
    <div class="pipeline"><div class="pipeline-label">PIPELINE</div><div class="step" id="evidence">○ Evidence</div><div class="step" id="draft">○ Draft</div><div class="step" id="review">○ Review</div></div>
    <div class="workspace">
      <section class="panel"><div class="panel-head"><h2>1 &nbsp; Lecture notes</h2></div><textarea id="notes" placeholder="Paste lecture notes here…"></textarea><div class="controls"><button class="btn secondary" onclick="loadExample()">Load example</button><button class="btn secondary" onclick="openText()">Open TXT</button><div class="spacer"></div><select id="mode"><option>AI · v3 chain</option><option>Offline preview</option></select><button class="btn primary" id="generate" onclick="generatePack()">Generate pack</button></div></section>
      <section class="panel"><div class="panel-head"><h2>2 &nbsp; Study pack</h2><div class="tabs" id="tabs"></div></div><label class="answer"><input type="checkbox" id="showAnswers" checked onchange="render()"> Show answers</label><div class="content" id="content"><div class="empty"><div><span>✦</span>Generate a pack to begin</div></div></div><div class="controls"><div class="spacer"></div><button class="btn secondary" id="export" onclick="exportMarkdown()" disabled>Export Markdown</button></div></section>
    </div>
  </main>
</div>
<input type="file" id="fileInput" accept=".txt,text/plain" hidden>
<script>
const sample=`A stack is a last-in, first-out data structure.\nA queue is a first-in, first-out data structure.\nPush means adding an item to the top of a stack.\nPop means removing the top item from a stack.\nEnqueue means adding an item to the back of a queue.`;
let pack=null,lines={},tab="Full pack";
const tabs=["Full pack","Summary","Key terms","Questions","Sources"];
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}
function setStatus(text,type=""){const el=document.getElementById("status");el.textContent=text;el.className="status "+type}
function setPipeline(active=null,done=false){["evidence","draft","review"].forEach((id,i)=>{const el=document.getElementById(id),name=["Evidence","Draft","Review"][i];el.className="step"+(done?" done":(active===name?" active":""));el.textContent=(done?"●":(active===name?"◉":"○"))+" "+name})}
function updateMetrics(){const text=document.getElementById("notes").value;document.getElementById("words").textContent=text.trim()?text.trim().split(/\\s+/).length:0;fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({notes:text})}).then(r=>r.json()).then(d=>{document.getElementById("lines").textContent=d.lines||0}).catch(()=>{})}
async function engineStatus(){try{const d=await (await fetch("/api/status")).json();document.getElementById("engineDot").className="dot"+(d.configured?" online":"");document.getElementById("engineLabel").textContent=d.configured?"API key configured":"API key missing";document.getElementById("engineModel").textContent=d.model}catch(e){document.getElementById("engineLabel").textContent="Engine unavailable"}}
function loadExample(){document.getElementById("notes").value=sample;updateMetrics()}
function openText(){document.getElementById("fileInput").click()}
document.getElementById("fileInput").onchange=e=>{const f=e.target.files[0];if(f){const r=new FileReader;r.onload=()=>{document.getElementById("notes").value=r.result;updateMetrics()};r.readAsText(f)}}
document.getElementById("notes").addEventListener("input",updateMetrics);
function buildTabs(){const el=document.getElementById("tabs");el.innerHTML=tabs.map(t=>`<button class="tab ${t===tab?"active":""}" onclick="setTab('${t}')">${t}</button>`).join("")}
function setTab(t){tab=t;buildTabs();render()}
function render(){if(!pack){return}const show=document.getElementById("showAnswers").checked;let h="";
if(tab==="Full pack"||tab==="Summary"){h+="<h3>Summary</h3><ul>"+(pack.summary||[]).map(r=>`<li>${esc(r.text)} <small>[${esc(r.refs.join(", "))}]</small></li>`).join("")+"</ul>"}
if(tab==="Full pack"||tab==="Key terms"){h+="<h3>Key terms</h3><ul>"+(pack.terms||[]).map(r=>`<li><strong>${esc(r.term)}</strong> — ${esc(r.definition)} <small>[${esc(r.refs.join(", "))}]</small></li>`).join("")+"</ul>"}
if(tab==="Full pack"||tab==="Questions"){h+="<h3>Practice questions</h3><ol>"+(pack.questions||[]).map(r=>`<li>${esc(r.question)} <small>[${esc(r.refs.join(", "))}]</small>${show?`<br><strong>Answer:</strong> ${esc(r.answer)}`:""}</li>`).join("")+"</ol>"}
if(tab==="Full pack"||tab==="Sources"){h+="<h3>Source lines</h3><ul>"+Object.entries(lines).map(([ref,line])=>`<li><strong>[${esc(ref)}]</strong> ${esc(line)}</li>`).join("")+"</ul>"}
if(pack.warnings&&pack.warnings.length){h+="<h3>Review notes</h3><ul>"+pack.warnings.map(w=>`<li>${esc(w)}</li>`).join("")+"</ul>"}
document.getElementById("content").innerHTML=h}
async function generatePack(){const notes=document.getElementById("notes").value,mode=document.getElementById("mode").value,btn=document.getElementById("generate");btn.disabled=true;pack=null;document.getElementById("export").disabled=true;setPipeline("Evidence");setStatus("Processing notes…");try{const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({notes,mode})});const d=await r.json();if(!r.ok)throw new Error(d.error||"Generation failed");pack=d.pack;lines=d.lines;document.getElementById("terms").textContent=pack.terms.length;document.getElementById("questions").textContent=pack.questions.length;document.getElementById("export").disabled=false;setPipeline(null,true);setStatus(d.label+(d.label.includes("AI")?" · local model":"")+" · "+pack.questions.length+" questions","success");render()}catch(e){setStatus(e.message,"error");setPipeline();document.getElementById("content").innerHTML=`<div class="empty"><div><span>!</span>${esc(e.message)}</div></div>`}finally{btn.disabled=false}}
function exportMarkdown(){if(!pack){setStatus("Generate a study pack before exporting.","error");return}fetch("/api/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pack,lines,showAnswers:document.getElementById("showAnswers").checked})}).then(r=>r.json()).then(d=>{if(d.error)throw new Error(d.error);const blob=new Blob([d.markdown],{type:"text/markdown"}),a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=d.filename||"neuralnotes-study-pack.md";a.click();URL.revokeObjectURL(a.href);setStatus("Study pack exported","success")}).catch(e=>setStatus(e.message,"error"))}
buildTabs();updateMetrics();engineStatus();
</script>
</body></html>"""


class NeuralNotesHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if unquote(self.path) == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if unquote(self.path) == "/api/status":
            self.send_json(200, {
                "configured": bool(os.getenv("GOOGLE_API_KEY", "").strip()),
                "model": ENGINE_NAME,
            })
            return
        self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON request"})
            return

        if unquote(self.path) == "/api/analyze":
            try:
                lines = source_lines(data.get("notes", ""))
            except ValueError:
                lines = {}
            self.send_json(200, {"lines": len(lines)})
            return

        if unquote(self.path) == "/api/generate":
            try:
                notes = data["notes"]
                offline = data.get("mode") == "Offline preview"
                lines = source_lines(notes)
                pack = preview(notes) if offline else generate(notes)
                label = "Offline preview" if offline else f"AI study pack · {ENGINE_NAME}"
                self.send_json(200, {"pack": pack, "lines": lines, "label": label})
            except (KeyError, ValueError, OSError, TypeError) as error:
                self.send_json(400, {"error": str(error)})
            return

        if unquote(self.path) == "/api/export":
            pack = data["pack"]
            lines = data["lines"]
            show_answers = data.get("showAnswers", True)
            document = markdown(pack, show_answers) + "\n## Source lines\n\n" + "\n".join(
                f"- [{ref}] {line}" for ref, line in lines.items()) + "\n"
            self.send_json(200, {"markdown": document, "filename": "neuralnotes-study-pack.md"})
            return

        self.send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), NeuralNotesHandler)
    print(f"NeuralNotes is running at http://{HOST}:{PORT}")
    webbrowser.open(f"http://{HOST}:{PORT}")
    server.serve_forever()
