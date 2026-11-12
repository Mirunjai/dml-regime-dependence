"""Checksum manifest of gitignored raw output directories (so an auditor can verify regenerated/handed-over raw files)."""
import hashlib, json, sys
from pathlib import Path

def dir_digest(d):
    files = sorted(p for p in Path(d).rglob("*") if p.is_file())
    h = hashlib.sha256()
    for p in files:
        h.update(str(p.relative_to(d)).encode()); h.update(hashlib.sha256(p.read_bytes()).digest())
    return {"files": len(files), "bytes": sum(p.stat().st_size for p in files), "sha256": h.hexdigest()}

if __name__ == "__main__":
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    res = {}
    for sess in sorted(root.glob("mirun_session*")):
        for d in sorted(p for p in sess.iterdir() if p.is_dir()):
            res[str(d)] = dir_digest(d)
    out.write_text(json.dumps(res, indent=1)); print(len(res), "directories")
