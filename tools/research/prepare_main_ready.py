"""Materialize reviewed lightweight files on a separate branch based on main.

Never merges history or writes the protected repositories. Caller creates worktree.
"""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, quote, urlsplit

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destination",type=Path,required=True)
    p.add_argument("--snapshot",required=True)
    a=p.parse_args();dest=a.destination.resolve()
    if dest!=Path("/home/liu/ring_first_3d_harness_main_ready"):
        raise ValueError("Only this task's explicit new main-ready destination is allowed")
    git=lambda *args:subprocess.check_output(["git","-C",str(dest),*args],text=True).strip()
    if not git("branch","--show-current").startswith("release/") or git("status","--porcelain"):
        raise ValueError("Clean independent release branch required")
    if git("rev-parse","HEAD")!="02dee8092dce9f89d050bccca35aa51768988645":
        raise ValueError("main base changed; re-audit release contents")
    names=["docs/PROJECT_HOME.md","docs/RESEARCH_EXECUTION_HARNESS.md","pyproject.toml",".gitattributes"]
    for folder in ["docs/registry","docs/architecture","src/ring_first_3d","tests"]:
        names += [str(x.relative_to(ROOT)) for x in sorted((ROOT/folder).rglob("*"))if x.is_file() and "__pycache__" not in x.parts]
    names += ["tools/research/"+s for s in ["_bootstrap.py","preflight.py","smoke.py","validate_contracts.py","audit_reuse.py","run.sh","check_payload.py","frozen_fixture.json","frozen_reference.json","support_fixture.json","render_evidence.py"]]
    task="experiments/TASK-RESEARCH-HARNESS-STORAGE-001/"
    names += [task+s for s in ["TECHNICAL_REPORT.md","REPRODUCE.md","TEST_RESULTS.json","SMOKE_AFTER.json","figures/REAL_SMOKE_EVIDENCE.png"]]
    included=set(names)|{"README.md",".gitignore"};rewrites=[]
    pattern=re.compile(r"(!?\[[^\]\n]*\]\()([^\s)]+)(\))")
    for name in names:
        raw=subprocess.check_output(["git","-C",str(ROOT),"show",a.snapshot+":"+name])
        if name.endswith(".md"):
            def replace(m):
                href=m[2].strip("<>");u=urlsplit(href)
                if u.scheme or href.startswith(("#","/")):return m[0]
                target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(u.path)))
                if target in included:return m[0]
                subprocess.run(["git","-C",str(ROOT),"cat-file","-e",a.snapshot+":"+target],check=True,capture_output=True)
                link="https://github.com/zheng1524/ring-first-3d/blob/"+a.snapshot+"/"+quote(target)
                if u.fragment:link+="#"+u.fragment
                rewrites.append(dict(document=name,original=href,pinned=link))
                return m[1]+link+m[3]
            raw=pattern.sub(replace,raw.decode()).encode()
        output=dest/name
        if output.exists():raise FileExistsError("Unexpected existing release file: "+name)
        output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(raw)
    readme=dest/"README.md"
    readme.write_text("# Research engineering entry\n\n本发布分支基于 main，仅添加技术注册表、文档和最小共享 Harness。[从 PROJECT_HOME 开始](docs/PROJECT_HOME.md)，先运行 [Preflight / Smoke](docs/RESEARCH_EXECUTION_HARNESS.md)。历史科学状态未晋升；数据/环境/原算法源对象为明确外部依赖。下方保留原 main 的历史 bootstrap 说明。\n\n"+readme.read_text())
    ignore=dest/".gitignore";text=ignore.read_text();extra="experiments/TASK-RESEARCH-HARNESS-STORAGE-001/local_only/"
    ignore.write_text(text.rstrip()+"\n"+extra+"\n")
    manifest=dict(main_base=git("rev-parse","HEAD"),source_snapshot=a.snapshot,whole_history_merged=False,
                  files={name:hashlib.sha256((dest/name).read_bytes()).hexdigest()for name in sorted(included)},
                  historical_link_rewrites=rewrites,
                  exclusions="No historical experiment tree, raw data, weights, environment, full caches or destructive storage scripts")
    (dest/"docs/registry/MAIN_READY_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(dict(files=len(included),pinned_historical_links=len(rewrites),bytes=sum((dest/n).stat().st_size for n in included))))


if __name__=="__main__":main()
