# Skills & Custom Agents

Central repository for VS Code Copilot agent skills and custom agent definitions.

## Structure

```
skills/          # Agent skills (~/.agents/skills/)
agents/          # Custom agent definitions (.github/agents/)
.skill-lock.json # Skill source tracking
```

## Skills

### Custom (built in-house)

| Skill | Description |
|-------|-------------|
| `issues-to-stories` | Convert GitHub Issues (PRDs) into Rally Features and User Stories |
| `rally-board-ops` | Full Rally board lifecycle: features, stories, iterations, estimates, tags |
| `rally-to-prd` | Fetch a Rally user story and generate a PRD document |
| `run-turbo-local` | Run any app in a turborepo locally (dev servers, ports, installs) |

### Installed from [mattpocock/skills](https://github.com/mattpocock/skills)

| Skill | Description |
|-------|-------------|
| `caveman` | Ultra-compressed communication mode (~75% token reduction) |
| `diagnose` | Disciplined diagnosis loop for hard bugs |
| `grill-me` | Stress-test a plan or design through relentless questioning |
| `grill-with-docs` | Grill session that updates CONTEXT.md and ADRs inline |
| `handoff` | Compact conversation into a handoff document |
| `improve-codebase-architecture` | Find deepening opportunities in a codebase |
| `prototype` | Build throwaway prototypes for design exploration |
| `setup-matt-pocock-skills` | Bootstrap skill installation |
| `tdd` | Test-driven development with red-green-refactor |
| `to-issues` | Break a plan into independently-grabbable issues |
| `to-prd` | Turn conversation context into a PRD |
| `triage` | Triage issues through a state machine |
| `write-a-skill` | Create new agent skills with proper structure |
| `zoom-out` | Step back and evaluate the bigger picture |

### Installed from [vercel-labs/skills](https://github.com/vercel-labs/skills)

| Skill | Description |
|-------|-------------|
| `find-skills` | Discover and install agent skills |

## Custom Agents

| Agent | Description |
|-------|-------------|
| `api-architect` | API design mentor: generates layered service/manager/resilience code |
| `orchestrator` | General-purpose custom agent (template) |

## Usage

### Installing skills from this repo

Copy the desired skill folder into `~/.agents/skills/`:

```bash
cp -R skills/rally-board-ops ~/.agents/skills/
```

### Installing agents into a project

Copy agent files into your project's `.github/agents/` directory:

```bash
mkdir -p .github/agents
cp agents/api-architect.agent.md .github/agents/
```
