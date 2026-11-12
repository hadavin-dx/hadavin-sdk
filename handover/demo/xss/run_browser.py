import json, sys, time
from playwright.sync_api import sync_playwright
OUT="/tmp/demo-wt/handover/demo/xss"
BASE="http://127.0.0.1:8765/ui/"
CASES={"a":"<script>window.__xss=1</script>","b":'<img src=x onerror="window.__xss=2">',"c":'<svg onload="window.__xss=3">',
 "d":'"><iframe srcdoc="<script>parent.__xss=4</script>">',"e":"javascript:window.__xss=5","f":"'; DROP TABLE leads;--",
 "h2":"H"*200,"i":"{{7*7}} and ${7*7}","k":"Emoji \U0001F600 Person","l-company":"<script>window.__xss=11</script><img src=x onerror=window.__xss=12>",
 "l-message":'<svg onload="window.__xss=13"> "><iframe srcdoc="<script>parent.__xss=14</script>">'}
PAGES=["overview","leads","needs","log","data","demo"]
res=[]
def run():
  with sync_playwright() as p:
    b=p.chromium.launch()
    print("chromium",b.version)
    for scheme in ("light","dark"):
      for masked in (True,False):
        ctx=b.new_context(color_scheme=scheme,viewport={"width":1280,"height":900})
        pg=ctx.new_page()
        dialogs=[];cons=[];perr=[]
        pg.on("dialog",lambda d:(dialogs.append((d.type,d.message)),d.dismiss()))
        pg.on("console",lambda m:cons.append((m.type,m.text)) if m.type in("error","warning") else None)
        pg.on("pageerror",lambda e:perr.append(str(e)))
        pg.goto(BASE+"#/leads",wait_until="networkidle"); pg.wait_for_selector('[data-testid="lead-row"]',timeout=10000)
        if not masked:
          pg.locator('[data-testid="leads-hide-personal"]').uncheck()
          time.sleep(.5)
        for route in PAGES:
          d0,c0,e0=len(dialogs),len(cons),len(perr)
          pg.goto(BASE+"#/"+route); pg.reload(wait_until="networkidle"); time.sleep(1.2)
          if route=="leads":
            try: pg.wait_for_selector('[data-testid="lead-row"]',timeout=8000)
            except Exception as e: pass
          txt=pg.inner_text("#main"); html=pg.content()
          present=[k for k,v in CASES.items() if v in txt]
          info=pg.evaluate("""()=>{const m=document.querySelector('#main');
            const q=s=>m.querySelectorAll(s).length;
            return {xss:String(window.__xss),script_in_main:q('script'),img_src_x:q('img[src="x"]'),img_any:q('img'),svg_with_onload:q('svg[onload]'),svg_total_in_main:q('svg'),iframe:q('iframe'),
             onerror_attr:q('[onerror]'),onload_attr:q('[onload]'),
             doc_iframe:document.querySelectorAll('iframe').length,doc_onattr:document.querySelectorAll('[onerror],[onload],[onclick]').length,
             sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,
             wraps:[...document.querySelectorAll('.table-wrap')].map(w=>[w.scrollWidth,w.clientWidth]),
             theme:document.documentElement.getAttribute('data-theme'),cs:getComputedStyle(document.documentElement).colorScheme,
             hidebox:(document.querySelector('[data-testid=leads-hide-personal]')||{}).checked}}""")
          row=dict(scheme=scheme,masked=masked,route=route,text_present=present,raw_script_literal_in_content=("<script>window.__xss" in html),escaped_in_content=html.count("&lt;script&gt;window.__xss=1"),
             dialogs=dialogs[d0:],console=cons[c0:],pageerrors=perr[e0:],**info)
          if route=="leads":
            shot=f"{OUT}/leads-{scheme}-{'masked' if masked else 'unmasked'}.png"
            pg.screenshot(path=shot,full_page=True)
            from struct import unpack
            w,h=unpack(">II",open(shot,"rb").read()[16:24]); row["screenshot"]=[shot,w,h]
            rows=pg.locator('[data-testid="lead-row"]'); n=rows.count(); row["lead_rows"]=n
            drawers=[]
            for i in range(n):
              r=rows.nth(i); rt=r.inner_text()[:60].replace("\n"," | ")
              r.click(); time.sleep(.8)
              dt=pg.locator('[data-testid="lead-drawer"]')
              dinfo=pg.evaluate("""()=>{const d=document.querySelector('[data-testid=lead-drawer]');if(!d)return null;const q=s=>d.querySelectorAll(s).length;
                return {script:q('script'),img_src_x:q('img[src="x"]'),iframe:q('iframe'),onattr:q('[onerror],[onload]'),svg_onload:q('svg[onload]'),sw:d.scrollWidth,cw:d.clientWidth,xss:String(window.__xss)}}""")
              dtxt=dt.inner_text() if dt.count() else ""
              dinfo["case_text"]=[k for k,v in CASES.items() if v in dtxt]; dinfo["row"]=rt
              drawers.append(dinfo)
              if i==0 or any(k in dinfo["case_text"] for k in("a","d")) and not masked and i<8 and len([x for x in drawers if x["case_text"]])==1:
                pg.screenshot(path=f"{OUT}/drawer-{scheme}-{'masked' if masked else 'unmasked'}-{i}.png")
              pg.keyboard.press("Escape"); time.sleep(.3)
            row["drawers"]=drawers
            # narrow viewport overflow
            pg.set_viewport_size({"width":390,"height":800}); time.sleep(.6)
            row["narrow390"]=pg.evaluate("()=>[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
            pg.screenshot(path=f"{OUT}/leads-{scheme}-{'masked' if masked else 'unmasked'}-390.png",full_page=True)
            pg.set_viewport_size({"width":1280,"height":900})
          row["xss_final"]=pg.evaluate("String(window.__xss)")
          res.append(row)
        ctx.close()
    b.close()
run()
json.dump(res,open(OUT+"/05-browser-results.json","w"),indent=1,ensure_ascii=False)
print("done",len(res))
