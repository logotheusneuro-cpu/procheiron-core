# Procheiron — install instructions for coding agents

You are a coding agent installing Procheiron for your operator. Execute the steps in order.
Each step ends with a **gate**; do not continue past a failed gate — report it instead. When
you finish, give your operator the report described at the end.

Procheiron is a trust layer for agent memory: an enforced independent-review lifecycle plus a
tamper-evident, hash-chained audit log. It stores nothing and retrieves nothing.

## 1. Install

```bash
pipx install procheiron   # or: pip install --user procheiron
```

**Gate:** `procheiron version` prints a version (0.2.2 or later).

## 2. Scaffold a commons

Agree on a location with your operator (default: `./procheiron-commons` in the project root).

```bash
procheiron init ./procheiron-commons
```

**Gate:** `procheiron validate ./procheiron-commons` prints `PASS`.

## 3. Prove tamper-evidence

Run the whole loop once so your operator sees the catch, not a claim. From inside the commons:

```bash
python3 memory_propose.py --created-by setup_agent --type decision --scope project \
    --subject "install check" --statement "Procheiron installed and verified on this machine." \
    --source-path INSTALL_FOR_AGENTS.md --confidence 0.9
```

Take the record id it prints (`mem_…`), then promote it. The reviewer must be a different
identity than `setup_agent` — promoting your own record will be refused, which is correct:

```bash
python3 memory_promote.py --memory-id <the id> --new-status active \
    --reviewer operator --authorized-by operator --reason "install check verified" \
    --allow-unverified-reviewer
procheiron validate .                                  # expect: PASS
sed -i.bak 's/operator/rogue/g' memory/index/audit.jsonl
procheiron validate .                                  # expect: FAIL, entry_hash mismatch
mv memory/index/audit.jsonl.bak memory/index/audit.jsonl
procheiron validate .                                  # expect: PASS again
```

**Gate:** the middle validate FAILED and its output contained `entry_hash mismatch`; the final
validate passed.

## 4. Wire yourself in over MCP

Add Procheiron to your own MCP configuration, using the **absolute** path to the commons.
Merge into an existing `mcpServers` block — never replace it:

```json
{ "mcpServers": { "procheiron": { "command": "procheiron", "args": ["mcp", "--root", "/abs/path/to/procheiron-commons"] } } }
```

(Claude Code equivalent: `claude mcp add procheiron -- procheiron mcp --root /abs/path/to/procheiron-commons`.)

This is read-only: writes stay dry-run until `--allow-writes` is added. **Ask your operator
before enabling writes** — do not add the flag on your own initiative.

**Gate:** after a reload, the `memory.search` tool is callable and returns without error.

## 5. Rules you now operate under

- Propose memories under your own identity (`--created-by <your agent id>`).
- Never promote a record you proposed. Self-review is refused by the tool; do not work around
  it with a second identity.
- Never put secrets, tokens, or credentials in a memory. The writer scans and refuses
  secret-shaped content; treat a refusal as final.

## 6. Report to your operator

- The installed version (`procheiron version`).
- The commons path, and the final `procheiron validate` output.
- The exact line from step 3 proving the tamper was caught.
- MCP wiring status: which config file you edited, and that writes are still disabled.
- Anything that failed a gate, verbatim.
