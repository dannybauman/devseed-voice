# devseed-voice, the build tracker

Charted 2026-10-24. The course is `.astrolabe/courses/devseed-voice/`; this file holds the work. The first version is done: ask and make, by voice, from a phone, against an allowlist of notebooks.

## Hard rules / off-limits

- The voice never sees more than the person asking can see. No shared service account.
- Only allowlisted notebooks exist as far as the voice is concerned.
- Anything that makes or sends waits for a spoken yes.
- Nothing internal in this repository: notebook ids, keys and accounts stay in local, gitignored files.
- Foley stays a runtime dependency, never vendored here.

## Phase 1. Hand back what it makes

- [x] **1.1 Know when it is done.** After a make, poll the notebook's Studio until the artifact is ready (the download succeeding is the proof for video), with a stale cutoff.
- [x] **1.2 Hand it over.** Tell the caller it is ready, on the call if it is still open, and put a link on the screen.
- [ ] **1.3 Heard on a call.** Make an audio overview, hear "it's ready", open it from the phone.

## Phase 2. Pictures on the screen

- [ ] **2.1 A card that shows an image or a map.** A tool can return an image or map card, and the page shows it on the phone.
- [ ] **2.2 Seen on a call.** A slide deck or infographic from a notebook shows on the phone screen.

## Phase 3. Ground Station by voice

- [ ] **3.1 A Ground Station tool.** Ask for a geospatial thing out loud; the request goes to Ground Station.
- [ ] **3.2 Spoken and shown.** The answer is spoken briefly and the map or image lands on the screen.
- [ ] **3.3 Heard on a call.**

## Phase 4. Notebooks made for an audience

- [ ] **4.1 Public-only copies.** A notebook built only from public sources for anything a wider group will hear.
- [ ] **4.2 One notebook, one audience.** The allowlist records who each notebook is for, and sharing a notebook never reaches past its sources' own permissions.

## Phase 5. Past the policy owners

- [ ] **5.1 The questions, written.** Which Gemini terms apply, the official NotebookLM route for a team, and per-person sign-in.
- [ ] **5.2 Their answer, recorded.** What they said, and what changes because of it.

## Phase 6. A teammate runs it

- [ ] **6.1 Their own sign-in.** A teammate signs in as themselves and sees only what they can already open.
- [ ] **6.2 Setup that a teammate can follow.** From a fresh machine to a first answer, using the README alone.
- [ ] **6.3 One teammate uses it for real.**

## Phase 7. GitHub and Slack, read-only

- [ ] **7.1 Read-only tools for the questions that need them**, added only when a real question asks for them.

## Progress log

- 2026-10-24: first version proven by voice on a phone. Both notebooks answered with their source named, an out-of-list notebook and a general-knowledge question were refused, and make waited for a yes.
- 2026-10-24: 1.1 and 1.2 built and merged (devseed-voice #1, Foley #166): make spawns a watcher that polls NotebookLM until the download proves the artifact ready, then leaves a notice the call page shows and says, on the call or next time it opens. The route was exercised with a test line; 1.3 waits for a real call.
