"""Compose existing immutable scientific publication; require both recovery cases."""
from .structured_artifacts import enhance as existing_publish
from .contracts import require
from ..contracts.identities import sha256
def enhance(root,t,state,latest,pending):
    existing_publish(root,t,state,latest,pending)
    state['recovery_files']=state.pop('structured_files')
    if 'G4_visualize'not in latest:
        p=pending/'visualization/index.html';p.write_text(p.read_text().replace('Structured body pilot','Rejected-candidate growth recovery'))
def validate(root,state):
    files=state.get('recovery_files',{})
    for name,rec in files.items():require((root/name).is_file()and sha256(root/name)==rec['sha256'],'ARTIFACT_MISSING',name)
    if any('-G4_visualize-'in x['path']for x in state['attempts']):
        required={f'visualization/figures/{c}_{figure}.png'for c in ['G01','G03']for figure in ['FRONT','BACK','LEFT','RIGHT','ROOT','CENTERLINE_SECTIONS','TRIANGLE_SECTIONS','GT_EVALUATION']}
        require(required|{'visualization/FAILURE_REGISTRY.json'}<=set(files),'ARTIFACT_MISSING','Both actual candidates, roots, arc lengths and failures')
