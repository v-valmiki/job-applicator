"""Resume versioning: track files in resumes/, archive every accepted version (append-only).

Manifest: <local>/resume_manifest.json  {filename: {sha256, size, accepted_at[, removed_at]}}
Archive:  resumes/archive/<sha256[:8]>-<filename>
CLI: resumes.py status | accept | find <sha_prefix>   (status exits 10 if anything changed)
"""
import hashlib, json, os, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"README.md", ".gitignore"}


def resumes_dir():
    return Path(os.environ.get("JOB_APPLICATOR_RESUMES_DIR") or ROOT / "resumes")


def local_dir():
    d = Path(os.environ.get("JOB_APPLICATOR_LOCAL_DIR") or ROOT / "local")
    d.mkdir(parents=True, exist_ok=True)
    return d


def manifest_path():
    return local_dir() / "resume_manifest.json"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest():
    try:
        return json.loads(manifest_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def current_files():
    d = resumes_dir()
    if not d.is_dir():
        return {}
    return {p.name: p for p in sorted(d.iterdir())
            if p.is_file() and p.name not in SKIP and not p.name.startswith(".")}


def status():
    man, cur = load_manifest(), current_files()
    out = {"new": [], "changed": [], "removed": [], "unchanged": []}
    for name, p in cur.items():
        e = man.get(name)
        if not e or e.get("removed_at"):
            out["new"].append(name)
        elif e["sha256"] != sha256_file(p):
            out["changed"].append(name)
        else:
            out["unchanged"].append(name)
    out["removed"] = [n for n, e in sorted(man.items()) if n not in cur and not e.get("removed_at")]
    return out


def archive_file(path):
    """Copy a file into the archive (no-op if that exact version is there). Returns (sha256, archive_path)."""
    path = Path(path)
    sha = sha256_file(path)
    dest = resumes_dir() / "archive" / f"{sha[:8]}-{path.name}"
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return sha, dest


def accept():
    st = status()
    man, cur, t = load_manifest(), current_files(), now()
    for name in st["new"] + st["changed"]:
        sha, _ = archive_file(cur[name])
        man[name] = {"sha256": sha, "size": cur[name].stat().st_size, "accepted_at": t}
    for name in st["removed"]:
        man[name]["removed_at"] = t
    manifest_path().write_text(json.dumps(man, indent=2, sort_keys=True), encoding="utf-8")
    return st


def find_version(sha_prefix):
    """Archive path for a hash prefix (>= 4 hex chars), or None."""
    sha_prefix = (sha_prefix or "").lower()
    if len(sha_prefix) < 4:
        return None
    arch = resumes_dir() / "archive"
    if not arch.is_dir():
        return None
    short = sha_prefix[:8]
    for p in sorted(arch.iterdir()):
        if p.is_file() and p.name.startswith(short + "-"):
            if len(sha_prefix) <= 8 or sha256_file(p).startswith(sha_prefix):
                return p
    return None


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    cmd = a[0] if a else ""
    if cmd == "status":
        st = status()
        print(json.dumps(st, indent=2))
        return 10 if st["new"] or st["changed"] or st["removed"] else 0
    if cmd == "accept":
        print(json.dumps(accept(), indent=2))
        return 0
    if cmd == "find" and len(a) == 2:
        p = find_version(a[1])
        print(p if p else "not found")
        return 0 if p else 1
    print("usage: resumes.py status | accept | find <sha_prefix>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
