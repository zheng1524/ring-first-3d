"""Planned narrowly scoped resume for a cap-only implementation repair.
Adopts only same-task frozen non-cap predictions; all identities are rechecked.
"""
from pathlib import Path
import json,shutil
import numpy as np
from ring_first_3d.policy.contracts import require
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.synthetic.io import save_json


def adoption(task,attempt,stage,case=None):
    repair=task['structural'].get('engineering_repair')
    if not repair:return False
    cache=json.loads(Path(task['structural']['assets']['repair_cache']['path']).read_text())
    key=stage+(':'+case if case else '')
    require(key in cache['entries'],'RESUME_IDENTITY','Only explicitly frozen same-task stages may be adopted: '+key)
    entry=cache['entries'][key]
    # Every adopted BODY was computed on the branch on which the repair is a no-op.
    if stage!='G2_C0_evaluate':
        initial=np.load(entry['initial']['path'])
        require(not initial['inferred_base_faces'].any(),'CAP_REPAIR_RESUME','Cap-bearing inputs must be rerun with the corrected updater')
    for rec in entry['files']:
        src=Path(rec['path']);require(src.is_file() and sha256(src)==rec['sha256'],'SOURCE_SHA',str(src));dst=attempt/rec['target_relative'];dst.parent.mkdir(parents=True,exist_ok=True);require(not dst.exists(),'OUTPUT_EXISTS','Never overwrite previous attempt');shutil.copyfile(src,dst)
    save_json(attempt/((case+'/' if case else '')+'ADOPTED_FROZEN_NONCAP.json'),dict(stage=stage,case=case,original_run=cache['source_run'],
                original_freeze_sha256=cache['source_freeze_sha256'],repair='Restore original cap feasible proposal only',
                noncap_branch_byte_identical=True,parameters_unchanged=True,same_task=True,GT_did_not_select_prediction=True))
    return True
