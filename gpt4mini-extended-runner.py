#!/usr/bin/env python3
"""
Extended GFI study — Cond_A2 runner (matched-model ungoverned).

Sends the 15-question H2H protocol to OpenAI's gpt-4o-mini for each of
the 10 books, in sequence, in a single fresh chat session per book.
This is the matched-model counterpart to Cond_A1 (Gemini-2.5-flash) —
same system prompt, same questions, same temperature, only the model
differs. Cond_B will use the same gpt-4o-mini family with full
governance.

Saves each response as a JSON file in:
    Ungoverned_GPT4omini/<abbrev>_responses/CondA2_QNN_<abbrev>.json

System prompt (identical to Cond_A1 for parity):
    "You are a helpful assistant that answers questions about the
     book <Title> by <Author>."

Usage
-----
    pip install openai
    $env:OPENAI_API_KEY = "<gfi-project-key>"
    python gpt4mini-extended-runner.py

The script auto-runs all 10 books in alphabetical order. No CLI flags.

Behaviour on existing data (per-book pre-flight)
------------------------------------------------
    0 files in book folder       -> fresh run
    15 valid files               -> SKIP (option a); idempotent re-run
    1-14 files OR 15 with errors -> HALT (manual fix needed)

Halt also fires on:
    - missing OPENAI_API_KEY
    - mid-book API call failures after retries
    - post-book integrity check failure (less than 15 valid files)
    - Ctrl+C (saves what we have, logs interrupt)

A run summary is always saved to:
    Ungoverned_GPT4omini/run_summary_<UTC-timestamp>.json

No automatic sanity check (per spec). Run sanity_check_condA.py
afterwards (with the future --condition condA2 flag).
"""
from __future__ import annotations

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
RESPONSES_ROOT = HERE / "Ungoverned_GPT4omini"

# Pinned snapshot — gpt-4o-mini-2024-07-18 is the stable mini snapshot.
# The script also captures the actual model id returned by the API per call
# (resp.model) so any silent alias rolls show up in the data.
MODEL_ID = "gpt-4o-mini-2024-07-18"
TEMPERATURE = 0.0

INTRA_BOOK_SLEEP = 1.5     # seconds between Qs within a book
INTER_BOOK_SLEEP = 5.0     # seconds between books
RATE_LIMIT_BACKOFFS = (10, 30, 60)  # rare on Tier 1 paid; safety net only

SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant that answers questions about the book "
    "{title} by {author}."
)

CONDITION_LABEL = "A2_ungoverned_matched_model"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["books"]


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))["questions"]


def book_output_dir(abbrev: str) -> Path:
    return RESPONSES_ROOT / f"{abbrev}_responses"


def output_filename(abbrev: str, qid: str) -> str:
    return f"CondA2_{qid}_{abbrev}.json"


# ---------------------------------------------------------------------------
# Pre-flight integrity check
# ---------------------------------------------------------------------------

def integrity_check(book_dir: Path, abbrev: str) -> tuple[str, str]:
    """
    Inspect a book folder. Returns (status, detail) where status is one of:
        'empty'     no files at all -> safe to run fresh
        'complete'  15 valid files  -> skip
        'partial'   1-14 files      -> halt
        'invalid'   15 files but some fail to parse / have empty replies
                                    -> halt
    """
    expected = [f"Q{i:02d}" for i in range(1, 16)]
    files = {qid: book_dir / output_filename(abbrev, qid) for qid in expected}
    n_present = sum(1 for p in files.values() if p.exists())

    if n_present == 0:
        return "empty", "no existing files"
    if n_present < 15:
        present_qids = sorted(qid for qid, p in files.items() if p.exists())
        return "partial", (
            f"{n_present}/15 files present; missing "
            f"{sorted(set(expected) - set(present_qids))}"
        )

    # 15 files exist — verify each
    bad: list[str] = []
    for qid, path in files.items():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{qid}:parse_error({type(exc).__name__})")
            continue
        if not str(data.get("reply") or "").strip():
            bad.append(f"{qid}:empty_reply")
            continue
        if data.get("question_id") != qid:
            bad.append(f"{qid}:question_id_mismatch")
            continue
        if data.get("condition") != CONDITION_LABEL:
            bad.append(f"{qid}:condition_mismatch")
            continue
    if bad:
        return "invalid", f"15 files but {len(bad)} fail integrity: {bad[:5]}"
    return "complete", "15/15 files all valid"


