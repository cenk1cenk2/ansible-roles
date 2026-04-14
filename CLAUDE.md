## Overview

Ansible collection `cenk1cenk2.reloaded` — action plugins for deploying containerized services as Podman Quadlets with Helm chart templating. Replaces the legacy role-based approach (`cenk1cenk2.generic.*`, `cenk1cenk2.service.*`) with Python action plugins that have structured return values, diff support, and proper controller/target separation.

## Stack & Structure

- **Language:** Python (action plugins), YAML (Ansible playbooks, Helm charts)
- **Framework:** Ansible collection (namespace: `cenk1cenk2`, name: `reloaded`)
- **Build:** Taskfile (`task test` runs all tests in Podman container)
- **CI:** GitLab CI with semantic-release via `devops/pipelines`
- **Python:** 3.13+ (pyproject.toml), ansible-core 2.20+ (2.21 beta adds `VariableLayer`)
- **Key directories:**
  - `plugins/action/` — action plugins (the core logic)
  - `plugins/modules/` — module documentation stubs (no logic, just docs)
  - `molecule/` — test scenarios per plugin
  - `meta/` — collection metadata

## Plugins

| Plugin | Purpose |
|--------|---------|
| `load_vars` | Load variables from YAML files with pattern/environment modes. `scope: global` injects facts, `scope: return` returns without injection. `files` return gives per-file data for loop patterns. |
| `copy_files` | Copy directory tree to target. Auto-categorizes: regular files (copy), `.secrets` files (vault decrypt), `.j2` files (template render). Supports `state: absent`. |
| `quadlet_template_helm` | Render Helm chart via `kubernetes.core.helm_template` on controller (LocalConnection swap), deploy manifest to target via copy. Supports `state: absent`. |
| `quadlet_systemd` | Daemon reload + manage service states with trigger-based restart logic. Timer support for writing `.timer` unit files. |
| `degit` | Clone git repo to temp dir on controller, copy files to target via `copy_files`. Cleans up temp dir automatically. |

## Conventions

