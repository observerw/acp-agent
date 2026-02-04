## 1. CLI Implementation

- [x] 1.1 Add `search` command stub to `src/acp_agent/cli/app.py`
- [x] 1.2 Implement agent filtering logic in the `search` command
- [x] 1.3 Implement result display using `rich.table.Table`

## 2. Verification

- [x] 2.1 Manually verify `acp-agent search` with an exact name
- [x] 2.2 Manually verify `acp-agent search` with a substring
- [x] 2.3 Manually verify `acp-agent search` with a non-existent agent name

## 3. Refactoring

- [x] 3.1 Extract table display logic into a shared helper function
- [x] 3.2 Move shared CLI utilities to `src/acp_agent/cli/utils.py`
