#!/usr/bin/env python3
"""Foley live tools for the DevSeed voice agent: ask a notebook, or make something from one.

Foley runs `nb_tool.py ask|make` with the tool's args as JSON on stdin and speaks the
`answer` it prints. Only the notebooks in notebooks.json exist as far as the voice is concerned.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

NLM = os.environ.get("NLM_BIN", os.path.expanduser("~/.local/bin/nlm"))
PROFILE = os.environ.get("NLM_PROFILE", "devseed")
HERE = os.path.dirname(os.path.abspath(__file__))
POLL_S = 30
STALE_MINUTES = 120  # NotebookLM takes 5-15 minutes; past this the artifact is presumed dead
# The CLI can label a finished artifact "unknown", so ready is proven by a download that
# succeeds, not by the status; only these statuses mean it will never finish
DEAD = ("failed",)
DOWNLOAD_KIND = {"slides": "slide-deck"}


def load_notebooks(path=os.path.join(HERE, "notebooks.json")):
    try:
        with open(path) as f:
            return {k: (v["id"], v["title"]) for k, v in json.load(f).items()}
    except FileNotFoundError:
        return {}


NOTEBOOKS = load_notebooks()

MAKERS = {
    "audio": ["audio", "create"],
    "video": ["video", "create"],
    "slides": ["slides", "create"],
    "report": ["report", "create"],
}


def notebook(name):
    key = (name or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key not in NOTEBOOKS:
        raise ValueError(f"unknown notebook {name!r}; choose one of: {', '.join(NOTEBOOKS)}")
    return NOTEBOOKS[key]


def for_speech(text):
    text = text.split("\n---", 1)[0]  # NotebookLM appends a "Would you like..." follow-up
    paras = text.strip().split("\n\n")
    if len(paras) > 1 and "would you like" in paras[-1].lower():
        text = "\n\n".join(paras[:-1])
    text = re.sub(r"\s*\[\d+(?:\s*[-,]\s*\d+)*\]", "", text)
    return re.sub(r"[*_#]+", "", text).strip()


def nlm(args, timeout, raw=False):
    # download has no --profile or --json flag; the profile rides the env there
    env = {**os.environ, "NLM_PROFILE": PROFILE}
    flags = [] if raw else ["--profile", PROFILE, "--json"]
    r = subprocess.run([NLM, *args, *flags], capture_output=True,
                       text=True, timeout=timeout, env=env)
    if r.returncode != 0:
        last = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["nlm failed"]
        raise RuntimeError(last[0])
    return None if raw else json.loads(r.stdout)


def ask(args):
    nb_id, title = notebook(args.get("notebook"))
    q = (args.get("question") or "").strip()
    if not q:
        raise ValueError("no question")
    d = nlm(["notebook", "query", nb_id, q, "--new-conversation", "--timeout", "150"], 170)
    return {"answer": f"From the {title} notebook: " + for_speech(d.get("answer", ""))}


def make(args):
    nb_id, title = notebook(args.get("notebook"))
    kind = (args.get("kind") or "").strip().lower()
    if kind not in MAKERS:
        raise ValueError(f"kind must be one of: {', '.join(MAKERS)}")
    cmd = [*MAKERS[kind], nb_id, "--confirm"]
    focus = (args.get("focus") or "").strip()
    if focus and kind == "report":
        cmd += ["--format", "Create Your Own", "--prompt", focus]
    elif focus:
        cmd += ["--focus", focus]
    created = nlm(cmd, 90)
    art = created.get("artifact_id") if isinstance(created, dict) else None
    if art:
        log = open(os.path.join(home(), "devseed-voice-watch.log"), "a")
        w = subprocess.Popen([sys.executable, os.path.abspath(__file__), "watch"],
                             stdin=subprocess.PIPE, stdout=log, stderr=log, start_new_session=True,
                             text=True)
        w.stdin.write(json.dumps({"nb_id": nb_id, "title": title, "kind": kind,
                                  "artifact_id": art, "started": time.time()}))
        w.stdin.close()
        return {"answer": f"Started the {kind} from the {title} notebook. It takes about 5 to 15 "
                          f"minutes. I will tell you when it is ready and put the link on your screen."}
    return {"answer": f"Started the {kind} from the {title} notebook. It takes about 5 to 15 "
                      f"minutes and will be in that notebook's Studio panel when it is done."}


def home():
    return os.environ.get("FOLEY_HOME") or os.getcwd()


def notice(title, body, say):
    line = json.dumps({"title": title, "body": body, "source": "devseed-voice", "say": say}) + "\n"
    with open(os.path.join(home(), "notices.jsonl"), "a") as f:
        f.write(line)  # one write of one line so a concurrent reader never sees half of it


def watch(job):
    nb_id, title, kind, art = job["nb_id"], job["title"], job["kind"], job["artifact_id"]
    what = f"The {kind} from the {title} notebook"
    while True:
        try:
            rows = nlm(["studio", "status", nb_id], 120) or []
            status = next((r.get("status") or "unknown" for r in rows
                           if art in (r.get("artifact_id"), r.get("id"))), "missing")
            if status not in DEAD:
                out = os.path.join(tempfile.mkdtemp(), "artifact")
                try:
                    nlm(["download", DOWNLOAD_KIND.get(kind, kind), nb_id, "--id", art,
                         "--output", out, "--no-progress"], 600, raw=True)
                    if os.path.getsize(out) > 0:
                        notice(f"Ready: {kind} from {title}",
                               f"{what} is ready.\nhttps://notebooklm.google.com/notebook/{nb_id}",
                               f"{what} is ready. The link is on your screen.")
                        return
                except (RuntimeError, OSError):
                    pass  # not rendered yet
                finally:
                    if os.path.exists(out):
                        os.remove(out)
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
            print("watch:", e, file=sys.stderr, flush=True)
            status = "unknown"
        if status in DEAD or time.time() - job["started"] > STALE_MINUTES * 60:
            notice(f"Did not finish: {kind} from {title}", f"{what} did not finish.",
                   f"{what} did not finish. You can try again.")
            return
        time.sleep(POLL_S)


def selftest():
    global nlm, POLL_S
    calls = []

    def fake(args, timeout, raw=False):
        calls.append(args[0])
        if args[0] == "studio":
            return [{"artifact_id": "a1", "status": "in_progress" if calls.count("studio") < 2 else "completed"}]
        if len(calls) > 2:  # first download: not rendered yet
            open(args[args.index("--output") + 1], "w").write("x")
        else:
            raise RuntimeError("not ready")
    nlm, POLL_S = fake, 0
    with tempfile.TemporaryDirectory() as d:
        os.environ["FOLEY_HOME"] = d
        watch({"nb_id": "nb9", "title": "Blog", "kind": "audio", "artifact_id": "a1", "started": time.time()})
        n = json.loads(open(os.path.join(d, "notices.jsonl")).read())
    assert n["title"] == "Ready: audio from Blog" and "https://notebooklm.google.com/notebook/nb9" in n["body"], n
    assert n["source"] == "devseed-voice" and "link is on your screen" in n["say"]
    print("selftest ok")


def main():
    verb = sys.argv[1] if len(sys.argv) > 1 else ""
    if verb == "selftest":
        return selftest()
    try:
        args = json.loads(sys.stdin.read() or "{}")
        if verb == "watch":
            return watch(args)
        out = {"ask": ask, "make": make}[verb](args)
    except (ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as e:
        out = {"answer": f"That did not work: {e}"}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
