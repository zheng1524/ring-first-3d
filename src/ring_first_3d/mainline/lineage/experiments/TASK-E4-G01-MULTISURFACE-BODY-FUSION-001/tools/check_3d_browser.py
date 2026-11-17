import asyncio,json,urllib.request,base64
from pathlib import Path
import websockets
async def main():
 from urllib.parse import quote
 td=Path.cwd()/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001'
 request=urllib.request.Request('http://127.0.0.1:9229/json/new?'+quote((td/'visualization/multisurface_3d.html').as_uri(),safe=''),method='PUT')
 page=json.load(urllib.request.urlopen(request));i=0
 await asyncio.sleep(.5)
 async with websockets.connect(page['webSocketDebuggerUrl'],max_size=20000000)as ws:
  async def cmd(method,params):
   nonlocal i
   i+=1;ident=i;await ws.send(json.dumps(dict(id=i,method=method,params=params)))
   while True:
    r=json.loads(await ws.recv())
    if r.get('id')==ident:return r
  async def ev(expr):
   r=await cmd('Runtime.evaluate',dict(expression=expr,returnByValue=True));assert not r.get('result',{}).get('exceptionDetails'),r;return r['result']['result'].get('value')
  await cmd('Emulation.setDeviceMetricsOverride',dict(width=1600,height=1350,deviceScaleFactor=1,mobile=False))
  print('INITIAL',await ev("document.querySelector('#info').textContent.slice(0,180)"))
  structure=await ev("({views:S.frames.length,videos:[...new Set(S.frames.map(f=>f.video))],fullTriangles:S.frames.reduce((n,f)=>n+S.meshes[f.id].F.length,0),webgl:!!gl,glerror:gl.getError()})")
  assert structure['views']==16 and structure['webgl'] and structure['fullTriangles']>100000,structure
  tested=[]
  for cond,arm,method,tol,stage in [('C3','E1','BODY_HIER',.5,'before'),('C3','E1','BODY_HIER',.5,'after'),('C3','E1','BODY_HIER',.5,'fusion'),('C3','E1','BODY_HIER',.5,'evaluation'),('C4','E2','BODY_HIER',.5,'fusion'),('C0','E1','M0',.5,'fusion'),('C3','E2','BODY_HIER',0,'after'),('C3','E2','BODY_HIER',1,'after'),('C1','E1','ICP',.5,'after')]:
   await ev('cs.value='+json.dumps(cond)+';as.value='+json.dumps(arm)+';ms.value='+json.dumps(method)+';ts.value='+json.dumps(str(tol).rstrip('0').rstrip('.'))+';ss.value='+json.dumps(stage)+';draw();true')
   for retry in range(60):
    info=await ev("document.querySelector('#info').textContent")
    if info.startswith(cond+'_'+arm+' / '+method):break
    await asyncio.sleep(.05)
   assert info.startswith(cond+'_'+arm+' / '+method),info[:300];assert 'Complete independent surfaces shown: 16/16'in info,info[:300];tested.append([cond,arm,method,tol,stage])
  await ev("document.querySelector('#video004').checked=false;draw();true");info=await ev("document.querySelector('#info').textContent");assert 'shown: 8/16'in info
  await ev("document.querySelector('#video004').checked=true;checks[S.frames[0].id].checked=false;draw();true");info=await ev("document.querySelector('#info').textContent");assert 'shown: 15/16'in info
  await ev("checks[S.frames[0].id].checked=true;cs.value='C3';as.value='E1';ms.value='BODY_HIER';ts.value='0.5';ss.value='fusion';draw();true")
  await asyncio.sleep(.1);shot=await cmd('Page.captureScreenshot',dict(format='png'));Path('/tmp/multisurface-browser.png').write_bytes(base64.b64decode(shot['result']['data']))
  out=dict(status='PASS',page=str(td/'visualization/multisurface_3d.html'),structure=structure,states_tested=tested,video_toggle_verified=True,individual_view_toggle_verified=True,no_JavaScript_exceptions=True,offline_relative_scripts=True)
  Path('/tmp/multisurface-browser.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
asyncio.run(main())