# ---------------------------------------------------------------------------
# OpenAI call with retry
# ---------------------------------------------------------------------------

def _import_openai():
    try:
        import openai
        return openai
    except ImportError as exc:
        raise SystemExit(
            "ERROR: openai SDK not installed.\n"
            "Run: python -m pip install openai"
        ) from exc


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("429" in msg or "rate" in msg and "limit" in msg
            or "resource_exhausted" in msg)


def call_with_retry(client, messages: list, qid: str) -> dict:
    """
    One chat.completions.create call with rate-limit retry. Returns a
    dict with reply / token-usage / model / latency. Raises on
    permanent failure.
    """
    last_exc = None
    for attempt, backoff in enumerate([0] + list(RATE_LIMIT_BACKOFFS)):
        if backoff:
            print(f"    [{qid}] rate-limited, sleeping {backoff}s "
                  f"(attempt {attempt}/{len(RATE_LIMIT_BACKOFFS)})...",
                  flush=True)
            time.sleep(backoff)
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                temperature=TEMPERATURE,
            )
            latency = time.time() - t0
            usage = resp.usage
            return {
                "reply": (resp.choices[0].message.content or ""),
                "input_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                "output_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
                "model_version_returned": getattr(resp, "model", MODEL_ID) or MODEL_ID,
                "latency_seconds": round(latency, 2),
            }
        except Exception as exc:
            last_exc = exc
            if not _is_rate_limit(exc):
                raise
            if attempt == 0:
                print(f"    [{qid}] 429 detail: {str(exc)[:500]}", flush=True)
    raise RuntimeError(
        f"Rate-limit retries exhausted for {qid}. Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Per-book run
# ---------------------------------------------------------------------------

def run_book(client, abbrev: str, meta: dict, protocol: dict) -> tuple[str, str, dict]:
    """
    Run all 15 Qs for one book as a single chat session.
    Returns (status, detail, manifest).
        status in {'ok', 'failed'}
    """
    title = meta["title"]
    author = meta["author_canonical"]
    book_dir = book_output_dir(abbrev)
    book_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(title=title, author=author)
    print(f"\n=== {title} by {author} ({abbrev}) ===")
    print(f"  output: {book_dir}")
    print(f"  system prompt: {system_prompt!r}")

    session_uuid = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # OpenAI chat.completions is stateless per call; we manually maintain
    # the running message list to mirror Gemini's chat.start_chat()
    # behaviour. Each call sends the full prior history.
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    completed: list[str] = []
    failed: list[dict] = []

    for i in range(1, 16):
        qid = f"Q{i:02d}"
        qrec = protocol[qid]
        question_text = qrec["text"]

        print(f"  [{qid}] sending...", flush=True)
        messages.append({"role": "user", "content": question_text})

        try:
            result = call_with_retry(client, messages, qid)
        except Exception as exc:
            print(f"  [{qid}] FAILED: {exc}", flush=True)
            failed.append({"qid": qid, "error": str(exc)})
            # Pop the unanswered user message so subsequent calls don't
            # carry an unmatched user turn at the end.
            messages.pop()
            continue

        # Append assistant reply to history for next turn.
        messages.append({"role": "assistant", "content": result["reply"]})

        record = {
            "condition": CONDITION_LABEL,
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

        out_path = book_dir / output_filename(abbrev, qid)
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        completed.append(qid)
        print(f"  [{qid}] ok ({result['latency_seconds']}s, "
              f"{result['input_tokens']}+{result['output_tokens']} tokens) "
              f"-> {out_path.name}", flush=True)

        time.sleep(INTRA_BOOK_SLEEP)

    # Manifest written even on failure for forensics.
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
        "condition": CONDITION_LABEL,
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
    (book_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Post-book integrity check (the user's "checkpoint at end of each book").
    status, detail = integrity_check(book_dir, abbrev)
    if status == "complete":
        return "ok", detail, manifest
    else:
        return "failed", detail, manifest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "ERROR: OPENAI_API_KEY env var not set.\n"
            "PowerShell: $env:OPENAI_API_KEY = '<your-gfi-key>'"
        )

    last4 = api_key[-4:] if len(api_key) >= 4 else "????"
    print(f"=== Cond_A2 runner — gpt-4o-mini ungoverned ===")
    print(f"[info] OPENAI_API_KEY ends with ...{last4}")
    print(f"[info] Model:        {MODEL_ID}")
    print(f"[info] Temperature:  {TEMPERATURE}")
    print(f"[info] Pacing:       {INTRA_BOOK_SLEEP}s intra-book, "
          f"{INTER_BOOK_SLEEP}s inter-book")
    print(f"[info] Output root:  {RESPONSES_ROOT}")
    print()
    print(f"Starting in 5s... press Ctrl+C now to abort if any of the above")
    print(f"is wrong (especially the API key suffix).")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n[abort] cancelled before start")
        return

    openai = _import_openai()
    client = openai.OpenAI(api_key=api_key)

    registry = load_registry()
    protocol = load_protocol()
    book_order = sorted(registry.keys())

    RESPONSES_ROOT.mkdir(parents=True, exist_ok=True)

    summary: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_ID,
        "temperature": TEMPERATURE,
        "system_prompt_template": SYSTEM_PROMPT_TEMPLATE,
        "book_order": book_order,
        "books": {},
    }

    halt_reason: str | None = None
    interrupted: bool = False

    try:
        for abbrev in book_order:
            meta = registry[abbrev]
            book_dir = book_output_dir(abbrev)

            # Pre-flight integrity check
            if book_dir.exists():
                status, detail = integrity_check(book_dir, abbrev)
                if status == "complete":
                    print(f"\n=== {meta['title']} ({abbrev}) ===")
                    print(f"  SKIP: {detail}")
                    summary["books"][abbrev] = {
                        "result": "skipped",
                        "detail": detail,
                    }
                    continue
                elif status in ("partial", "invalid"):
                    print(f"\n=== {meta['title']} ({abbrev}) ===")
                    print(f"  HALT: pre-flight {status} — {detail}")
                    print(f"  Manual fix needed: clean the folder or restore valid files,")
                    print(f"  then re-run the script.")
                    summary["books"][abbrev] = {
                        "result": "halted_pre_flight",
                        "detail": detail,
                    }
                    halt_reason = (f"pre-flight integrity {status} on {abbrev}: "
                                   f"{detail}")
                    break
                # status == "empty" -> fall through and run

            # Run the book.
            status, detail, manifest = run_book(client, abbrev, meta, protocol)
            summary["books"][abbrev] = {
                "result": status,
                "detail": detail,
                "n_completed": manifest["n_completed"],
                "n_failed": manifest["n_failed"],
            }

            if status != "ok":
                print(f"\n  HALT: post-book integrity check failed for "
                      f"{abbrev}: {detail}")
                halt_reason = (f"post-book integrity {status} on {abbrev}: "
                               f"{detail}")
                break

            time.sleep(INTER_BOOK_SLEEP)

    except KeyboardInterrupt:
        print(f"\n\n[interrupt] User cancelled with Ctrl+C. Saving summary.")
        interrupted = True
        halt_reason = "KeyboardInterrupt"

    # Always write a run summary, halted or not.
    summary["ended_at"] = datetime.now(timezone.utc).isoformat()
    summary["halt_reason"] = halt_reason
    summary["interrupted"] = interrupted

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = RESPONSES_ROOT / f"run_summary_{ts}.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # End-of-run report
    print(f"\n=== Run summary ===")
    for abbrev in book_order:
        info = summary["books"].get(abbrev)
        if info is None:
            print(f"  {abbrev:6s}  not reached")
        else:
            print(f"  {abbrev:6s}  {info['result']:20s}  {info.get('detail', '')}")
    if halt_reason:
        print(f"\nHalted: {halt_reason}")
    print(f"\nFull summary: {summary_path}")


if __name__ == "__main__":
    main()
