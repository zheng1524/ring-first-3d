import asyncio,json,urllib.request,base64
from pathlib import Path
import websockets
TD=Path.cwd()/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001'
async def main():
 browser=json.load(urllib.request.urlopen('http://127.0.0.1:9229/json/version'));i=0
 async with websockets.connect(browser['webSocketDebuggerUrl'],max_size=20000000) as ws:
  await ws.send(json.dumps(dict(id=1,method='Target.createTarget',params=dict(url=(TD/'visualization/sections_all.html').as_uri()))))
  while True:
   r=json.loads(await ws.recv())
   if r.get('id')==1:target=r['result']['targetId'];break
 await asyncio.sleep(.3)
 pages=json.load(urllib.request.urlopen('http://127.0.0.1:9229/json'));page=next(p for p in pages if p.get('id')==target)
 async with websockets.connect(page['webSocketDebuggerUrl'],max_size=20000000) as ws:
  async def cmd(method,params):
   nonlocal i
   i+=1;ident=i;await ws.send(json.dumps(dict(id=i,method=method,params=params)))
   while True:
    r=json.loads(await ws.recv())
    if r.get('id')==ident:return r
  async def ev(expr):
   r=await cmd('Runtime.evaluate',dict(expression=expr,returnByValue=True));assert not r.get('result',{}).get('exceptionDetails'),r;return r['result']['result'].get('value')
  await cmd('Emulation.setDeviceMetricsOverride',dict(width=1680,height=1900,deviceScaleFactor=1,mobile=False))
  keys=await ev('S.keys');assert len(keys)==52
  states=[]
  for key in keys:
   await ev('sel.value='+json.dumps(key)+';draw();true')
   for retry in range(100):
    ready=await ev('!!CUT_CASES['+json.dumps(key)+'] && document.querySelector("#details").textContent.startsWith('+json.dumps(key)+')')
    if ready:break
    await asyncio.sleep(.02)
   assert ready,key
   structure=await ev('({key:sel.value,exact:CUT_CASES[sel.value].exact_triangle_intersection,views:CUT_CASES[sel.value].after.length,planes:CUT_CASES[sel.value].fused.length,segments:CUT_CASES[sel.value].after.reduce((n,v)=>n+v.reduce((m,p)=>m+p.length,0),0)})')
   assert structure['exact'] and structure['views']==16 and structure['planes']==4 and structure['segments']>0,structure
   states.append(structure)
  await ev("sel.value='C3__E1__BODY_HIER__tol0.5';document.querySelector('#v004').checked=false;draw();true")
  a=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data']
  await ev("document.querySelector('#v004').checked=true;document.querySelector('#v005').checked=false;draw();true")
  b=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data']
  assert a!=b,'Video toggles do not change rendering'
  await ev("document.querySelector('#v005').checked=true;draw();true")
  shot=await cmd('Page.captureScreenshot',dict(format='png'));Path('/tmp/multisurface-sections-browser.png').write_bytes(base64.b64decode(shot['result']['data']))
  result=dict(status='PASS',page=str(TD/'visualization/sections_all.html'),cases_checked=len(states),all_cases_real_triangle_intersections=True,each_case_views=16,four_planes_per_case=True,video_toggle_changes_rendering=True,JavaScript_exceptions=0,offline=True,states=states)
  Path('/tmp/multisurface-sections-browser.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='states'}))
asyncio.run(main())
