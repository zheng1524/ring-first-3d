"""Execute one exact-file audit release under the shared maintenance lock."""

import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import stat
import subprocess
import sys


ROOT = pathlib.Path('/home/liu/ring_first_3d_workspace')
HANDOFF = ROOT / 'runs/v6_r1_split_handoff_001'


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    temp = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    try:
        with open(temp, 'w') as target:
            json.dump(value, target, ensure_ascii=False, indent=2)
            target.write('\n')
            target.flush()
            os.fsync(target.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def append_progress(path, index, result):
    with open(path, 'a') as target:
        target.write(json.dumps({'index': index, 'result': result}, ensure_ascii=False) + '\n')
        target.flush()
        os.fsync(target.fileno())


def load_progress(path):
    if not path.exists():
        return {}
    updates = {}
    with open(path) as source:
        for line in source:
            record = json.loads(line)
            updates[record['index']] = record['result']
    return updates


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def free_bytes():
    info = os.statvfs(ROOT)
    return info.f_bavail * info.f_frsize


def is_protected(path, protected_paths):
    guards = protected_paths if isinstance(protected_paths, set) else set(protected_paths)
    current = path
    while current != '/':
        if current in guards:
            return True
        current = os.path.dirname(current)
    return '/' in guards


def recoverable_blocks(info):
    return info.st_blocks * 512 if info.st_nlink == 1 else 0


def check_item(item, protected_paths, deletion_paths):
    path = item.get('path', '')
    result = {'path': path, 'status': 'SKIPPED', 'size_bytes': item.get('size_bytes'),
              'sha256': item.get('sha256')}
    candidate = pathlib.Path(path)
    if not candidate.is_absolute() or str(candidate) != path:
        result['reason'] = 'non-absolute or non-normalized path'
        return result
    if item.get('file_type') != 'regular' or not item.get('realpath'):
        result['reason'] = 'release does not name an exact regular file and realpath'
        return result
    if is_protected(path, protected_paths) or is_protected(item['realpath'], protected_paths):
        result['reason'] = 'protected path or target'
        return result
    if os.path.realpath(path) != item['realpath']:
        result['reason'] = 'realpath changed'
        return result
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        result.update(status='ALREADY_ABSENT', reason='file already absent; no recovery counted')
        return result
    if not stat.S_ISREG(info.st_mode):
        result['reason'] = 'not a regular non-symlink file'
        return result
    if info.st_size != item.get('size_bytes') or sha256(path) != item.get('sha256'):
        result['reason'] = 'size or SHA256 changed'
        return result
    retained_at = item.get('retained_at')
    if retained_at:
        retained = pathlib.Path(retained_at)
        if retained_at in deletion_paths or not retained.is_file() or retained.is_symlink():
            result['reason'] = 'retained copy missing, linked, or in deletion set'
            return result
        expected = item.get('retained_sha256')
        if expected != item['sha256'] or sha256(retained) != expected:
            result['reason'] = 'retained copy SHA256 mismatch'
            return result
        if not item.get('consumer_load_evidence'):
            result['reason'] = 'retained copy has no consumer load evidence'
            return result
    result.update(status='VERIFIED', inode=info.st_ino, device=info.st_dev,
                  links_before=info.st_nlink, allocated_bytes=info.st_blocks * 512)
    return result


def proc_open_paths():
    opened = set()
    with os.scandir('/proc') as processes:
        for process in processes:
            if not process.name.isdigit():
                continue
            try:
                with os.scandir(process.path + '/fd') as descriptors:
                    for descriptor in descriptors:
                        try:
                            target = os.readlink(descriptor.path)
                        except (OSError, PermissionError):
                            continue
                        if target.startswith('/'):
                            opened.add(target)
            except (OSError, PermissionError):
                continue
    return opened


def execute(batch_id):
    release_path = HANDOFF / 'releases' / (batch_id + '.json')
    receipt_path = HANDOFF / 'receipts' / (batch_id + '.json')
    progress_path = HANDOFF / 'receipts' / (batch_id + '.progress.ndjson')
    protected_path = HANDOFF / 'PROTECTED_ASSETS.json'
    cancel_path = HANDOFF / 'cancellations' / (batch_id + '.json')
    with (HANDOFF / 'maintenance.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        release = json.loads(release_path.read_text())
        protected = json.loads(protected_path.read_text())
        release_sha = sha256(release_path)
        protected_sha = sha256(protected_path)
        if release.get('batch_id') != batch_id or release.get('status') != 'READY':
            raise RuntimeError('release identity or READY status mismatch')
        if release.get('protected_manifest_sha256') != protected_sha:
            raise RuntimeError('protected manifest changed; regenerate release')
        items = release.get('items', [])
        if not items or len({x.get('path') for x in items}) != len(items):
            raise RuntimeError('empty or duplicate release paths')
        guards = {str(pathlib.Path(x['real_path'])) for x in protected['paths']}
        paths = {x['path'] for x in items}
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt.get('status') in ('COMPLETE', 'CANCELLED'):
                print('EXISTING_TERMINAL_RECEIPT', receipt_path)
                return
            if receipt.get('release_sha256') != release_sha:
                raise RuntimeError('RUNNING receipt has different release SHA')
            if receipt.get('status') != 'RUNNING':
                raise RuntimeError('unknown existing receipt state')
            for index, result in load_progress(progress_path).items():
                receipt['items'][index] = result
        else:
            results = [check_item(x, guards, paths) for x in items]
            receipt = {'batch_id': batch_id, 'status': 'RUNNING',
                       'release_sha256': release_sha,
                       'protected_manifest_sha256': protected_sha,
                       'evidence_ref': release.get('evidence_ref'),
                       'started_at': timestamp(), 'items': results,
                       'space_before_available_bytes': free_bytes(),
                       'df_before': subprocess.check_output(['df', '-B1', str(ROOT)], text=True).strip()}
            atomic_json(receipt_path, receipt)
        if cancel_path.exists():
            cancellation = json.loads(cancel_path.read_text())
            if cancellation.get('release_sha256') != release_sha:
                raise RuntimeError('cancellation references a different release')
            receipt.update(status='CANCELLED', completed_at=timestamp())
            atomic_json(receipt_path, receipt)
            print('CANCELLED', batch_id)
            return
        opened = None
        for index, item in enumerate(items):
            previous = receipt['items'][index]
            if previous['status'] != 'VERIFIED':
                continue
            path = item['path']
            try:
                if index % 100 == 0 or opened is None:
                    opened = proc_open_paths()
                fresh = check_item(item, guards, paths)
                if fresh['status'] != 'VERIFIED':
                    previous.update(status=fresh['status'], reason=fresh.get('reason'))
                elif path in opened:
                    previous.update(status='SKIPPED', reason='open according to lsof')
                else:
                    info = os.lstat(path)
                    if (info.st_ino, info.st_dev) != (fresh['inode'], fresh['device']):
                        previous.update(status='SKIPPED', reason='inode changed after verification')
                    else:
                        os.unlink(path)
                        previous.update(status='DELETED', deleted_at=timestamp(),
                                        logical_deleted_bytes=info.st_size,
                                        allocated_bytes_released_estimate=recoverable_blocks(info),
                                        links_before=info.st_nlink, inode=info.st_ino,
                                        device=info.st_dev)
            except FileNotFoundError:
                previous.update(status='ALREADY_ABSENT', reason='vanished before unlink')
            except Exception as error:
                previous.update(status='SKIPPED', reason=repr(error))
            append_progress(progress_path, index, previous)
        checks = {}
        for anchor in [ROOT / '.git', ROOT / 'runs/v6_full_run_001',
                       ROOT / 'runs/v6_r1_split_handoff_001',
                       pathlib.Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1/weights/mvsanywhere_hero_full.ckpt')]:
            checks[str(anchor)] = anchor.exists() and os.access(anchor, os.R_OK)
        counts = dict(collections.Counter(x['status'] for x in receipt['items']))
        logical = sum(x.get('logical_deleted_bytes', 0) for x in receipt['items'])
        allocated = sum(x.get('allocated_bytes_released_estimate', 0) for x in receipt['items'])
        after = free_bytes()
        receipt.update(status='COMPLETE', completed_at=timestamp(),
                       health={'protected_anchor_readable': checks},
                       counts=counts, logical_deleted_bytes=logical,
                       attributable_allocated_recovery_estimate_bytes=allocated,
                       space_after_available_bytes=after,
                       df_after=subprocess.check_output(['df', '-B1', str(ROOT)], text=True).strip(),
                       df_available_delta_bytes=after-receipt['space_before_available_bytes'],
                       concurrent_write_note='df delta is net change and may include other filesystem writes')
        atomic_json(receipt_path, receipt)
        with (HANDOFF / 'CLEANUP_REPORT.md').open('a') as report:
            report.write('\n## ' + batch_id + ' (' + receipt['completed_at'] + ')\n\n')
            report.write('- Audit evidence: `' + str(release.get('evidence_ref')) + '`\n')
            report.write('- Status: COMPLETE; counts: `' + json.dumps(counts, ensure_ascii=False) + '`\n')
            report.write('- Logical deleted bytes: ' + str(logical) + '\n')
            report.write('- Attributable allocated block recovery: ' + str(allocated) + ' bytes (last-link `st_blocks * 512`).\n')
            report.write('- df available before/after/delta: ' + str(receipt['space_before_available_bytes']) + ' / ' + str(after) + ' / ' + str(after-receipt['space_before_available_bytes']) + ' bytes; concurrent writes may affect net delta.\n')
            report.write('- Receipt: `receipts/' + batch_id + '.json`; release SHA256 `' + release_sha + '`; protected SHA256 `' + protected_sha + '`.\n')
            report.flush()
            os.fsync(report.fileno())
        print(json.dumps({'batch_id': batch_id, 'counts': counts,
                          'logical_deleted_bytes': logical,
                          'allocated_recovery_estimate_bytes': allocated,
                          'df_delta_bytes': after-receipt['space_before_available_bytes'],
                          'free_bytes': after}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('batch_id')
    args = parser.parse_args()
    execute(args.batch_id)
