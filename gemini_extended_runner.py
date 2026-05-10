#!/usr/bin/env python3
"""
Extended GFI study — Condition A runner (Gemini, ungoverned).

Sends the 15-question H2H protocol to a Google Gemini model in a
single fresh chat session for one book at a time. Saves each response
as a JSON file in
    Gemini_15_responses/<abbrev>_responses/condA_QNN_<abbrev>.json

System prompt:
    "You are a helpful assistant that answers questions about the
     book <Title> by <Author>."
User messages: the 15 verbatim questions from protocol_15q.json,
sent sequentially in the same chat session.

Usage
-----
    # Configure once (PowerShell):
    $env:GOOGLE_API_KEY = "<your-free-tier-key>"

    # Run one book at a time (case-insensitive):
    python gemini_extended_runner.py --book med
    python gemini_extended_runner.py --book aow

    # Default behaviour: errors out if any condA_*_<abbrev>.json files already
    # exist in the target book folder (prevents accidental overwrite).

    # Override flags:
    python gemini_extended_runner.py --book med --force      # overwrite all 15
    python gemini_extended_runner.py --book med --resume     # skip existing, do missing only

    # List available abbreviations:
    python gemini_extended_runner.py --list

Install
-------
    pip install google-genai

Free-tier safety
----------------
- Default model gemini-2.5-flash (RPD=250, well under 150-query budget).
- 2s pacing between turns within a book; 10s pacing not relevant for
  single-book runs.
- 429 rate-limit -> exponential backoff (60/120/180s) up to 3 retries.
- Hard daily-cap detection -> clean exit with resume hint.
- Every JSON written immediately after each successful call -> partial
  runs survive interruption; --resume picks up where left off.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "book_registry.json"
PROTOCOL_PATH = HERE / "protocol_15q.json"
RESPONSES_ROOT = HERE / "Gemini_15_responses"

MODEL_ID = "gemini-2.5-flash"
TEMPERATURE = 0.0

# Pacing strategy.
# Tuned for Gemini API Tier 1 (paid: 1000 RPM, 1M TPM, generous RPD on
# gemini-2.5-flash) — no need for free-tier burst-cooldown protection.
# All 15 Qs sent in a single burst with a polite 2s gap between turns;
# whole book completes in roughly 3 minutes.
# If you ever drop back to free tier, lower BURST_SIZE to 5 and raise
# INTER_BURST_SLEEP to 120 to recover the free-tier survival pacing.
BURST_SIZE = 15
INTRA_BURST_SLEEP = 2.0    # seconds between calls within a burst
INTER_BURST_SLEEP = 0      # n/a when burst >= 15
RATE_LIMIT_BACKOFFS = (60, 120, 180)  # safety net if a 429 still fires

SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant that answers questions about the book "
    "{title} by {author}."
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["books"]


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))["questions"]


def resolve_book(arg: str, registry: dict) -> tuple[str, dict]:
    """Map a case-insensitive abbreviation to its registry entry."""
    key = arg.strip().lower()
    if key not in registry:
        valid = ", ".join(sorted(registry.keys()))
        raise SystemExit(
            f"ERROR: book abbreviation '{arg}' not recognised.\n"
            f"Valid options: {valid}"
        )
    return key, registry[key]


# ---------------------------------------------------------------------------
# Output paths and resume logic
# ---------------------------------------------------------------------------

def book_output_dir(abbrev: str) -> Path:
    return RESPONSES_ROOT / f"{abbrev}_responses"


def output_filename(abbrev: str, qid: str) -> str:
    """Per-book filename: condA_Q01_med.json"""
    return f"condA_{qid}_{abbrev}.json"


def existing_files(out_dir: Path, abbrev: str) -> list[str]:
    if not out_dir.exists():
        return []
    return sorted(p.name for p in out_dir.glob(f"condA_Q*_{abbrev}.json"))


def decide_run_mode(out_dir: Path, abbrev: str,
                    force: bool, resume: bool) -> set[str]:
    """
    Returns the set of qids ('Q01'..'Q15') that this run should send.
    Also enforces the default error-out behaviour if files exist and
    neither --force nor --resume is supplied.
    """
    if force and resume:
        raise SystemExit("ERROR: --force and --resume are mutually exclusive.")

    all_qids = {f"Q{i:02d}" for i in range(1, 16)}
    existing = set()
    if out_dir.exists():
        for p in out_dir.glob(f"condA_Q*_{abbrev}.json"):
            # filename: condA_Q01_med.json -> stem 'condA_Q01_med'
            stem = p.stem
            # extract Qxx between 'condA_' and '_<abbrev>'
            try:
                qid = stem.split("_")[1]
                if qid.startswith("Q") and len(qid) == 3:
                    existing.add(qid)
            except (IndexError, ValueError):
                continue

    if not existing:
        return all_qids

    if force:
        print(f"[mode] --force: overwriting {len(existing)} existing file(s)")
        return all_qids

    if resume:
        missing = sorted(all_qids - existing)
        if not missing:
            raise SystemExit(
                f"ERROR --resume: all 15 files already exist in {out_dir}. "
                f"Use --force to re-collect or delete the folder."
            )
        print(f"[mode] --resume: {len(existing)} existing, "
              f"{len(missing)} to do: {', '.join(missing)}")
        return set(missing)

    raise SystemExit(
        f"ERROR: target folder already contains {len(existing)} response file(s):\n"
        f"  {out_dir}\n"
        f"  files: {', '.join(sorted(existing))}\n"
        f"\n"
        f"Pass one of:\n"
        f"  --resume   (skip existing files, only collect the missing ones)\n"
        f"  --force    (overwrite all 15 files)\n"
    )


# ---------------------------------------------------------------------------
# Gemini call with retry
# ---------------------------------------------------------------------------

def _import_genai():
    try:
        from google import genai
        from google.genai import types
        return genai, types
    except ImportError as exc:
        raise SystemExit(
            "ERROR: google-genai SDK not installed.\n"
            "Run: pip install google-genai"
        ) from exc


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("429" in msg or "resource_exhausted" in msg
            or "rate" in msg and "limit" in msg
            or "quota" in msg)


def send_with_retry(chat, question_text: str, qid: str) -> dict:
    """
    Send one question to the Gemini chat session. Returns a dict with
    keys: reply (str), input_tokens, output_tokens, total_tokens,
    model_version, latency_seconds. Raises on permanent failure.
    """
    last_exc = None
    for attempt, backoff in enumerate([0] + list(RATE_LIMIT_BACKOFFS)):
        if backoff:
            print(f"  [{qid}] rate-limited, sleeping {backoff}s "
                  f"(attempt {attempt}/{len(RATE_LIMIT_BACKOFFS)})...",
                  flush=True)
            time.sleep(backoff)
        try:
            t0 = time.time()
            resp = chat.send_message(question_text)
            latency = time.time() - t0
            usage = getattr(resp, "usage_metadata", None)
            in_tok = getattr(usage, "prompt_token_count", 0) if usage else 0
            out_tok = getattr(usage, "candidates_token_count", 0) if usage else 0
            total_tok = getattr(usage, "total_token_count", in_tok + out_tok) if usage else 0
            model_version = getattr(resp, "model_version", MODEL_ID) or MODEL_ID
            return {
                "reply": resp.text or "",
                "input_tokens": int(in_tok or 0),
                "output_tokens": int(out_tok or 0),
                "total_tokens": int(total_tok or 0),
                "model_version_returned": model_version,
                "latency_seconds": round(latency, 2),
            }
        except Exception as exc:
            last_exc = exc
            if not _is_rate_limit_error(exc):
                raise
            # Verbose: print Google's full error text on FIRST 429 of this
            # question, so we can see exactly which quota was tripped
            # (RPM / TPM / RPD / burst protection / etc.).
            if attempt == 0:
                print(f"  [{qid}] 429 detail: {str(exc)[:600]}", flush=True)
    # All retries exhausted -> permanent failure for this question.
    raise RuntimeError(
        f"Rate-limit retries exhausted for {qid}. "
        f"Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Per-book run
# ---------------------------------------------------------------------------

def run_book(abbrev: str, meta: dict, qids_to_send: set[str],
             api_key: str) -> None:
    title = meta["title"]
    author = meta["author_canonical"]
    out_dir = book_output_dir(abbrev)
    out_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(title=title, author=author)
    print(f"\n=== {title} by {author} ({abbrev}) ===")
    print(f"  output: {out_dir}")
    print(f"  questions to send: {len(qids_to_send)}")
    print(f"  system prompt: {system_prompt!r}")

    protocol = load_protocol()
    genai, types = _import_genai()
    client = genai.Client(api_key=api_key)

    # One chat session for the entire book -- 15 turns share context.
    chat = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=TEMPERATURE,
        ),
    )

    session_uuid = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    completed = []
    failed = []

    # Build the in-order list of Qs we will actually send this run.
    qids_in_order = [f"Q{i:02d}" for i in range(1, 16) if f"Q{i:02d}" in qids_to_send]
    n_to_send = len(qids_in_order)

    # Always iterate Q01..Q15 in order so the chat session sees the
    # questions in the published sequence. Skip qids that we don't
    # need to re-send (i.e., resume mode); the burst counter operates
    # over calls actually sent in this run, so resume bursts cleanly.

    print(f"  [pacing] burst of {BURST_SIZE}, intra={INTRA_BURST_SLEEP}s, "
          f"inter-burst={INTER_BURST_SLEEP}s; "
          f"projected runtime ~{int((n_to_send * INTRA_BURST_SLEEP + (n_to_send - 1) // BURST_SIZE * (INTER_BURST_SLEEP - INTRA_BURST_SLEEP)) / 60)} min "
          f"if no rate-limits.", flush=True)

    sent_idx = 0  # 0-based index of the question being sent in this run
    for qid in qids_in_order:
        qrec = protocol[qid]
        question_text = qrec["text"]

        print(f"  [{qid}] sending...", flush=True)
        try:
            result = send_with_retry(chat, question_text, qid)
        except Exception as exc:
            print(f"  [{qid}] FAILED: {exc}", flush=True)
            failed.append({"qid": qid, "error": str(exc)})
            # Stop early if we hit a hard cap -- preserve what we have.
            if "exhausted" in str(exc).lower() or "quota" in str(exc).lower():
                print("  [stop] hard cap reached -- exiting cleanly. "
                      "Re-run with --resume tomorrow.", flush=True)
                break
            continue

        record = {
            "condition": "A_ungoverned",
            "abbrev": abbrev,
            "book_slug": meta["slug"],
            "book_title": title,
            "book_author_canonical": author,
            "book_author_display": meta["author_display"],
            "companion_for_cross_ref": meta["companion"],
            "cluster": meta["cluster"],
            "question_id": qid,
            "question_text": question_text,
            "primary_drift": qrec["primary_drift"],
            "block": qrec["block"],
            "reply": result["reply"],
            "model": MODEL_ID,
            "model_version_returned": result["model_version_returned"],
            "temperature": TEMPERATURE,
            "system_prompt": system_prompt,
            "session_uuid": session_uuid,
            "token_usage": {
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "total_tokens": result["total_tokens"],
            },
            "latency_seconds": result["latency_seconds"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        out_path = out_dir / output_filename(abbrev, qid)
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        completed.append(qid)
        print(f"  [{qid}] ok ({result['latency_seconds']}s, "
              f"{result['input_tokens']}+{result['output_tokens']} tokens) "
              f"-> {out_path.name}", flush=True)

        sent_idx += 1
        # Pacing decision: cooldown after every BURST_SIZE successful calls,
        # otherwise the short intra-burst sleep. Skip the final sleep.
        is_last = (sent_idx == n_to_send)
        if not is_last:
            if sent_idx % BURST_SIZE == 0:
                print(f"  [pacing] burst complete ({sent_idx}/{n_to_send}). "
                      f"Cooldown {int(INTER_BURST_SLEEP)}s before next burst...",
                      flush=True)
                time.sleep(INTER_BURST_SLEEP)
            else:
                time.sleep(INTRA_BURST_SLEEP)

    # Manifest
    manifest = {
        "book": {
            "abbrev": abbrev,
            "slug": meta["slug"],
            "title": title,
            "author_canonical": author,
            "author_display": meta["author_display"],
            "companion": meta["companion"],
            "cluster": meta["cluster"],
        },
        "model": MODEL_ID,
        "temperature": TEMPERATURE,
        "system_prompt": system_prompt,
        "session_uuid": session_uuid,
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "completed_qids": sorted(completed),
        "failed_qids": failed,
        "n_completed": len(completed),
        "n_failed": len(failed),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n  done: {len(completed)}/{len(qids_to_send)} ok, "
          f"{len(failed)} failed.")
    if failed:
        print(f"  re-run with --resume to retry the missing ones.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extended GFI Cond_A runner (Gemini, ungoverned).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage")[1].split("Install")[0]
    )
    parser.add_argument("--book", help="Book abbreviation (case-insensitive). "
                                       "Use --list to see available.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite all 15 output files.")
    parser.add_argument("--resume", action="store_true",
                        help="Skip existing files, only fetch missing ones.")
    parser.add_argument("--list", action="store_true",
                        help="List available book abbreviations and exit.")
    args = parser.parse_args()

    registry = load_registry()

    if args.list:
        print("Available books:")
        for abbrev in sorted(registry.keys()):
            m = registry[abbrev]
            print(f"  {abbrev:6s}  {m['title']} ({m['cluster']})")
        return

    if not args.book:
        parser.error("--book is required (or use --list).")

    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "ERROR: GOOGLE_API_KEY env var not set.\n"
            "PowerShell: $env:GOOGLE_API_KEY = '<your-key>'\n"
            "bash:       export GOOGLE_API_KEY='<your-key>'"
        )

    abbrev, meta = resolve_book(args.book, registry)
    out_dir = book_output_dir(abbrev)
    qids_to_send = decide_run_mode(out_dir, abbrev, args.force, args.resume)

    run_book(abbrev, meta, qids_to_send, api_key)


if __name__ == "__main__":
    main()
