"""Chrome renders every actual GT-aligned Mesh and every full HERO method."""
import asyncio,json,urllib.request,base64
from urllib.parse import quote
from pathlib import Path
import websockets
TD=Path.cwd()/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001';VIS=TD/'visualization';PORT=9449
async def check(path,hero):
 req=urllib.request.Request(f'http://127.0.0.1:{PORT}/json/new?'+quote(path.as_uri(),safe=''),method='PUT');page=json.load(urllib.request.urlopen(req));await asyncio.sleep(.3);i=0;exceptions=[]
 async with websockets.connect(page['webSocketDebuggerUrl'],max_size=30000000)as ws:
  async def cmd(method,params):
   nonlocal i
   i+=1;ident=i;await ws.send(json.dumps(dict(id=i,method=method,params=params)))
   while True:
    r=json.loads(await ws.recv())
    if r.get('method')=='Runtime.exceptionThrown':exceptions.append(r)
    if r.get('id')==ident:return r
  async def ev(expr):
   r=await cmd('Runtime.evaluate',dict(expression=expr,returnByValue=True));assert not r.get('result',{}).get('exceptionDetails'),r;return r['result']['result'].get('value')
  await cmd('Runtime.enable',{});await cmd('Emulation.setDeviceMetricsOverride',dict(width=1500,height=1300,deviceScaleFactor=1,mobile=False));structure=await ev('({webgl:!!gl,glerror:gl.getError(),views:S.frames.length,bodyKeys:Object.keys(S.bodies),GT_faces:S.GT.F.length,full_source_faces:S.frames.reduce((n,f)=>n+S.meshes[f.id].F.length,0)})');assert structure['webgl']and structure['glerror']==0
  tested=[]
  if hero:
   assert structure['views']>=2 and structure['full_source_faces']>10000 and structure['GT_faces']==0
   for method in ['M0','BODY_A0','BODY_A1','BODY_A2','ICP']:
    await ev('ms.value='+json.dumps(method)+';ss.value="after";draw();true');info=await ev('document.querySelector("#info").textContent');assert 'shown: '+str(structure['views'])+'/'+str(structure['views'])in info,info[:200];assert await ev('gl.getError()')==0;tested.append(method)
   await ev("document.querySelector('#video004').checked=false;draw();true");count=await ev("S.frames.filter(f=>f.video==='005').length");assert 'shown: '+str(count)+'/'+str(structure['views'])in await ev('document.querySelector("#info").textContent')
   await ev("document.querySelector('#video004').checked=true;checks[S.frames[0].id].checked=false;draw();true");assert 'shown: '+str(structure['views']-1)+'/'+str(structure['views'])in await ev('document.querySelector("#info").textContent')
   await ev("checks[S.frames[0].id].checked=true;ms.value='BODY_A2';draw();true")
  else:
   assert structure['GT_faces']>100 and 'A0'in structure['bodyKeys']
   for arm in structure['bodyKeys']:
    await ev('as.value='+json.dumps(arm)+';draw();true')
    for retry in range(150):
     ready=await ev('!!MF_CASES["SHAPE_"+as.value]')
     if ready:break
     await asyncio.sleep(.02)
    assert ready;assert await ev('gl.getError()')==0;tested.append(arm)
   await ev("document.querySelector('#showgt').checked=false;draw();true");a=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data'];await ev("document.querySelector('#showgt').checked=true;draw();true");b=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data'];assert a!=b,'GT toggle does not affect actual geometry rendering'
  assert not exceptions,exceptions
  shot=await cmd('Page.captureScreenshot',dict(format='png'));(TD/'evidence'/('BROWSER_'+path.parent.name+'.png')).write_bytes(base64.b64decode(shot['result']['data']))
  result=dict(path=str(path),status='PASS',kind='FULL_HERO_MESH'if hero else'ACTUAL_ALIGNED_GT_COPIES',structure=structure,states_tested=tested,JavaScript_exceptions=0);print(json.dumps(result),flush=True)
  try:await cmd('Page.close',{})
  except websockets.exceptions.ConnectionClosed:pass
  return result
async def main():
 results=[]
 for folder in sorted(VIS.iterdir()):
  if(folder/'multisurface_3d.html').is_file():results.append(await check(folder/'multisurface_3d.html',folder.name.endswith('_HERO')))
 receipt=dict(status='PASS',pages=len(results),offline=True,results=results);(TD/'evidence/OFFLINE_BROWSER_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print('ALL OFFLINE MESH PAGES PASS',len(results))
asyncio.run(main())
