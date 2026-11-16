"""Read-only local inventory and a narrowly bounded, frozen HTTP-cache deletion plan."""
from pathlib import Path
import csv, hashlib, json, os, shutil, subprocess, time

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "maintenance/storage"
BASE = "fa649fa1cf20b111bfdb8489e8af20ba90339bba"
ASSET = Path("/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001")
PROTECTED = (Path("/home/liu/polyp_research"), Path("/home/liu/new-polyp-dxy"))

def digest(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def table(name, rows, fields=None):
    keys = fields or list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)

def project_processes(root):
    result = []
    own = os.getpid()
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == own:
            continue
        try:
            cwd = Path(os.readlink(p / "cwd"))
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            if (cwd == root or root in cwd.parents or str(root) + "/" in cmd) and "audit_storage.py" not in cmd:
                result.append({"pid": int(p.name), "cwd": str(cwd), "command": cmd[:220]})
        except OSError:
            pass
    return result

def inventory():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "PHASE0_FREEZE.json").exists():
        raise RuntimeError("Existing phase-0 freeze is immutable; use a separate audit task")
    remote = dict((line.split()[1].removeprefix("refs/heads/"), line.split()[0])
                  for line in subprocess.check_output(
                      ["git", "ls-remote", "--heads", "https://github.com/zheng1524/ring-first-3d.git"],
                      text=True).splitlines())
    rows = []
    environments = []
    preserve = []
    for r in sorted(Path("/home/liu").glob("ring_first_3d*")):
        if not (r / ".git").exists() or r.is_symlink():
            continue
        head = git(r, "rev-parse", "HEAD")
        branch = git(r, "branch", "--show-current")
        tracked = set(git(r, "ls-files").splitlines())
        files = []
        links = 0
        for dp, dn, fn in os.walk(r, followlinks=False):
            dn[:] = [n for n in dn if n != ".git" and not (Path(dp) / n).is_symlink()]
            for n in fn:
                p = Path(dp) / n
                if p.is_symlink():
                    links += 1
                    continue
                files.append(p)
                if n == "pyvenv.cfg" or n == "activate" and p.parent.name == "bin":
                    environments.append({"root": str(r), "marker": str(p), "kind": "venv"})
        untracked = [p for p in files if str(p.relative_to(r)) not in tracked]
        status = git(r, "status", "--porcelain", "--untracked-files=normal")
        active = project_processes(r)
        classification = "ACTIVE" if r == REPO or active or r.name == "ring_first_3d_e4_sdf_localization" else (
            "UNIQUE_RESEARCH_ASSET" if untracked or status else "UNCERTAIN")
        common = Path(git(r, "rev-parse", "--git-common-dir"))
        if not common.is_absolute():
            common = (r / common).resolve()
        rows.append(dict(PATH=str(r), REALPATH=str(r.resolve()),
            GIT_KIND="linked_worktree" if (r / ".git").is_file() else "primary_checkout",
            COMMON_GIT_DIR=str(common), HEAD=head, BRANCH=branch,
            REMOTE=git(r, "remote", "get-url", "origin"), REMOTE_TIP=remote.get(branch, "MISSING"),
            HEAD_EQUALS_REMOTE=head == remote.get(branch), STATUS_LINES=len(status.splitlines()),
            STATUS_SHA256=hashlib.sha256(status.encode()).hexdigest(),
            LOCAL_COMMITS_NOT_REMOTE_TRACKED=len(git(r, "log", "--format=%H", "--branches", "--not", "--remotes").splitlines()),
            STASH_COUNT=len(git(r, "stash", "list").splitlines()),
            TOTAL_FILES=len(files), UNTRACKED_INCLUDING_IGNORED=len(untracked), SYMLINKS_NOT_FOLLOWED=links,
            LOGICAL_BYTES=sum(p.stat().st_size for p in files),
            ALLOCATED_BYTES=sum(p.stat().st_blocks * 512 for p in files),
            ACTIVE_PIDS=json.dumps(active, ensure_ascii=False), CLASSIFICATION=classification,
            UNIQUE_ASSET_BACKUP="NOT_PROVEN; preserved in place",
            REFERENCES="Historical absolute paths and shared runtime dependencies retained",
            RECOVERY="Tracked Git files recoverable; ignored/unique data not proven backed up",
            DELETE_ELIGIBLE=False))
        for p in files:
            if p.suffix in {".ckpt", ".pt", ".pth", ".safetensors"}:
                preserve.append(dict(PATH=str(p), REALPATH=str(p.resolve()), BYTES=p.stat().st_size,
                    SHA256=digest(p), ROLE="historical checkpoint/weight; preserve failure and training state",
                    RETAINED_COPY=str(p), RECOVERY="in-place original; no external backup claimed"))
        for p in r.glob("experiments/*/runtime/packages"):
            environments.append({"root": str(r), "marker": str(p), "kind": "task-local site-packages, not an unused venv"})
    # Keep original interactive GLBs; browser cache is a disposable HTTP response copy.
    for p in sorted((ASSET / "local_results/interactive").glob("*")):
        if p.is_file() and p.suffix in {".glb", ".html", ".js"}:
            preserve.append(dict(PATH=str(p), REALPATH=str(p.resolve()), BYTES=p.stat().st_size,
                SHA256=digest(p), ROLE="source interactive asset; browser reload repopulates cache",
                RETAINED_COPY=str(p), RECOVERY="serve original interactive gallery and reload"))
    delete = []
    for cache in sorted((ASSET / "runtime").glob("chrome*/Default/Cache/Cache_Data")):
        if cache.is_symlink():
            raise RuntimeError("Cache symlink is not eligible")
        for p in sorted(cache.rglob("*")):
            if not p.is_file() or p.is_symlink():
                continue
            s = p.stat()
            delete.append(dict(PATH=str(p), REALPATH=str(p.resolve()), SYMLINK=False,
                BYTES=s.st_size, ALLOCATED_BYTES=s.st_blocks * 512, SHA256=digest(p),
                MTIME_NS=s.st_mtime_ns, INODE=s.st_ino, DEVICE=s.st_dev,
                TASK="TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001",
                CLASSIFICATION="VERIFIED_REDUNDANT", KIND="regenerable Chromium HTTP response cache",
                UNIQUENESS="Not source/model/evidence; response cache of preserved interactive gallery",
                RETAINED_COPY=str(ASSET / "local_results/interactive"),
                RECOVERY="Reload preserved local interactive HTML/GLB in browser; byte-identical cache index not promised",
                REASON="Expired experiment browser profile cache, no running Chromium task; original assets retained"))
    # Search only project textual source/reports for exact candidate paths and cache filenames.
    # A runtime user-data-dir reference is allowed; a direct cache-file dependency is not.
    needles = {str(p["PATH"]) for p in delete} | {Path(p["PATH"]).name for p in delete if len(Path(p["PATH"]).name) > 12}
    hits = []
    for rr in rows:
        r = Path(rr["PATH"])
        for dp, dn, fn in os.walk(r, followlinks=False):
            dn[:] = [n for n in dn if n not in {".git", "runtime"} and not (Path(dp) / n).is_symlink()]
            for n in fn:
                p = Path(dp) / n
                if p.is_symlink() or p.suffix not in {".py", ".md", ".html", ".js"} or p.stat().st_size > 2_000_000:
                    continue
                t = p.read_text(errors="replace")
                for word in needles:
                    if word in t:
                        hits.append({"file": str(p), "candidate": word})
    if hits:
        raise RuntimeError("Direct cache references require review: " + repr(hits[:5]))
    table("PROJECT_WORKTREE_AUDIT.csv", rows)
    table("DELETE_MANIFEST.csv", delete)
    table("PRESERVED_ASSETS.csv", preserve)
    dump("ENVIRONMENT_INVENTORY.json", environments)
    dump("REFERENCE_AUDIT.json", {"direct_cache_file_hits": hits,
        "scope": "All allowed project roots: py/md/html/js <=2MB, no symlink traversal or runtime scan",
        "limitation": "Opaque/binary references not exhaustively inferable; deletion limited to browser cache, not checkouts"})
    dump("PHASE0_FREEZE.json", dict(baseline=BASE, epoch=time.time(),
        disk=dict(zip(["total", "used", "free"], shutil.disk_usage(REPO))),
        project_count=len(rows), deletion_files=len(delete),
        candidate_logical_bytes=sum(x["BYTES"] for x in delete),
        candidate_allocated_bytes=sum(x["ALLOCATED_BYTES"] for x in delete),
        manifests={n: digest(OUT / n) for n in ["DELETE_MANIFEST.csv", "PRESERVED_ASSETS.csv", "PROJECT_WORKTREE_AUDIT.csv"]},
        protected=[str(p) for p in PROTECTED],
        shared_objects="No GC or history/ref deletion; dangling 3da9852b25fd82f4f158299a264d9a433aa572da preserved in place"))
    os.chmod(OUT / "DELETE_MANIFEST.csv", 0o444)
    print(json.dumps({"projects": len(rows), "cache_files": len(delete),
        "cache_allocated": sum(x["ALLOCATED_BYTES"] for x in delete), "preserved": len(preserve)}))

if __name__ == "__main__":
    inventory()
