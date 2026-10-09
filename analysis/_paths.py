"""
Path resolution for the analysis scripts.

The scripts were written against a local working tree and are published in a
flatter repository layout. This module locates the data wherever it actually
is, so the same script runs in both without editing.

Resolution order for the data root:
  1. $RRD_DATA_ROOT, if set
  2. the repository root, found by walking up from this file and looking for
     book_registry.json alongside the four condition folders
  3. the directory containing this file

Raises immediately with a readable message if the data cannot be found, rather
than failing later on a missing file.
"""
from pathlib import Path
import os

_HERE = Path(__file__).resolve().parent

def _looks_like_data_root(p: Path) -> bool:
    return (p / "book_registry.json").is_file() and (p / "CondA2_Ungoverned_GPT4omini").is_dir()

def _find_data_root() -> Path:
    env = os.environ.get("RRD_DATA_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if _looks_like_data_root(p):
            return p
        raise SystemExit(f"RRD_DATA_ROOT is set to {p}, which does not contain the response data.")
    for cand in (_HERE, *_HERE.parents):
        if _looks_like_data_root(cand):
            return cand
    raise SystemExit(
        "Could not locate the response data.\n"
        "Expected a directory containing book_registry.json and the four Cond* folders.\n"
        "Run from inside a clone of the repository, or set RRD_DATA_ROOT."
    )

def _first_existing(*cands: Path) -> Path:
    for c in cands:
        if c.exists():
            return c
    return cands[-1]

HERE   = _HERE
DATA   = _find_data_root()
CANON  = _first_existing(DATA / "canon_packs", _HERE / "canon_packs")
EXPORT = _first_existing(
    *(p / "a-llm-default-bias" for p in DATA.glob("hermeneutics-export-*")),
    DATA / "hermeneutics-export-20260510-071918" / "a-llm-default-bias",
)
FIGS   = _first_existing(DATA / "figures", _HERE.parent / "figures")

def data_file(name: str) -> Path:
    """A derived data file (CSV/TXT), wherever it sits relative to the scripts."""
    return _first_existing(_HERE / name, DATA / "analysis" / name, DATA / name)

def canon_pack(stem: str) -> Path:
    """A Canon Pack JSON by filename stem prefix, e.g. 'nathan-the-wise'."""
    for p in sorted(CANON.glob(f"{stem}*.json")):
        return p
    raise SystemExit(f"No Canon Pack matching '{stem}*' under {CANON}")
