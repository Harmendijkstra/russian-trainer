#!/usr/bin/env python3
"""Lokale Russisch-trainer. Zet russisch_10000.tsv in dezelfde map.
Start: python russisch_trainer.py
Open: http://127.0.0.1:8000
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import csv, json, random, threading, webbrowser

HOST, PORT = '127.0.0.1', 8000
DATA = Path(__file__).with_name('russisch_10000.tsv')

def load_data():
    if not DATA.exists():
        raise FileNotFoundError(f'Zet {DATA.name} naast dit script.')
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    return rows

ROWS = load_data()
CATEGORIES = sorted({r['categorie'] for r in ROWS})
LIMITS = {'100 belangrijkste':100, '200 belangrijkste':200, '500 belangrijkste':500,
          '1000 belangrijkste':1000, 'Overig':10000, 'Alles':10000}

HTML = r'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Russisch trainer</title><style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#172033;background:#f5f7fb}*{box-sizing:border-box}body{margin:0}.wrap{max-width:820px;margin:auto;padding:18px}.card{background:#fff;border:1px solid #dce3ec;border-radius:20px;padding:22px;box-shadow:0 8px 24px #17203312;margin-bottom:14px}h1{text-align:center;margin:8px}.muted{color:#64748b;font-size:14px}.filters{display:grid;grid-template-columns:1fr 1fr auto;gap:10px}select,button,input{font:inherit;border:1px solid #cbd5e1;border-radius:11px;padding:12px;background:#fff}button{cursor:pointer;font-weight:650}button:hover{background:#eef4ff}.primary{width:100%;background:#2563eb;color:white;border-color:#2563eb;font-size:18px}.primary:hover{background:#1d4ed8}.ru{text-align:center;font-size:clamp(35px,8vw,58px);font-weight:700;padding:40px 4px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.two{grid-template-columns:1fr 1fr}.box{margin-top:12px;padding:15px;border-radius:13px}.green{background:#ecfdf5}.amber{background:#fffbeb}.hidden{display:none}.status{text-align:center;min-height:22px;margin:7px}.badge{display:inline-block;background:#e8eef8;border-radius:99px;padding:5px 9px;margin:3px;font-size:12px}.progress{height:7px;background:#e2e8f0;border-radius:9px;overflow:hidden;margin:12px 0}.progress i{display:block;height:100%;background:#2563eb}@media(max-width:650px){.filters,.grid,.two{grid-template-columns:1fr}.wrap{padding:10px}}
</style></head><body><main class="wrap"><h1>Russisch oefenen met geluid</h1><p class="muted" style="text-align:center">Kies eerst een leerlaag en categorie. Daarna luister je uitsluitend naar die selectie.</p>
<section class="card"><div class="filters"><select id="level"></select><select id="category"></select><button id="apply">Selectie laden</button></div><div style="margin-top:10px"><input id="search" style="width:100%" placeholder="Optioneel zoeken in Russisch of Nederlands"></div><p id="selection" class="muted"></p></section>
<div class="progress"><i id="bar"></i></div><section class="card"><div><span class="badge" id="levelBadge"></span><span class="badge" id="catBadge"></span><span class="muted" id="counter"></span></div><div class="ru" id="ru">Laden...</div><button class="primary" id="speak">🔊 Luister naar het Russisch</button><div id="status" class="status muted"></div><div class="grid two"><button id="showNl">Toon Nederlands</button><button id="showHelp">Toon uitleg</button></div><div id="nlBox" class="box green hidden"><b>Nederlands</b><div id="nl" style="font-size:21px;margin-top:5px"></div></div><div id="helpBox" class="box amber hidden"><b>Uitleg</b><div id="help" style="margin-top:5px"></div></div></section>
<div class="grid"><button id="prev">← Vorige</button><button id="shuffle">Willekeurig</button><button id="next" style="background:#172033;color:#fff">Volgende →</button></div>
<section class="card" style="margin-top:14px"><b>Bediening</b><p class="muted">Spatie = luisteren, pijltjes = vorige/volgende. De categorie en belangrijkheidslaag zijn twee afzonderlijke kolommen in het TSV-bestand.</p></section></main><script>
let items=[],i=0;const $=x=>document.getElementById(x);
async function meta(){const m=await fetch('/api/meta').then(r=>r.json());$('level').innerHTML=m.levels.map(x=>`<option>${x}</option>`).join('');$('category').innerHTML='<option>Alle categorieën</option>'+m.categories.map(x=>`<option>${x}</option>`).join('');}
function reset(){['nlBox','helpBox'].forEach(x=>$(x).classList.add('hidden'));$('showNl').textContent='Toon Nederlands';$('showHelp').textContent='Toon uitleg';$('status').textContent=''}
function render(){if(!items.length){$('ru').textContent='Geen resultaten';$('counter').textContent='';return}i=(i+items.length)%items.length;const x=items[i];$('ru').textContent=x.russisch;$('nl').textContent=x.nederlands;$('help').textContent=x.uitleg||'Luister enkele keren en spreek de zin hardop na.';$('levelBadge').textContent=x.belangrijkheidslaag;$('catBadge').textContent=x.categorie;$('counter').textContent=` ${i+1} / ${items.length}`;$('bar').style.width=((i+1)/items.length*100)+'%';reset()}
async function load(){const p=new URLSearchParams({level:$('level').value,category:$('category').value,q:$('search').value});$('selection').textContent='Selectie wordt geladen...';items=await fetch('/api/items?'+p).then(r=>r.json());i=0;$('selection').textContent=`${items.length} kaarten geladen uit de gekozen selectie.`;render()}
function speak(){if(!items.length)return;if(!('speechSynthesis'in window)){ $('status').textContent='Geen spraakondersteuning in deze browser.';return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(items[i].russisch);u.lang='ru-RU';u.rate=.72;const v=speechSynthesis.getVoices().find(v=>(v.lang||'').toLowerCase().startsWith('ru'));if(v)u.voice=v;u.onstart=()=>$('status').textContent='▶ Afspelen...';u.onend=()=>$('status').textContent=v?'✓ Russische stem gebruikt':'✓ Afgespeeld; geen aparte Russische stem gevonden';u.onerror=()=>$('status').textContent='Afspelen mislukt. Controleer de Russische Windows-stem.';speechSynthesis.speak(u)}
$('apply').onclick=load;$('speak').onclick=speak;$('next').onclick=()=>{i++;render()};$('prev').onclick=()=>{i--;render()};$('shuffle').onclick=()=>{i=Math.floor(Math.random()*items.length);render()};$('showNl').onclick=()=>{let h=$('nlBox').classList.toggle('hidden');$('showNl').textContent=h?'Toon Nederlands':'Verberg Nederlands'};$('showHelp').onclick=()=>{let h=$('helpBox').classList.toggle('hidden');$('showHelp').textContent=h?'Toon uitleg':'Verberg uitleg'};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.key==='ArrowRight')$('next').click();if(e.key==='ArrowLeft')$('prev').click();if(e.key===' '){e.preventDefault();speak()}});(async()=>{await meta();await load()})();
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def reply(self, body, ctype='application/json; charset=utf-8'):
        if not isinstance(body, (bytes, bytearray)): body=body.encode('utf-8')
        self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/': return self.reply(HTML,'text/html; charset=utf-8')
        if u.path=='/api/meta': return self.reply(json.dumps({'levels':list(LIMITS),'categories':CATEGORIES},ensure_ascii=False))
        if u.path=='/api/items':
            q=parse_qs(u.query); level=q.get('level',['100 belangrijkste'])[0]; cat=q.get('category',['Alle categorieën'])[0]; text=q.get('q',[''])[0].casefold().strip(); limit=LIMITS.get(level,100)
            data=ROWS[:limit]
            if cat!='Alle categorieën': data=[r for r in data if r['categorie']==cat]
            if text: data=[r for r in data if text in (r['russisch']+' '+r['nederlands']).casefold()]
            return self.reply(json.dumps(data,ensure_ascii=False))
        self.send_error(404)
    def log_message(self,*args): pass

if __name__=='__main__':
    print(f'Geladen: {len(ROWS)} kaarten uit {DATA.name}')
    print(f'Open http://{HOST}:{PORT} - stoppen met Ctrl+C')
    threading.Timer(.7,lambda:webbrowser.open(f'http://{HOST}:{PORT}')).start()
    try: ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt: print('\nGestopt.')
