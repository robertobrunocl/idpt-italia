#!/usr/bin/env python3
"""Genera docs/decorrenza_gdp.html: grafico interattivo dell'eta media alla
decorrenza e dell'importo medio delle pensioni dei dipendenti pubblici (GDP),
per anno di decorrenza 1980-2025, estratto dal cubo 4 del grafo RDF.
Dati iniettati inline (solo Chart.js da CDN)."""
import json
from rdflib import Graph
BASE = "https://robertobrunocl.github.io/idpt-italia/"

def extract():
    g = Graph(); g.parse("output/observations/cubo4_decorrenza_gdp.ttl", format="turtle")
    q = """PREFIX idpt:<%(b)s> SELECT ?a ?eta ?imp ?n WHERE {
      ?o idpt:annoDecorrenza ?a ; idpt:etaMediaDecorrenza ?eta ;
         idpt:importoMedioMensile ?imp ; idpt:numeroPensioni ?n . }""" % {"b": BASE}
    rows = sorted((int(str(a)), round(float(e),1), round(float(i)), int(str(n)))
                  for a,e,i,n in g.query(q))
    return {"anni":[r[0] for r in rows], "eta":[r[1] for r in rows],
            "imp":[r[2] for r in rows], "num":[r[3] for r in rows]}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eta e importo delle pensioni per anno di decorrenza - IDPT</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root{--primary:#4a5d8a;--accent:#b5524a;--text:#222;--text-light:#555;--border:#e0e0e0;--bg:#f5f7fb}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--text);background:#fff;font-size:14px;line-height:1.5}
  .wrap{max-width:900px;margin:0 auto;padding:18px 16px 28px}
  h1{font-size:19px;color:var(--primary);margin:0 0 2px}
  .sub{color:var(--text-light);font-size:12.5px;margin:0 0 14px}
  .controls{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin-bottom:10px}
  .grp{display:flex;align-items:center;gap:6px}
  .grp>span.lbl{font-size:11.5px;color:var(--text-light);text-transform:uppercase;letter-spacing:.04em}
  button.opt{font:inherit;font-size:12.5px;border:1px solid var(--border);background:#fff;color:var(--text);
    padding:5px 10px;border-radius:6px;cursor:pointer;transition:all .12s}
  button.opt:hover{border-color:var(--primary);background:var(--bg)}
  button.opt.active{background:var(--primary);color:#fff;border-color:var(--primary)}
  .chartbox{position:relative;height:440px}
  .cap{font-size:12px;color:var(--text-light);margin-top:12px;border-top:1px solid var(--border);padding-top:10px}
  .cap b{color:var(--text)}
</style></head><body>
<div class="wrap">
  <h1>La parabola delle riforme: eta e importo delle pensioni nel tempo</h1>
  <p class="sub">Pensioni dei dipendenti pubblici (gestione GDP) ancora vigenti, per <b>anno di decorrenza</b> 1980-2025. Eta media alla decorrenza e importo medio mensile. Dati dal cubo 4 del grafo RDF (livello nazionale). Le linee verticali segnano le grandi riforme previdenziali.</p>
  <div class="controls">
    <div class="grp"><span class="lbl">Mostra</span>
      <button class="opt active" data-s="both">Eta + importo</button>
      <button class="opt" data-s="eta">Solo eta</button>
      <button class="opt" data-s="imp">Solo importo</button>
    </div>
  </div>
  <div class="chartbox"><canvas id="cv"></canvas></div>
  <p class="cap">L'<b>eta media alla decorrenza</b> sale da ~40 a 67 anni: dall'epoca delle <b>"pensioni baby"</b> del pubblico impiego (ritiri anche prima dei 50 anni, abolite dalla riforma <b>Amato 1992</b>) al regime post-<b>Fornero 2011</b>, passando per la <b>Dini 1995</b>. Due cautele: (1) <b>bias di sopravvivenza</b> sulle coorti vecchie - il valore e l'eta dei soli pensionati ancora vigenti nel 2026, quindi atipicamente bassa prima del ~1995; per le coorti recenti il segnale e pulito. (2) il cubo copre i <b>soli dipendenti pubblici</b>, a livello nazionale - non l'intero sistema. L'importo medio e quello corrente (rivalutato), non quello alla decorrenza. Fonte: Osservatorio INPS, pensioni per anno di decorrenza.</p>
</div>
<script>
const D = __DATA__;
let mode='both';
const C_ETA='#4a5d8a', C_IMP='#b5524a';
const fmt=new Intl.NumberFormat('it-IT');
const REFORMS=[[1992,'Amato 1992'],[1995,'Dini 1995'],[2011,'Fornero 2011']];

const vlines={id:'vlines',afterDraw(c){
  const xs=c.scales.x, ya=c.chartArea, ctx=c.ctx;
  REFORMS.forEach(([yr,txt])=>{
    const xp=xs.getPixelForValue(yr); if(isNaN(xp))return;
    ctx.save();ctx.strokeStyle='#c9a13b';ctx.setLineDash([4,4]);ctx.lineWidth=1.2;
    ctx.beginPath();ctx.moveTo(xp,ya.top);ctx.lineTo(xp,ya.bottom);ctx.stroke();
    ctx.setLineDash([]);ctx.fillStyle='#9a7b1f';ctx.font='bold 10px -apple-system,sans-serif';
    ctx.textAlign='left';ctx.fillText(txt,xp+3,ya.top+11);ctx.restore();});
}};

let chart;
function datasets(){
  const ds=[];
  if(mode==='both'||mode==='eta') ds.push({label:'Eta media alla decorrenza (anni)',data:D.eta,
    borderColor:C_ETA,backgroundColor:C_ETA,yAxisID:'yEta',borderWidth:2.5,pointRadius:0,pointHoverRadius:4,tension:.2});
  if(mode==='both'||mode==='imp') ds.push({label:'Importo medio mensile (EUR)',data:D.imp,
    borderColor:C_IMP,backgroundColor:C_IMP,yAxisID:'yImp',borderWidth:2,borderDash:[6,3],pointRadius:0,pointHoverRadius:4,tension:.2});
  return ds;
}
function render(){
  const showEta=mode!=='imp', showImp=mode!=='eta';
  if(chart){chart.data.datasets=datasets();chart.options.scales.yEta.display=showEta;chart.options.scales.yImp.display=showImp;chart.update();return;}
  chart=new Chart(document.getElementById('cv'),{type:'line',
    data:{labels:D.anni,datasets:datasets()},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:14,font:{size:11.5}}},
        tooltip:{callbacks:{
          title:items=>'Decorrenza '+items[0].label,
          label:ctx=>ctx.dataset.label+': '+(ctx.dataset.yAxisID==='yImp'?'EUR '+fmt.format(ctx.parsed.y):ctx.parsed.y+' anni'),
          afterBody:items=>{const i=items[0].dataIndex;return 'pensioni vigenti di questa coorte: '+fmt.format(D.num[i]);}}}},
      scales:{x:{ticks:{maxTicksLimit:12,font:{size:11}}},
        yEta:{position:'left',display:showEta,title:{display:true,text:'eta (anni)'},suggestedMin:35,suggestedMax:70,ticks:{font:{size:11}}},
        yImp:{position:'right',display:showImp,grid:{drawOnChartArea:false},title:{display:true,text:'EUR / mese'},ticks:{font:{size:11},callback:v=>fmt.format(v)}}}},
    plugins:[vlines]});
}
document.querySelectorAll('button.opt[data-s]').forEach(b=>b.onclick=()=>{
  mode=b.dataset.s;document.querySelectorAll('button.opt[data-s]').forEach(x=>x.classList.toggle('active',x===b));render();});
render();
</script></body></html>"""

def build_html(d):
    return TEMPLATE.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",",":")))

if __name__ == "__main__":
    d = extract()
    print("coorti:", len(d["anni"]), "| range:", d["anni"][0], "-", d["anni"][-1])
    print("eta:", d["eta"][0], "->", d["eta"][-1], "| importo:", d["imp"][0], "->", d["imp"][-1])
    open("docs/decorrenza_gdp.html", "w", encoding="utf-8").write(build_html(d))
    print("scritto docs/decorrenza_gdp.html")
