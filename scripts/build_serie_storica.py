#!/usr/bin/env python3
"""Genera i dati della serie storica pensioni 1998-2026 per sede INPS dal cubo 3."""
import json
from collections import defaultdict
from rdflib import Graph
BASE = "https://robertobrunocl.github.io/idpt-italia/"

def extract():
    g = Graph(); g.parse("output/observations/cubo3_serie_storica_sede.ttl", format="turtle")
    def pull(measure, prop):
        q = """PREFIX qb:<http://purl.org/linked-data/cube#> PREFIX idpt:<%(b)s>
        SELECT ?sede ?anno ?v WHERE { ?o qb:measureType idpt:%(m)s ;
          idpt:sedeINPS ?sede ; idpt:annoRiferimento ?anno ; idpt:%(p)s ?v . }""" % {"b":BASE,"m":measure,"p":prop}
        d = defaultdict(dict)
        for sede, anno, v in g.query(q):
            slug = str(sede).rsplit("/",1)[-1].replace("sede-inps-","")
            d[slug][int(str(anno))] = float(v)
        return d
    num = pull("numeroPensioni","numeroPensioni")
    med = pull("importoMedioMensile","importoMedioMensile")

    gm = Graph(); gm.parse("output/mappings/inps_to_agid.ttl", format="turtle")
    label={}; provof={}
    for sede, lab in gm.query("""PREFIX skos:<http://www.w3.org/2004/02/skos/core#> PREFIX idpt:<%(b)s>
        SELECT ?sede ?lab WHERE { ?sede a idpt:SedeINPS ; skos:prefLabel ?lab . }"""%{"b":BASE}):
        label[str(sede).rsplit("/",1)[-1].replace("sede-inps-","")] = str(lab).title()
    for sede, prov in gm.query("""PREFIX idpt:<%(b)s>
        SELECT ?sede ?prov WHERE { ?sede idpt:correspondsToProvinceAGID ?prov . }"""%{"b":BASE}):
        provof[str(sede).rsplit("/",1)[-1].replace("sede-inps-","")] = str(prov).rsplit("/",1)[-1]

    gp = Graph(); gp.parse("data/provinces.ttl", format="turtle")
    nuts=defaultdict(list)
    for p,n in gp.query("""SELECT ?p ?n WHERE{?p <http://www.w3.org/2002/07/owl#sameAs> ?n.
        FILTER(STRSTARTS(STR(?n),'http://nuts.geovocab.org/id/'))}"""):
        c=str(p).rsplit("/",1)[-1]; s=str(n).rsplit("/",1)[-1]
        if c.isdigit() and len(s)>=3 and s[2].isalpha(): nuts[c].append(s)
    MAC={'C':'Nord-Ovest','D':'Nord-Est','H':'Nord-Est','E':'Centro','I':'Centro','F':'Sud','G':'Isole'}
    # province 2009 senza NUTS Eurostat (placeholder degenere in AGID): macroarea a mano
    MACRO_OVERRIDE={'barletta-andria-trani':'Sud','fermo':'Centro','monza-e-della-brianza':'Nord-Ovest'}
    LABEL_FIX={'barletta-andria-trani':'Barletta-Andria-Trani','monza-e-della-brianza':'Monza e della Brianza',
               'cagliari-e-sud-sardegna':'Cagliari e Sud Sardegna'}
    def macro(slug):
        if slug in MACRO_OVERRIDE: return MACRO_OVERRIDE[slug]
        for s in nuts.get(provof.get(slug,""),[]):
            if s[2] in MAC: return MAC[s[2]]
        return 'Isole' if slug in ('cagliari-e-sud-sardegna',) else 'Altro'

    years=list(range(1998,2027))
    series=[]
    for slug in sorted(num, key=lambda s: label.get(s,s)):
        series.append({"label":LABEL_FIX.get(slug,label.get(slug,slug.title())),"macro":macro(slug),
            "num":[int(num[slug][y]) if y in num[slug] else None for y in years],
            "med":[round(med.get(slug,{}).get(y),1) if y in med.get(slug,{}) else None for y in years]})
    tot=[sum(s["num"][i] for s in series if s["num"][i] is not None) for i in range(len(years))]
    return {"years":years,"series":series,"totale":tot}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Serie storica pensioni 1998-2026 - IDPT</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root{--primary:#4a5d8a;--primary-light:#6e7fb8;--primary-bg:#f5f7fb;--text:#222;--text-light:#555;--border:#e0e0e0}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--text);background:#fff;font-size:14px;line-height:1.5}
  .wrap{max-width:900px;margin:0 auto;padding:18px 16px 28px}
  h1{font-size:19px;color:var(--primary);margin:0 0 2px}
  .sub{color:var(--text-light);font-size:12.5px;margin:0 0 14px}
  .controls{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin-bottom:12px}
  .grp{display:flex;align-items:center;gap:6px}
  .grp>span.lbl{font-size:11.5px;color:var(--text-light);text-transform:uppercase;letter-spacing:.04em}
  button.opt,button.preset{font:inherit;font-size:12.5px;border:1px solid var(--border);background:#fff;color:var(--text);
    padding:5px 10px;border-radius:6px;cursor:pointer;transition:all .12s}
  button.opt:hover,button.preset:hover{border-color:var(--primary-light);background:var(--primary-bg)}
  button.opt.active{background:var(--primary);color:#fff;border-color:var(--primary)}
  button.preset{border-style:dashed}
  input#picker{font:inherit;font-size:12.5px;padding:5px 8px;border:1px solid var(--border);border-radius:6px;min-width:180px}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px;min-height:4px}
  .chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:3px 6px 3px 9px;border-radius:12px;
    background:var(--primary-bg);border:1px solid var(--border)}
  .chip b{width:9px;height:9px;border-radius:50%;display:inline-block}
  .chip span.x{cursor:pointer;color:var(--text-light);font-weight:700;padding:0 2px}
  .chip span.x:hover{color:#b5524a}
  .chartbox{position:relative;height:430px}
  .cap{font-size:12px;color:var(--text-light);margin-top:12px;border-top:1px solid var(--border);padding-top:10px}
  .cap b{color:var(--text)}
</style></head><body>
<div class="wrap">
  <h1>Serie storica delle pensioni vigenti, 1998-2026</h1>
  <p class="sub">Numero di pensioni (o importo medio mensile) per sede INPS. Dati dal cubo 3 del grafo RDF del progetto (serie storica, 106 sedi x 29 anni). Le linee verticali segnano le due discontinuita strutturali del territorio.</p>
  <div class="controls">
    <div class="grp"><span class="lbl">Misura</span>
      <button class="opt active" data-m="num">Numero pensioni</button>
      <button class="opt" data-m="med">Importo medio (EUR/mese)</button>
    </div>
    <div class="grp"><span class="lbl">Aggiungi</span>
      <input id="picker" list="provlist" placeholder="cerca una sede...">
      <datalist id="provlist"></datalist>
    </div>
  </div>
  <div class="controls">
    <div class="grp"><span class="lbl">Storie</span>
      <button class="preset" data-p="tot">Totale nazionale</button>
      <button class="preset" data-p="top">Top 5 IDPT</button>
      <button class="preset" data-p="2009">Nate nel 2009</button>
      <button class="preset" data-p="sardegna">Sardegna (salto 2012)</button>
      <button class="preset" data-p="clear">Pulisci</button>
    </div>
  </div>
  <div class="chips" id="chips"></div>
  <div class="chartbox"><canvas id="cv"></canvas></div>
  <p class="cap"><b>2009</b>: nascita di Barletta-Andria-Trani, Fermo e Monza-Brianza, prima assenti come sedi autonome.
  <b>2012</b>: l'INPS accorpa le ex-province sarde, da cui il salto di Cagliari-e-Sud-Sardegna, Sassari e Nuoro.
  Il <b>totale nazionale</b> resta continuo perche le discontinuita sono ridistribuzioni interne. Fonte: Osservatorio INPS, serie storica; importo medio mensile come misura primaria, importo annuo ricostruito non mostrato.</p>
</div>
<script>
const D = __DATA__;
const MAC_COLOR = {'Nord-Ovest':'#4a5d8a','Nord-Est':'#5b8a72','Centro':'#c9a13b','Sud':'#b5524a','Isole':'#7d5ba6'};
const PALETTE = ['#4a5d8a','#b5524a','#5b8a72','#c9a13b','#7d5ba6','#3a8ea5','#d07b3f','#9aa23b','#c25b8c','#6a6f7d'];
const fmt = new Intl.NumberFormat('it-IT');
const byLabel = {}; D.series.forEach((s,i)=>byLabel[s.label]=i);
let measure='num';
let selected=['__TOT__']; // keys: '__TOT__' or a label
const PRESETS={
  tot:['__TOT__'],
  top:['Reggio Calabria','Taranto','Catanzaro','Oristano','Nuoro'],
  '2009':['Barletta-Andria-Trani','Fermo','Monza e della Brianza'],
  sardegna:['Cagliari e Sud Sardegna','Sassari','Nuoro','Oristano']
};
// datalist
const dl=document.getElementById('provlist');
D.series.map(s=>s.label).sort((a,b)=>a.localeCompare(b,'it')).forEach(l=>{
  const o=document.createElement('option');o.value=l;dl.appendChild(o);});

function colorFor(key,i){ if(key==='__TOT__') return '#111'; return PALETTE[i%PALETTE.length]; }
function valuesFor(key){
  if(key==='__TOT__') return measure==='num'?D.totale:D.totale.map(()=>null);
  const s=D.series[byLabel[key]]; return s? s[measure] : null;
}
function macroFor(key){ return key==='__TOT__'?'Italia':(D.series[byLabel[key]]||{}).macro; }

let chart;
const vlines={id:'vlines',afterDraw(c){
  const xs=c.scales.x, ya=c.scales.y, ctx=c.ctx;
  [[2009,'2009 - nuove province'],[2012,'2012 - Sardegna']].forEach(([yr,txt])=>{
    const xp=xs.getPixelForValue(yr); if(isNaN(xp))return;
    ctx.save();ctx.strokeStyle='#bbb';ctx.setLineDash([4,4]);ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(xp,ya.top);ctx.lineTo(xp,ya.bottom);ctx.stroke();
    ctx.setLineDash([]);ctx.fillStyle='#999';ctx.font='10px -apple-system,sans-serif';
    ctx.textAlign='left';ctx.fillText(txt,xp+3,ya.top+10);ctx.restore();});
}};

function render(){
  const ds=selected.map((key,i)=>{
    const c=colorFor(key,i),isTot=key==='__TOT__';
    return {label:isTot?'Totale nazionale (asse dx)':key,data:valuesFor(key),
      borderColor:c,backgroundColor:c,borderWidth:isTot?3:2,borderDash:isTot?[6,3]:[],
      yAxisID:isTot?'yTot':'y',pointRadius:0,pointHoverRadius:4,tension:.15,spanGaps:false};
  });
  const hasTot=selected.includes('__TOT__')&&measure==='num';
  if(chart){chart.data.datasets=ds;
    chart.options.scales.y.title.text=measure==='num'?'numero pensioni (provincia)':'EUR / mese';
    chart.options.scales.yTot.display=hasTot;chart.update();}
  else{
    chart=new Chart(document.getElementById('cv'),{type:'line',
      data:{labels:D.years,datasets:ds},
      options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'nearest',intersect:false},
        plugins:{legend:{position:'bottom',labels:{boxWidth:14,font:{size:11.5}}},
          tooltip:{callbacks:{label:ctx=>{const v=ctx.parsed.y;return ctx.dataset.label+': '+(v==null?'n.d.':(measure==='med'?'EUR '+fmt.format(v):fmt.format(v)));}}}},
        scales:{x:{title:{display:false},ticks:{maxTicksLimit:12,font:{size:11}}},
          y:{position:'left',title:{display:true,text:'numero pensioni (provincia)'},ticks:{font:{size:11},callback:v=>fmt.format(v)}},
          yTot:{position:'right',display:hasTot,grid:{drawOnChartArea:false},title:{display:true,text:'totale Italia'},ticks:{font:{size:11},callback:v=>fmt.format(v)}}}},
      plugins:[vlines]});
  }
  renderChips();
}
function renderChips(){
  const box=document.getElementById('chips');box.innerHTML='';
  selected.forEach((key,i)=>{
    const c=colorFor(key,i),el=document.createElement('span');el.className='chip';
    el.innerHTML='<b style="background:'+c+'"></b>'+(key==='__TOT__'?'Totale nazionale':key+' <small style="color:#888">'+macroFor(key)+'</small>')+' <span class="x">x</span>';
    el.querySelector('.x').onclick=()=>{selected.splice(i,1);render();};
    box.appendChild(el);});
}
document.querySelectorAll('button.opt').forEach(b=>b.onclick=()=>{
  measure=b.dataset.m;document.querySelectorAll('button.opt').forEach(x=>x.classList.toggle('active',x===b));
  if(measure==='med'&&selected.includes('__TOT__')){selected=selected.filter(k=>k!=='__TOT__');if(!selected.length)selected=['Reggio Calabria','Milano'];}
  render();});
document.querySelectorAll('button.preset').forEach(b=>b.onclick=()=>{
  const p=b.dataset.p;if(p==='clear'){selected=[];}else{selected=PRESETS[p].filter(l=>l==='__TOT__'||l in byLabel);}
  if(measure==='med')selected=selected.filter(k=>k!=='__TOT__');render();});
document.getElementById('picker').addEventListener('change',e=>{
  const v=e.target.value;if(v in byLabel&&!selected.includes(v)){selected.push(v);render();}e.target.value='';});
// default extra
if(!selected.includes('Reggio Calabria'))selected.push('Reggio Calabria');
if('Milano' in byLabel)selected.push('Milano');
render();
</script></body></html>"""

def build_html(d):
    return TEMPLATE.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",",":")))

if __name__=="__main__":
    d=extract()
    print("sedi:",len(d["series"]),"| tot 2026:",d["totale"][-1],"(atteso ~20.925.421) | tot 1998:",d["totale"][0])
    print("macroaree:",sorted(set(s["macro"] for s in d["series"])))
    html=build_html(d)
    open("docs/serie_storica.html","w",encoding="utf-8").write(html)
    print("scritto docs/serie_storica.html (%d KB)" % (len(html)//1024))
