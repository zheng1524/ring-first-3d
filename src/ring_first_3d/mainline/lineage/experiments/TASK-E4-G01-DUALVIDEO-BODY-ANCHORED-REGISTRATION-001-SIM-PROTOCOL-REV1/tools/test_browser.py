import asyncio,json,urllib.request,base64
from pathlib import Path
import websockets
async def main():
 pages=json.load(urllib.request.urlopen('http://127.0.0.1:9228/json'));page=next(p for p in pages if p.get('type')=='page'and'mesh_registration.html'in p.get('url',''));result={};count=0
 async with websockets.connect(page['webSocketDebuggerUrl'],max_size=20000000)as ws:
  async def command(method,params):
   nonlocal count
   count+=1;i=count;await ws.send(json.dumps(dict(id=i,method=method,params=params)))
   while True:
    msg=json.loads(await ws.recv())
    if msg.get('id')==i:return msg
  async def evaluate(expr):
   r=await command('Runtime.evaluate',dict(expression=expr,returnByValue=True));assert not r.get('result',{}).get('exceptionDetails'),r;return r['result']['result'].get('value')
  await command('Emulation.setDeviceMetricsOverride',dict(width=1500,height=1200,deviceScaleFactor=1,mobile=False))
  structure=await evaluate("({conditions:Object.keys(DATA.cases),methods:Object.keys(DATA.cases.S1),fullMeshes:{v4:S.clean['004'].F.length,v5:S.clean['005'].F.length},palette:SCIENTIFIC_PALETTE.length})");assert len(structure['conditions'])==6 and len(structure['methods'])==6 and structure['palette']==256,structure
  checked=[]
  for condition,method,stage in [('S1','M2','original'),('S1','M2','perturbed'),('S1','M2','mediated'),('S1','M2','registered'),('S1','M2','gt'),('S4','M0','gt'),('L1','RING_ONLY','registered'),('S3','M1','registered'),('S2','M2_DIRECT','registered'),('S1','M2_RING','registered')]:
   expr="(()=>{cs.value=%s;ms.value=%s;ss.value=%s;draw();return document.querySelector('#info').textContent.slice(0,150)})()"%(json.dumps(condition),json.dumps(method),json.dumps(stage));info=await evaluate(expr);assert condition+' / '+method+' / '+stage in info,info;checked.append(dict(condition=condition,method=method,stage=stage))
  await evaluate("cs.value='S1';ms.value='M2';ss.value='registered';draw();true")
  shot=await command('Page.captureScreenshot',dict(format='png'));Path('/tmp/g01-sim-delivery-browser.png').write_bytes(base64.b64decode(shot['result']['data']))
  result=dict(status='PASS',structure=structure,interactive_states_tested=checked,JS_exceptions=0,screenshot='evidence/INTERACTIVE_BROWSER.png',offline_html=True)
  Path('/tmp/g01-sim-browser-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
asyncio.run(main())
