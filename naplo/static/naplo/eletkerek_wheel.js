(function () {
  "use strict";

  function $(sel, root){ return (root||document).querySelector(sel); }
  function $all(sel, root){ return Array.from((root||document).querySelectorAll(sel)); }

  const COLORS = ["#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F","#EDC948","#B07AA1","#FF9DA7"];

  function clear(node){ while(node && node.firstChild) node.removeChild(node.firstChild); }

  function drawTest(svg, msg){
    const NS="http://www.w3.org/2000/svg";
    clear(svg);
    svg.setAttribute("viewBox","0 0 420 320");
    const cx=210, cy=160, r=120;

    const circle=document.createElementNS(NS,"circle");
    circle.setAttribute("cx",cx); circle.setAttribute("cy",cy); circle.setAttribute("r",r);
    circle.setAttribute("fill","#f5f5f7"); circle.setAttribute("stroke","#ddd"); circle.setAttribute("stroke-width","2");
    svg.appendChild(circle);

    const t=document.createElementNS(NS,"text");
    t.setAttribute("x",cx); t.setAttribute("y",cy);
    t.setAttribute("text-anchor","middle"); t.setAttribute("dominant-baseline","middle");
    t.setAttribute("fill","#666"); t.setAttribute("font-size","14");
    t.textContent = msg || "WHEEL JS OK";
    svg.appendChild(t);
  }

  function safeNum(x){ const n=Number(x); return Number.isFinite(n)?n:0; }

  function parseTile(tile){
    const label = tile.dataset.label || (tile.querySelector(".title")?.textContent || "").trim();
    const minutesTxt = tile.querySelector(".meta b")?.textContent || "";
    // formatMinutes -> "1 óra 15 perc" stb. -> itt percet nehéz; viszont a backend adja it.minutes percben,
    // ezért a tile-ban a title attribútumból kiolvassuk: "<minutes> perc (<pct>%)"
    const barwrap = tile.querySelector(".barwrap");
    const title = barwrap?.getAttribute("title") || "";
    const mMin = title.match(/(\d+)\s*perc/i);
    const minutes = mMin ? safeNum(mMin[1]) : 0;

    const pctTxt = tile.querySelector(".meta .muted")?.textContent || "0%";
    const mPct = pctTxt.match(/(\d+(?:[.,]\d+)?)\s*%/);
    const pct = mPct ? safeNum(String(mPct[1]).replace(",", ".")) : 0;

    return { label, minutes, pct, code: tile.dataset.code || "" };
  }

  function polar(cx,cy,r,deg){
    const rad=(deg-90)*Math.PI/180;
    return {x:cx+r*Math.cos(rad), y:cy+r*Math.sin(rad)};
  }
  function arcPath(cx,cy,r,a0,a1){
    const p0=polar(cx,cy,r,a1), p1=polar(cx,cy,r,a0);
    const large=(a1-a0)>180 ? 1 : 0;
    return `M ${cx} ${cy} L ${p0.x} ${p0.y} A ${r} ${r} 0 ${large} 0 ${p1.x} ${p1.y} Z`;
  }

  function render(){
    const svg=$("#wheelSvg");
    const legend=$("#wheelLegend");
    if(!svg) return;

    const tiles=$all("#tiles .tile");
    if(!tiles.length){
      drawTest(svg, "NINCS KÁRTYA");
      if(legend) legend.textContent="";
      return;
    }

    const items=tiles.map(parseTile);
    const total=items.reduce((s,it)=>s+it.minutes,0);
    if(total<=0){
      drawTest(svg, "0 PERC");
      if(legend) legend.textContent="";
      return;
    }

    const NS="http://www.w3.org/2000/svg";
    clear(svg);
    if(legend) legend.innerHTML="";
    svg.setAttribute("viewBox","0 0 420 320");

    const cx=210, cy=160, r=120;
    let ang=0;

    items.filter(it=>it.minutes>0).forEach((it,i)=>{
      const slice=it.minutes/total*360;
      const a0=ang, a1=ang+slice;
      ang=a1;

      const path=document.createElementNS(NS,"path");
      path.setAttribute("d", arcPath(cx,cy,r,a0,a1));
      path.setAttribute("fill", COLORS[i%COLORS.length]);
      path.setAttribute("stroke", "#fff");
      path.setAttribute("stroke-width","2");
      path.style.cursor="pointer";
      const pct=it.minutes/total*100;

      const title=document.createElementNS(NS,"title");
      title.textContent = `${it.label}: ${pct.toFixed(1)}% (${it.minutes} perc)`;
      path.appendChild(title);

      path.addEventListener("click", ()=>{
        const target=$all("#tiles .tile").find(t => (t.dataset.label||"")===it.label);
        if(target) target.click();
      });

      svg.appendChild(path);

      if(legend){
        const row=document.createElement("div");
        row.style.display="flex"; row.style.alignItems="center"; row.style.gap="8px"; row.style.padding="4px 0";
        const sw=document.createElement("span");
        sw.style.width="10px"; sw.style.height="10px"; sw.style.borderRadius="3px";
        sw.style.background = COLORS[i%COLORS.length]; sw.style.display="inline-block";
        const txt=document.createElement("span");
        txt.style.fontSize="12px"; txt.style.color="#444";
        txt.textContent = `${it.label} — ${pct.toFixed(1)}% (${it.minutes} perc)`;
        row.appendChild(sw); row.appendChild(txt);
        legend.appendChild(row);
      }
    });
  }

  function schedule(){
    setTimeout(()=>{ try{ render(); }catch(e){ console.error(e); } }, 50);
    setTimeout(()=>{ try{ render(); }catch(e){ console.error(e); } }, 250);
    setTimeout(()=>{ try{ render(); }catch(e){ console.error(e); } }, 800);
  }

  document.addEventListener("DOMContentLoaded", ()=>{
    const svg=$("#wheelSvg");
    if(svg) drawTest(svg, "WHEEL JS OK");
    const tiles=$("#tiles");
    if(tiles){
      new MutationObserver(()=>schedule()).observe(tiles,{childList:true,subtree:true});
    }
    const refresh=$("#refreshBtn");
    if(refresh) refresh.addEventListener("click", ()=>schedule());
    schedule();
    console.log("eletkerek_wheel.js loaded");
  });
})();
