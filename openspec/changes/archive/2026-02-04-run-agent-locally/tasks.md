## 1. Preparation and Utilities

- [x] 1.1 Implement a structured exception hierarchy (`RegistryError`, `AgentNotFoundError`, etc.)
- [x] 1.2 Set up a dedicated logger for `acp_agent.registry`
- [x] 1.3 Implement system tool detection utility using `shutil.which` with logging
- [x] 1.4 Implement platform and architecture detection for binary distribution matching

## 2. Distribution Handlers

- [x] 2.1 Implement `execute_npx` with tool fallback logic and DEBUG logging
- [x] 2.2 Implement `execute_uvx` with tool fallback logic and DEBUG logging
- [x] 2.3 Implement `execute_binary` with platform matching, `DownloadError` handling, and caching

## 3. Core API

- [x] 3.1 Implement `run_local(agent_id, extra_args=(), env=None, cwd=None, cache_path=None)`
- [x] 3.2 Implement `cache_path` resolution (defaulting to `~/.local/bin`)
- [x] 3.3 Implement argument and environment merging logic
- [x] 3.4 Connect `run_local` to the appropriate distribution handlers with execution logging

## 4. Verification and Error Handling

- [x] 4.1 Add validation to ensure at least one runner is available, raising `RunnerNotFoundError` if not
- [x] 4.2 Ensure `DownloadError` contains helpful context (e.g., URL, exit code)
- [x] 4.3 Verify subprocess environment and arguments are correctly passed and logged
