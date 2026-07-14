---
name: nithin-forge
description: Nithin's delivery forge — carry one idea down an unbroken line from raw concept to reviewed, committed code: discover, spec, tickets, implement, verify, review, pausing only at approval gates.
disable-model-invocation: true
---

# Nithin's Forge

One idea enters the forge; reviewed, committed code comes out. Inside, the work moves down a fixed **assembly line** of **stations**, each a skill you already have. The **baton** is the idea, growing more concrete at every station — a pile of decisions, then a spec, then tickets, then green code. **Carry the baton to the end of the line.** The line pauses only at a **gate** (below); everywhere else, when a question surfaces, resolve it and keep moving.

Each station chains a skill that is user-invoked in isolation. Invoke it by its `/name`; if a station's skill won't invoke directly, read its `SKILL.md` and follow it.

## Before the line starts

- This forge conducts other skills rather than replacing them. It expects the **mattpocock/skills** ecosystem installed: `grill-with-docs`, `wayfinder`, `to-spec`, `to-tickets`, `implement`, `code-review`, `research`, `prototype`, `tdd`, `verify`, plus `setup-matt-pocock-skills`. Install those companions first — the line is only as complete as the stations behind it.
- A tracker must be configured — run `/setup-matt-pocock-skills` if the spec or ticket station reports none.
- Work on a feature branch named for the idea. If you're on `main` or a protected `FB*`/`RB*` branch, create one first.

## The stations

### 1. Discover — the user chooses the mode

Open the line by putting one choice to the user (the discovery gate): **grill it in one line**, or **chart the map first**. Recommend one, but the user picks.

- **`/grill-with-docs`** — the default. A single bounded session that grills the idea into shared understanding, capturing ADRs and a glossary. Right for a feature or a change that fits one run.
- **`/wayfinder`** — reserve for a **very complex, multi-stage** effort where the way to the destination is genuinely unclear: building a whole application or subsystem from scratch, a large migration, work too big for one session. It charts a multi-session map first; when the map's way is clear, start a fresh line on the pieces it produced. Recommend it only when the effort has that build-an-application shape.

During either mode, reach for `/research` when the answer lives in docs or a third-party API, and `/prototype` when "how should it look / behave" is the open question — both cut ambiguity before the spec.

**Done when** every decision the spec needs is settled and its ADRs and glossary are written — or, on the wayfinder path, the map's way to the destination is clear and a fresh line takes it from there.

### 2. Spec — `/to-spec`

Synthesize the discussion into a spec published to the tracker — no re-interview.

**Done when** the spec is published and its testing seams are agreed (Gate).

### 3. Tickets — `/to-tickets`

Slice the spec into tracer-bullet tickets, each declaring its blocking edges, published to the tracker.

**Done when** the breakdown is approved and every ticket is published with its edges (Gate).

### 4. Implement — `/implement`, one agent loop per ticket

Work the **frontier**: every ticket whose blockers are all closed. Dispatch each frontier ticket to its own agent loop — a subagent with a fresh context, running `/implement` for that one ticket. Run unblocked tickets in parallel; hold blocked ones until their blockers close. Each loop drives `/tdd`, reviews itself with `/code-review`, and commits. As tickets close, dispatch the ones they unblock.

**Done when** every ticket is closed green — tests passing and committed — with none left open or waiting on an unfinished blocker.

### 5. Verify — `/verify`

Drive the built feature end-to-end and watch it actually run — green tests are not a running app. Exercise the real flow the spec described, in the real app.

**Done when** the feature's behaviour is observed working end-to-end, not merely green in tests.

### 6. Review — `/code-review`

Review the whole branch since its base, across Standards and Spec.

**Done when** the review is reported and each blocking finding is fixed or explicitly deferred by the user.

## Gates — the only pauses

Arrive at a gate with a complete proposal and a recommendation, so the user's job is approve-or-adjust, not fill-in-the-blank:

- **Discovery gate** (station 1): grill in one line, or chart the map with wayfinder first.
- **Spec gate** (station 2): the spec and its testing seams.
- **Tickets gate** (station 3): the ticket breakdown and its blocking edges.

Between gates the line runs without stopping.

## Self-unblock

Figure it out before reaching out. When a question surfaces away from a gate, answer it from the code, the ADRs, the tracker, or a `/research` loop — reach for the user only when the answer is genuinely theirs: a product trade-off, a missing credential, a scope call. Batch those asks; never trickle one-at-a-time questions a gate could carry.