- All plugins use `self._loader.get_basedir()` for relative path resolution (NOT `ansible_playbook_dir` which is CWD)
- `_fail()` helper returns early with `result["failed"] = True`
- `_deploy()` helper uses `ansible.builtin.copy` action plugin for content→target writes (handles diff, check mode)
- `_run_action()` helper delegates to other action plugins via `action_loader.get()`
- `_execute_module()` for modules that run on target (systemd, file)
- `LocalConnection` swap pattern for modules that must run on controller (`helm_template`)
- Return values always include `changed`, `msg`, and relevant context (dest, filename, etc.)
- `diff` propagation: collect diffs from sub-actions and attach to result
- Molecule tests are self-contained: tempfile for isolation, block/always for cleanup, no prepare/verify playbooks
- Tests run in `quay.io/ansible/creator-ee` container via Taskfile (except `quadlet_systemd` which needs live systemd)
- Never run `uv run molecule` directly — always use `task test`
- Helm 3.x required (kubernetes.core doesn't support helm 4 yet)
- `galaxy.yml` version is managed by semantic-release, not manually

## Decision Log

- **Path resolution: `get_basedir()` over `ansible_playbook_dir`**
  - Chose: `self._loader.get_basedir()` for resolving relative paths
  - Why: `ansible_playbook_dir` returns the CWD where `ansible-playbook` was invoked, not the playbook file's directory. Running `ansible-playbook containers/headscale/deploy.yml` from repo root would resolve `./vars` to `<root>/vars` instead of `<root>/containers/headscale/vars`
  - Rejected: `task_vars["ansible_playbook_dir"]` — broken for nested playbook paths

- **Helm execution: LocalConnection swap over delegate_to**
  - Chose: Swap `self._connection` to `LocalConnection` for `_execute_module`, then restore
  - Why: `helm_template` module needs helm binary + PyYAML on wherever it runs. Target hosts don't have these. `delegate_to: localhost` in playbook doesn't affect `_execute_module` inside action plugins
  - Rejected: `delegate_to: localhost` on tasks (doesn't propagate to inner module calls), subprocess (user wanted ansible module)

- **load_vars scope: `global` vs `return`**
  - Chose: Two modes via `scope` parameter
  - Why: `global` (inject facts) for backward compat with existing playbooks. `return` (no injection) for multi-instance loop pattern where you iterate over `result.files` instead of overwriting facts each iteration
  - Rejected: `register` as parameter name (reserved Ansible keyword), always-return (breaks existing playbooks)

- **load_vars return mode: direct YAML loading over include_vars**
  - Chose: `self._loader.load_from_file()` + `self._templar.template()` for `scope: return`
  - Why: `include_vars` action plugin always injects facts as a side effect, even when we don't want it to. Direct loading avoids global pollution
  - Kept: `include_vars` for `scope: global` (it does the injection we want)

- **copy_files templates: action plugin over manual templar**
  - Chose: Delegate to `ansible.builtin.template` action plugin via `_run_action()`
  - Why: `self._templar.template()` doesn't resolve variables from play context. The template action plugin handles all Jinja2 resolution correctly
  - Rejected: `self._templar.template()` with `available_variables = task_vars` (Templar's `is_template()` returns False for plain strings in recent ansible versions)

- **Molecule tests: container via Taskfile**
  - Chose: `task test` runs all scenarios in `creator-ee` container
  - Why: Consistent environment, helm installed at test time, no local dependency issues
  - Exception: `quadlet_systemd` skipped in container (needs live systemd user session), runs locally only

## Approaches Tried

- **`ansible_facts` for return values in load_vars** → Worked but `INJECT_FACTS_AS_VARS` deprecation in ansible-core 2.24 means top-level access breaks. Switched to `register_host_variables` with `VariableLayer.INCLUDE_VARS` on 2.21+, fallback to `ansible_facts` on 2.20
- **`set_fact` to clear variables between tests** → Caused test failures because `set_fact` has higher precedence than `ansible_facts` from action plugins. Fixed by using `result.ansible_facts.*` in assertions instead of bare variable names
- **`kubernetes.core.helm_template` with helm 4** → Module hard-blocks helm >=4.0.0 (version check in `AnsibleHelmModule.validate_helm_version`). No fix upstream in collection v6.3.0. Use helm 3.x
- **`rstrip("*")` for extensionless glob patterns** → Destroyed the pattern (e.g., `*` became empty string, `vars*` became `vars`). Fixed by appending extensions to the full pattern directly

## Tools & MCP Usage

- `task test` — runs molecule tests in container. Always use this, never raw `molecule` or `uv run molecule`
- `mise` — manages helm version per project (`mise.toml` pins helm 3.x for this repo while system has helm 4)
- `ansible-galaxy collection install --force .` — installs collection from repo root (needed before molecule runs)
- `helm template` — used indirectly via `kubernetes.core.helm_template` module inside `quadlet_template_helm`

## Gotchas

- `_execute_module()` runs on the **target** via `self._connection`, not on the controller. For controller-side execution, swap connection to `LocalConnection` temporarily
- `ansible.builtin.copy` with `content:` parameter requires the **action plugin** (via `action_loader.get`), not `_execute_module`. The module alone fails with "Source None not found"
- `ansible.builtin.file` and `ansible.builtin.systemd` have no action plugins — use `_execute_module` for these
- Molecule `--all` includes `quadlet_systemd` which fails in containers. Taskfile explicitly lists scenarios to skip it
- `self._templar.template()` silently returns raw strings when `is_template()` returns False — this happens with content loaded from files. Use the `template` action plugin instead for file rendering
- YAML single quotes inside single quotes (`'{{ ansible_facts['env'] }}'`) causes parse errors. Use double quotes for inner access: `'{{ ansible_facts["env"] }}'`
