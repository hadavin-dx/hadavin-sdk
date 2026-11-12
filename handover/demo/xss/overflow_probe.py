import time,json
from playwright.sync_api import sync_playwright
OUT="/tmp/demo-wt/handover/demo/xss"
with sync_playwright() as p:
    b=p.chromium.launch(); out={}
    for scheme in("light","dark"):
        ctx=b.new_context(color_scheme=scheme,viewport={"width":1280,"height":900}); pg=ctx.new_page()
        pg.goto("http://127.0.0.1:8765/ui/#/leads",wait_until="networkidle"); pg.wait_for_selector('[data-testid="lead-row"]')
        pg.locator('[data-testid="leads-hide-personal"]').uncheck(); time.sleep(.6)
        for lid,tag in(("Lae63cd1d003a","len200"),("Ld2146dba4130","len100")):
            pg.locator(f'[data-lead-id="{lid}"]').click(); time.sleep(1)
            pg.screenshot(path=f"{OUT}/drawer-{scheme}-unmasked-{tag}.png")
            out[f"{scheme}-{tag}"]=pg.evaluate("""()=>{const d=document.querySelector('[data-testid=lead-drawer]');const r=[];
              d.querySelectorAll('*').forEach(e=>{if(e.scrollWidth>e.clientWidth+1&&e.clientWidth>0)r.push([e.tagName,e.className,e.scrollWidth,e.clientWidth,getComputedStyle(e).overflowX])});
              const cr=d.getBoundingClientRect();return {drawer:[d.scrollWidth,d.clientWidth,cr.width],over:r.slice(0,8),bodyOverflowX:getComputedStyle(document.documentElement).overflowX,docSW:document.documentElement.scrollWidth}}""")
            pg.keyboard.press("Escape"); time.sleep(.4)
        # table row for 200: element rect vs table-wrap
        out[f"{scheme}-table"]=pg.evaluate("""()=>{const w=document.querySelector('.table-wrap');const r=document.querySelector('[data-lead-id=Lae63cd1d003a]');const c=r.cells[0];return {wrap:[w.scrollWidth,w.clientWidth],rowh:r.getBoundingClientRect().height,cell0:[c.scrollWidth,c.clientWidth],cellText:c.innerText.length}}""")
        ctx.close()
    b.close()
json.dump(out,open(OUT+"/06-overflow-probe.json","w"),indent=1); print(json.dumps(out,indent=1))
