#!/usr/bin/env python3
"""
Extended GFI study — Cond_B runner (governed companion via Living Literature).

Sends the 15-question H2H protocol to each book's governed companion via
the Living Literature platform's chat endpoint. Same questions as
Cond_A1 (Gemini) and Cond_A2 (gpt-4o-mini ungoverned), so the three
conditions are directly comparable.

Endpoint:  POST https://www.living-literature.org/api/mem/chat
Auth:      Authorization: Bearer <user JWT>
Body:      {"message": "...", "book": "<slug>", "stream": false}
Response:  JSON with reply / companion / thread_id / model / token_usage
           / access_mode / turns_used / turns_cap

Saves each response as a JSON file in:
    Governed_GPT4omini/<abbrev>_responses/CondB_QNN_<abbrev>.json

The endpoint manages thread state per (user, book) — the platform
fetches/creates a thread automatically and accumulates 15 messages per
book within it. No client-side message-history bookkeeping required
(unlike CondA1/CondA2 which used chat sessions).

Usage
-----
    $env:LL_RESEARCH_JWT = "<paste fresh JWT from browser session>"
    python companion-runtime-runner.py

Auto-runs all 10 books in alphabetical order. No CLI flags.

Behaviour on existing data (per-book pre-flight)
------------------------------------------------
    0 files in book folder       -> fresh run
    15 valid files               -> SKIP (option a); idempotent re-run
    1-14 files OR 15 with errors -> HALT (manual fix needed)

Halt also fires on:
    - missing or invalid LL_RESEARCH_JWT (401 from server)
    - mid-book API call failures after retries
    - post-book integrity check failure (less than 15 valid files)
    - Ctrl+C (saves what we have, logs interrupt)

Methodological notes
--------------------
- Temperature is server-side (BOOK_COMPANION_TEMPERATURE env on Vercel,
  default 0.4). Cond_A1 and Cond_A2 used temperature 0.0. This is a
  small documented confound; Cond_B's temperature matches the published
  H2H Cond_B setting.
- Model is server-side (BOOK_COMPANION_MODEL or SELENE_FULL_MODEL env on
  Vercel; falls back to "gpt-4o" if unset). The runner logs the actual
  model returned per call (response.model). The first response will
  reveal the actual deployed model loudly so you can spot a mismatch
  with Cond_A2 (which used gpt-4o-mini-2024-07-18) immediately.
- JWT lifetime is ~1 hour. The full corpus run is ~15 min so one fresh
  JWT covers everything. If you have to resume the next day, re-acquire
  a JWT and re-run; complete books auto-skip.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "book_registry.json"
PROTOCOL_PATH = HERE / "protocol_15q.json"
RESPONSES_ROOT = HERE / "Governed_GPT4omini"

ENDPOINT_URL = "https://www.living-literature.org/api/mem/chat"
EXPECTED_MODEL_PREFIX = "gpt-4o-mini"  # warn if first response doesn't match

INTRA_BOOK_SLEEP = 1.5     # seconds between Qs within a book
INTER_BOOK_SLEEP = 5.0     # seconds between books
RATE_LIMIT_BACKOFFS = (10, 30, 60)
REQUEST_TIMEOUT = 90       # seconds per call (generous for cold starts)

CONDITION_LABEL = "B_governed_companion"


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
    return f"CondB_{qid}_{abbrev}.json"


# ---------------------------------------------------------------------------
# Pre-flight integrity check
# ---------------------------------------------------------------------------

def integrity_check(book_dir: Path, abbrev: str) -> tuple[str, str]:
    """
    Inspect a book folder. Returns (status, detail).
        'empty'     no files       -> safe to run fresh
        'complete'  15 valid files -> skip
        'partial'   1-14 files     -> halt
        'invalid'   15 files but some fail to parse / have empty replies -> halt
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
# HTTP call with retry
# ---------------------------------------------------------------------------

