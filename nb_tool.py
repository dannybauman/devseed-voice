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

NLM = os.environ.get("NLM_BIN", os.path.expanduser("~/.local/bin/nlm"))
PROFILE = os.environ.get("NLM_PROFILE", "devseed")
HERE = os.path.dirname(os.path.abspath(__file__))


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


def nlm(args, timeout):
    env = {**os.environ, "NLM_PROFILE": PROFILE}
    r = subprocess.run([NLM, *args, "--profile", PROFILE, "--json"], capture_output=True,
                       text=True, timeout=timeout, env=env)
    if r.returncode != 0:
        last = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["nlm failed"]
        raise RuntimeError(last[0])
    return json.loads(r.stdout)


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
    nlm(cmd, 90)
    return {"answer": f"Started the {kind} from the {title} notebook. It takes about 5 to 15 "
                      f"minutes and will be in that notebook's Studio panel when it is done."}


def main():
    verb = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        args = json.loads(sys.stdin.read() or "{}")
        out = {"ask": ask, "make": make}[verb](args)
    except (ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as e:
        out = {"answer": f"That did not work: {e}"}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
