# Use FolioPress with a coding agent

FolioPress is agent-neutral. The generator has no model SDK, provider API, required
subscription, agent-specific hook or external memory service. A coding agent needs
access to the checkout and the ability to read/write files and run commands.
Image viewing is needed to perform visual review; without it, the agent must ask
the owner to inspect rendered pages and report that visual review remains pending.
A plain chat assistant without file/shell access can suggest wording, but cannot
complete the same build-and-check workflow by itself.

## Start a session

1. Open a **private personal workspace**, not a public product checkout, when
   providing real career/contact data. For product development use fictional data.
2. Select the existing profile, or ask the agent to create one with new_profile.py.
3. Have the agent read root AGENTS.md and every AGENTS.md from the person folder
   down to the selected variant, plus its profile/settings and provenance notes.
4. Supply your task and confirmed facts. Do not provide passwords or API keys.
5. Expect edited source, a rebuilt PDF, verification results, and review of every
   rendered page. Ask for proposed wording only when you want approval before edits.

## Instruction entry points

| Agent/tool | Entry point shipped here | Notes |
| --- | --- | --- |
| Codex | AGENTS.md | Root guide routes to personal/variant instructions. |
| Claude Code | CLAUDE.md importing AGENTS.md | Import avoids duplicating rules; explicitly read profile guidance too. |
| Gemini CLI | GEMINI.md importing AGENTS.md | Same canonical guide and profile routing. |
| Cursor | AGENTS.md | Enable/use project instructions in the agent's workspace. |
| GitHub Copilot | .github/copilot-instructions.md | Routes to AGENTS.md and the profile guide; availability varies by Copilot surface/settings. |
| Other coding agents | Explicit prompt below | Attach/read the same Markdown files; no proprietary adapter required. |

Instruction discovery varies by tool version and settings. Check that the agent
actually read the files; do not assume an instruction filename is a hard sandbox.
The adapters have been checked against vendor documentation, not live-tested by
running paid sessions with every provider. No additional agent accounts are
needed for the build itself.

## Universal copy-paste prompt: create a CV

```text
Use this FolioPress checkout to create my CV. First read README.md, AGENTS.md,
and docs/agents.md. Create an independent profile if needed; then read every
personal/variant AGENTS.md applying to it. Do not copy fictional example claims.

Ask me for missing career facts, skills, education, contact details and language
levels. Use only confirmed information. Keep the sidebar template unless I ask
for another design, and record my durable preferences in my profile's AGENTS.md.

Edit the source, run bootstrap if needed, and build/verify the PDF using the
repository commands. Inspect every rendered page and fix layout problems. If
you cannot view images, tell me that visual review remains pending and show me
the previews. Deliver the PDF path and a short summary. Do not publish or submit
my CV without authorization, and keep real data in a private workspace.
```

## Universal copy-paste prompt: edit an existing CV

```text
Read root AGENTS.md, docs/agents.md, and the personal/variant AGENTS.md files for
profiles/<person>. Read that profile's source and settings. Apply this change:

[MY REQUEST OR EXACT APPROVED WORDING]

Preserve unrelated wording, confirmed facts, layout, fonts and reading order.
Rebuild and verify the selected PDF, visually inspect every page, and deliver
the PDF path with the changes and checks. Do not claim unperformed visual review.
```

For a role-specific version, add: “Create a variant under this person's variants/
folder and preserve the canonical CV. Use only existing or newly confirmed facts.”

## Commands every agent uses

Run from the repository root:

```sh
python3 bootstrap.py
bash build.sh --profile profiles/<person>
python3 verify.py --profile profiles/<person>
```

The build renders every page to profiles/<person>/output/previews/. The final file
is profiles/<person>/output/cv.pdf. Respect environment permissions for installing
Python/Poppler or downloading the pinned compiler. Do not disable verification to
finish a task. For machinery-only changes with an approved reference:

```sh
python3 compare_layout.py --profile profiles/<person>
```

Profiles stay independent. Keep profile-specific preferences in that profile's
AGENTS.md; update root AGENTS.md only for shared conventions. The Claude/Gemini/
Copilot entry files only route to that guide, so future edits have one source of
truth. Do not make claims of universal ATS compatibility or automatic agent compliance.

## Documentation for instruction discovery

- [Codex repository instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Claude Code memory and imports](https://code.claude.com/docs/en/memory)
- [Gemini CLI context files and imports](https://geminicli.com/docs/cli/gemini-md/)
- [Cursor project rules and AGENTS.md](https://cursor.com/docs/rules)
- [GitHub Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)

## Consistency checks

Treat consistent formatting as a required property, not a final polish step. The
build checks rendered main/sidebar styles, repeated gaps and alignment. Keep
source rules shared across headed and untitled contributions, and run
`python3 -m unittest discover -s tests -v` when changing the template or checker.
The regression suite must continue to reject intentionally inconsistent PDFs.
Never relax a check just to ship a crowded layout; use available whitespace and
visually inspect every page. Profiles may choose their own design, but equal roles
within that design should remain equal.

## Separate private profile repository (optional)

See README's optional private profile setup. Open the private repository and read
its root instructions, the separate generator checkout's AGENTS.md, and every
personal/variant instruction file. Run the generator by path, for example
`bash ../foliopress/build.sh --profile profile`. Explicit profile/output paths
resolve from the caller's directory. Keep facts, preferences, provenance, references
and PDFs in the private repository. Record the generator commit there; update it
only after rebuilding and visually reviewing the result. Shared generator edits
belong in the public checkout and must use fictional fixtures.