def _post_json(url: str, headers: dict, body: dict) -> tuple[int, dict | str]:
    """POST a JSON body and return (status_code, json_or_text)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            txt = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(txt)
            except Exception:
                return resp.status, txt
    except urllib.error.HTTPError as exc:
        body_txt = ""
        try:
            body_txt = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        try:
            return exc.code, json.loads(body_txt)
        except Exception:
            return exc.code, body_txt


def _is_retryable(status: int) -> bool:
    return status in (408, 429, 500, 502, 503, 504)


def call_with_retry(jwt: str, book_slug: str, message: str, qid: str) -> dict:
    """
    Send one chat message to the platform endpoint with retry on
    transient errors. Returns the parsed JSON response. Raises on
    permanent failure (e.g., 401 invalid JWT, 403 forbidden, 4xx
    other than 429, or all retries exhausted).
    """
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {"message": message, "book": book_slug, "stream": False}

    last_status = None
    last_body = None

    for attempt, backoff in enumerate([0] + list(RATE_LIMIT_BACKOFFS)):
        if backoff:
            print(f"    [{qid}] retrying after {backoff}s "
                  f"(attempt {attempt}/{len(RATE_LIMIT_BACKOFFS)})...",
                  flush=True)
            time.sleep(backoff)

        t0 = time.time()
        status, payload = _post_json(ENDPOINT_URL, headers, body)
        latency = time.time() - t0

        last_status = status
        last_body = payload

        if status == 200:
            if isinstance(payload, dict) and payload.get("ok") is True:
                payload["_latency_seconds"] = round(latency, 2)
                return payload
            # 200 but ok != true — surface for diagnosis
            raise RuntimeError(
                f"Server returned 200 but ok != true. Body: {str(payload)[:500]}"
            )

        # Non-200
        if status == 401:
            raise RuntimeError(
                f"401 Unauthorized — JWT is invalid or expired. "
                f"Re-acquire a fresh JWT and restart. Body: {str(payload)[:300]}"
            )
        if status == 403:
            raise RuntimeError(
                f"403 Forbidden — admin / entitlement state may be wrong. "
                f"Body: {str(payload)[:300]}"
            )

        if not _is_retryable(status):
            raise RuntimeError(
                f"HTTP {status} (non-retryable). Body: {str(payload)[:500]}"
            )

        # Retryable error — log on first attempt and loop
        if attempt == 0:
            print(f"    [{qid}] HTTP {status} (retryable). Body: "
                  f"{str(payload)[:300]}", flush=True)

    raise RuntimeError(
        f"Retries exhausted for {qid}. Last status: {last_status}. "
        f"Last body: {str(last_body)[:500]}"
    )


# ---------------------------------------------------------------------------
# Per-book run
# ---------------------------------------------------------------------------

def run_book(jwt: str, abbrev: str, meta: dict, protocol: dict,
             warned_about_model: list) -> tuple[str, str, dict]:
    """
    Run all 15 Qs for one book. Returns (status, detail, manifest).
    status in {'ok', 'failed'}.
    """
    title = meta["title"]
    author = meta["author_canonical"]
    book_slug = meta["slug"]
    book_dir = book_output_dir(abbrev)
    book_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {title} by {author} ({abbrev}, slug={book_slug}) ===")
    print(f"  output: {book_dir}")

    started_at = datetime.now(timezone.utc).isoformat()
    completed: list[str] = []
    failed: list[dict] = []
    seen_models: set[str] = set()
    seen_thread_id: str | None = None

    for i in range(1, 16):
        qid = f"Q{i:02d}"
        qrec = protocol[qid]
        question_text = qrec["text"]

        print(f"  [{qid}] sending...", flush=True)

        try:
            resp = call_with_retry(jwt, book_slug, question_text, qid)
        except Exception as exc:
            print(f"  [{qid}] FAILED: {exc}", flush=True)
            failed.append({"qid": qid, "error": str(exc)})
            # 401 / 403 are session-fatal; halt the whole run.
            if "401 Unauthorized" in str(exc) or "403 Forbidden" in str(exc):
                print(f"  [{qid}] HALT: session-level error", flush=True)
                break
            continue

        # Extract fields per the architecture doc's response shape.
        reply = str(resp.get("reply") or "")
        companion = resp.get("companion") or meta.get("companion")
        thread_id = resp.get("thread_id")
        model = resp.get("model") or "(unset)"
        access_mode = resp.get("access_mode")
        turns_used = resp.get("turns_used")
        turns_cap = resp.get("turns_cap")
        token_usage = resp.get("token_usage") or {}
        latency = resp.get("_latency_seconds", 0)

        seen_models.add(str(model))
        if seen_thread_id is None:
            seen_thread_id = thread_id

        # First-response model warning
        if (i == 1 and not warned_about_model
                and not str(model).startswith(EXPECTED_MODEL_PREFIX)):
            print(f"\n  ⚠️  MODEL WARNING: response.model = {model!r} "
                  f"(expected to start with {EXPECTED_MODEL_PREFIX!r})", flush=True)
            print(f"      The Cond_A2 runner used 'gpt-4o-mini-2024-07-18'.")
            print(f"      You can:")
            print(f"        (a) accept the model mismatch and document it")
            print(f"        (b) abort with Ctrl+C, set BOOK_COMPANION_MODEL")
            print(f"            in Vercel, redeploy, then restart")
            print(f"        (c) re-run Cond_A2 at the actual deployed model.")
            print(f"      Continuing for now; this warning is shown once.\n",
                  flush=True)
            warned_about_model.append(True)

        record = {
            "condition": CONDITION_LABEL,
            "abbrev": abbrev,
            "book_slug": book_slug,
            "book_title": title,
            "book_author_canonical": author,
            "book_author_display": meta["author_display"],
            "companion": companion,
            "cluster": meta["cluster"],
            "question_id": qid,
            "question_text": question_text,
            "primary_drift": qrec["primary_drift"],
            "block": qrec["block"],
            "reply": reply,
            "model": model,
            "thread_id": thread_id,
            "access_mode": access_mode,
            "turns_used": turns_used,
            "turns_cap": turns_cap,
            "token_usage": {
                "input_tokens": int(token_usage.get("input_tokens") or 0),
                "output_tokens": int(token_usage.get("output_tokens") or 0),
            },
            "latency_seconds": latency,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        out_path = book_dir / output_filename(abbrev, qid)
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        completed.append(qid)
        in_t = record["token_usage"]["input_tokens"]
        out_t = record["token_usage"]["output_tokens"]
        print(f"  [{qid}] ok ({latency}s, {in_t}+{out_t} tokens, "
              f"model={model}, turns={turns_used}/{turns_cap}) "
              f"-> {out_path.name}", flush=True)

        time.sleep(INTRA_BOOK_SLEEP)

    manifest = {
        "book": {
            "abbrev": abbrev,
            "slug": book_slug,
            "title": title,
            "author_canonical": author,
            "author_display": meta["author_display"],
            "companion": meta["companion"],
            "cluster": meta["cluster"],
        },
        "condition": CONDITION_LABEL,
        "endpoint": ENDPOINT_URL,
        "expected_model_prefix": EXPECTED_MODEL_PREFIX,
        "models_seen": sorted(seen_models),
        "thread_id": seen_thread_id,
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

    status, detail = integrity_check(book_dir, abbrev)
    if status == "complete":
        return "ok", detail, manifest
    else:
        return "failed", detail, manifest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    jwt = os.environ.get("LL_RESEARCH_JWT", "").strip()
    if not jwt:
        raise SystemExit(
            "ERROR: LL_RESEARCH_JWT env var not set.\n"
            "PowerShell: $env:LL_RESEARCH_JWT = '<your-fresh-JWT>'\n"
            "Acquire JWT from browser Local Storage on living-literature.org\n"
            "(Application -> Local Storage -> sb-...-auth-token -> access_token)."
        )

    last8 = jwt[-8:] if len(jwt) >= 8 else "????"
    print(f"=== Cond_B runner — governed companion via Living Literature ===")
    print(f"[info] JWT ends with ...{last8}")
    print(f"[info] Endpoint:     {ENDPOINT_URL}")
    print(f"[info] Expected model prefix: {EXPECTED_MODEL_PREFIX!r}")
    print(f"[info] Pacing:       {INTRA_BOOK_SLEEP}s intra-book, "
          f"{INTER_BOOK_SLEEP}s inter-book")
    print(f"[info] Output root:  {RESPONSES_ROOT}")
    print()
    print(f"Starting in 5s... press Ctrl+C now to abort if anything is wrong.")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n[abort] cancelled before start")
        return

    registry = load_registry()
    protocol = load_protocol()
    book_order = sorted(registry.keys())

    RESPONSES_ROOT.mkdir(parents=True, exist_ok=True)

    summary: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT_URL,
        "expected_model_prefix": EXPECTED_MODEL_PREFIX,
        "book_order": book_order,
        "books": {},
    }

    halt_reason: str | None = None
    interrupted: bool = False
    warned_about_model: list = []  # mutable flag passed to run_book

    try:
        for abbrev in book_order:
            meta = registry[abbrev]
            book_dir = book_output_dir(abbrev)

            if book_dir.exists():
                status, detail = integrity_check(book_dir, abbrev)
                if status == "complete":
                    print(f"\n=== {meta['title']} ({abbrev}) ===")
                    print(f"  SKIP: {detail}")
                    summary["books"][abbrev] = {
                        "result": "skipped", "detail": detail,
                    }
                    continue
                elif status in ("partial", "invalid"):
                    print(f"\n=== {meta['title']} ({abbrev}) ===")
                    print(f"  HALT: pre-flight {status} — {detail}")
                    print(f"  Manual fix: clean the folder or restore valid files.")
                    summary["books"][abbrev] = {
                        "result": "halted_pre_flight", "detail": detail,
                    }
                    halt_reason = (f"pre-flight integrity {status} on {abbrev}: "
                                   f"{detail}")
                    break

            status, detail, manifest = run_book(
                jwt, abbrev, meta, protocol, warned_about_model
            )
            summary["books"][abbrev] = {
                "result": status,
                "detail": detail,
                "n_completed": manifest["n_completed"],
                "n_failed": manifest["n_failed"],
                "models_seen": manifest["models_seen"],
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

    summary["ended_at"] = datetime.now(timezone.utc).isoformat()
    summary["halt_reason"] = halt_reason
    summary["interrupted"] = interrupted

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = RESPONSES_ROOT / f"run_summary_{ts}.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n=== Run summary ===")
    for abbrev in book_order:
        info = summary["books"].get(abbrev)
        if info is None:
            print(f"  {abbrev:6s}  not reached")
        else:
            models = ", ".join(info.get("models_seen", [])) or "-"
            print(f"  {abbrev:6s}  {info['result']:20s}  "
                  f"models={models}  {info.get('detail', '')}")
    if halt_reason:
        print(f"\nHalted: {halt_reason}")
    print(f"\nFull summary: {summary_path}")
    print(f"\nReminder: sign out of living-literature.org to invalidate the JWT.")


if __name__ == "__main__":
    main()
