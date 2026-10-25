# devseed-voice

Talk to your team's NotebookLM notebooks out loud. Ask a question and hear an answer grounded in the notebook's sources, or ask for an audio overview, video, slides or report and it starts one after you say yes.

Gemini Live does the listening and talking. [`nlm`](https://github.com/jacob-bd/gemini-notebook-mcp-cli) reaches NotebookLM. It runs on Foley, a voice runtime that is not public yet.

## Setup

1. Sign `nlm` in to your work Google account: `nlm login --profile devseed`
2. `cp notebooks.example.json notebooks.json` and list the notebooks it may use. It can reach nothing else
3. `cp .env.example .env.local` and set `KEY_CMD` to print a Gemini API key from a paid project
4. `./run.sh` and open the address it prints

`python3 test_nb_tool.py` checks the allowlist.

## License

MIT
