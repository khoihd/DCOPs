# Main Continuity

## Project
Name: DCOP  
Origin: Derived from pyDcop (Orange-OpenSource)  
Repo Type: Private continuation  
Status: Early-stage stabilization & exploration  

## Current Goal
Stabilize and understand the existing codebase before making structural changes.  
Prepare for incremental modernization (Python version, dependencies, tooling).

## Current Focus Area
- Core DCOP algorithms and execution flow
- Project structure and module responsibilities
- Identifying entry points and main APIs

## Key Decisions
- Work conservatively: no large refactors without explicit approval
- Preserve original behavior unless explicitly changing it
- Keep full commit history (no squash/rewrite)
- Do NOT maintain upstream remote (detached from original repo)
- Rename project identity to "DCOP" (not pyDcop)

## Constraints
- Minimal diffs only
- No large-scale renaming or restructuring yet
- No new dependencies without approval
- Avoid touching multiple modules in one change
- Maintain compatibility with existing code until upgrade plan is defined
- Prefer the project-local virtualenv (`./.venv/bin/python`, `./.venv/bin/pip`,
  `./.venv/bin/pydcop`) over Conda or commands resolved from ambient `PATH`.

## Recent Changes
- Cloned original pyDcop repository
- Renamed local project folder to DCOP
- Set private repo as origin (removed upstream reference)
- Planning AGENTS.md and continuity workflow

## Next Steps
- Identify main entry points (CLI / API usage)
- Run project locally and verify baseline behavior
- Review dependency list and Python version compatibility
- Identify critical modules:
  - algorithm implementations
  - agent/distribution logic
  - communication/simulation layer
- Decide initial small improvement task (low-risk)

## Known Issues
- Codebase likely targets older Python versions (>=3.6)
- CI (Travis) is outdated
- Dependencies may be outdated or unpinned
- Documentation may reference deprecated tooling or workflows

## Important Files
- README.md — original project description (needs adaptation)
- setup.py / pyproject.toml — packaging and dependencies
- pydcop/ (main package) — core logic
- tests/ — validation and behavior reference
- docs/ — may contain useful architecture insights

## Open Questions
- What is the primary execution path? (CLI vs library usage)
- Which modules are safe to modify first?
- What is the minimal supported Python version going forward?
- Should package/module names be renamed later?
- Which parts of the system are actively useful vs legacy?

## Notes for Agent
- Always read this file before starting work
- Only modify explicitly mentioned files
- Ask before touching core modules (e.g., algorithm logic, messaging)
- Prefer inspection and explanation before modification
- Suggest small, incremental improvements only
- Do not refactor for style alone
- Highlight uncertainty instead of guessing

## Working Style
- Human-in-the-loop (approval required for non-trivial changes)
- Prefer “analyze → propose → confirm → edit”
- Keep outputs concise and focused
