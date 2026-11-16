"""Offline full-triangle scene inspection in three explicitly separate frames."""
import json
import numpy as np


def create_scene(attempt,manifest,body):
    scenes=[]
    for video in ['004','005']:
        rows=[r for r in manifest['rows']if r['video']==video];ring=np.load(rows[0]['ring']['path'])
        cameras=[]
        for r in rows:
            T=np.asarray(r['Camera_to_Ring']);K=np.asarray(r['K'])
            uv=np.array([[0,0,1],[639,0,1],[639,359,1],[0,359,1]])
            corners=(uv@np.linalg.inv(K).T*4)@T[:3,:3].T+T[:3,3]
            cameras.append(dict(id=r['view_id'],role=r['role'],center=T[:3,3].tolist(),corners=corners.tolist(),pose_sha256=r['pose_origin']['sha256']))
        scenes.append(dict(name=f'Video {video}: native Ring frame ONLY',V=ring['V'].tolist(),F=ring['F'].tolist(),cameras=cameras,source=rows[0]['ring']['sha256'],kind='Ring',note='Full R10 CAD + original native cameras. No common-world certification or fitted Body.'))
    scenes.append(dict(name='G01 original Blender: AUTHOR frame ONLY',V=body['V'].tolist(),F=body['F'].tolist(),cameras=[],kind='GT author mesh',source='original Blender fresh evaluated mesh',note='Genuine GT geometry in mm. Deployment transform to either Ring is NOT_EVALUABLE; this is not an initialized prediction.'))
    # Inline JSON needs no fetch, CDN, browser server or web connection.
    data=json.dumps(scenes,separators=(',',':')).replace('</','<\\/')
    page='''<!doctype html><meta charset="utf-8"><title>G01 authentic scene audit</title>
<style>body{font:16px system-ui;margin:24px;background:#101b2a;color:#e6edf7}canvas{background:#182639;width:100%;max-width:1100px;touch-action:none}select,button{padding:8px}pre{white-space:pre-wrap}a{color:#90c7ff}</style>
<h1>G0 full mesh / native camera scene audit</h1><p>Fixed millimetre scale; each dropdown is a separate source frame. Never overlay 004, 005 and Blender as an authenticated common world. Drag to rotate; reset restores identical view angles.</p>
<select id="choice"></select> <button id="reset">Reset fixed view</button><p id="note"></p><canvas id="view" width="1100" height="700"></canvas><pre id="info"></pre>
<script>const scenes=__DATA__;const select=document.querySelector('#choice'),can=document.querySelector('#view'),ctx=can.getContext('2d');let yaw=.6,pitch=.5;
scenes.forEach((s,i)=>select.add(new Option(s.name,i)));
function point(p){let x=Math.cos(yaw)*p[0]+Math.sin(yaw)*p[2],z=-Math.sin(yaw)*p[0]+Math.cos(yaw)*p[2];return [550+12*x,370-12*(Math.cos(pitch)*p[1]-Math.sin(pitch)*z),Math.sin(pitch)*p[1]+Math.cos(pitch)*z]}
function line(a,b,color){a=point(a);b=point(b);ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke()}
function draw(){let s=scenes[+select.value];ctx.clearRect(0,0,1100,700);let v=s.V.map(point);let order=s.F.map(f=>({f,z:(v[f[0]][2]+v[f[1]][2]+v[f[2]][2])/3})).sort((a,b)=>a.z-b.z);
order.forEach(({f,z})=>{ctx.beginPath();ctx.moveTo(v[f[0]][0],v[f[0]][1]);ctx.lineTo(v[f[1]][0],v[f[1]][1]);ctx.lineTo(v[f[2]][0],v[f[2]][1]);ctx.closePath();ctx.fillStyle=s.kind==='Ring'?'#c3ad62':'#a9689d';ctx.fill();});
s.cameras.forEach(c=>{const col=c.role==='FIT'?'#5ad7f7':'#ff8765';c.corners.forEach((p,i)=>{line(c.center,p,col);line(p,c.corners[(i+1)%4],col)});let p=point(c.center);ctx.fillStyle=col;ctx.fillText(c.id,p[0],p[1]);});
[[[5,0,0],'#ff7474','X'],[[0,5,0],'#82e99b','Y'],[[0,0,5],'#91b8ff','Z']].forEach(([p,col,n])=>{line([0,0,0],p,col);let t=point(p);ctx.fillStyle=col;ctx.fillText(n+' 5 mm',t[0],t[1]);});
ctx.strokeStyle='white';ctx.beginPath();ctx.moveTo(30,650);ctx.lineTo(150,650);ctx.stroke();ctx.fillStyle='white';ctx.fillText('10 mm (12 px/mm, orthographic)',30,675);
document.querySelector('#note').textContent=s.note;document.querySelector('#info').textContent=s.name+' | '+s.V.length+' vertices / '+s.F.length+' full triangles | '+s.cameras.length+' cameras\nSource: '+s.source+'\nNo perturbation, no Body fitting, no mesh registration has been performed.';}
select.onchange=draw;document.querySelector('#reset').onclick=()=>{yaw=.6;pitch=.5;draw()};let last=null;can.onpointerdown=e=>{last=[e.clientX,e.clientY];can.setPointerCapture(e.pointerId)};can.onpointerup=()=>last=null;can.onpointermove=e=>{if(last){yaw+=(e.clientX-last[0])*.008;pitch+=(e.clientY-last[1])*.008;last=[e.clientX,e.clientY];draw()}};draw();</script>'''
    # Escape JS newline in the template, preserving actual HTML newlines.
    page=page.replace("+' cameras\nSource: '","+' cameras\\nSource: '").replace("+'\nNo perturbation", "+'\\nNo perturbation")
    (attempt/'scene.html').write_text(page.replace('__DATA__',data))
