# Molecule Testing for cenk1cenk2.reloaded.load_vars Plugin

This directory contains Molecule-based testing infrastructure for the `cenk1cenk2.reloaded.load_vars` action plugin.

## Overview

The tests use [Molecule](https://molecule.readthedocs.io/) with [Podman](https://podman.io/) as the container driver to provide isolated, reproducible testing of the load_vars plugin in both pattern and environment modes.

## Prerequisites

- Python 3.8+
- Podman (container runtime)
- Python packages (installed via pip/uv):
  - molecule
  - molecule-podman
  - ansible-core
  - ansible-lint

## Installation

```bash
# Install required Python packages
pip install molecule molecule-podman ansible-core ansible-lint

# Or using uv (if available)
uv pip install molecule molecule-podman ansible-core ansible-lint
```

## Test Structure

```
molecule/
└── default/                    # Default test scenario
    ├── molecule.yml           # Molecule configuration (uses Podman)
    ├── requirements.yml       # Ansible Galaxy requirements
    ├── prepare.yml            # Environment preparation (creates test files)
    ├── converge.yml           # Main test playbook (9 comprehensive tests)
    └── verify.yml             # Verification playbook (smoke tests)
```

## Running Tests

### Full Test Suite

Run all Molecule phases (prepare, converge, verify):

```bash
# From the reloaded/ directory
molecule test
```

This will:
1. Create a Podman container
2. Prepare the test environment (create test files)
3. Run the converge playbook (execute all 9 tests)
4. Run the verify playbook (smoke tests)
5. Destroy the container

### Individual Phases

Run specific Molecule phases:

```bash
# Create the container and prepare environment
molecule create
molecule prepare

# Run the main tests
molecule converge

# Run verification
molecule verify

# Check the current state
molecule list

# Destroy the container
molecule destroy
```

### Development Workflow

For iterative development, use converge instead of test:

```bash
# Run tests without destroying the container
molecule converge

# Make changes to the plugin...

# Re-run tests quickly (container persists)
molecule converge

# When done, destroy
molecule destroy
```

### Verbose Output

Add `-v`, `-vv`, `-vvv`, or `-vvvv` for increased verbosity:

```bash
molecule test -vvv
molecule converge -vvvv
```

## Test Coverage

The Molecule tests cover 9 comprehensive scenarios:

### Pattern Mode Tests (Tests 1-5)
1. **Basic pattern mode** - Load all *.yml files from a directory
2. **Non-strict mode with no matches** - Succeed with warning when no files match
3. **Strict mode with no matches** - Fail appropriately when no files match
4. **Specific pattern matching** - Load files matching specific glob patterns
5. **Missing required parameters** - Validate parameter requirements

### Environment Mode Tests (Tests 6-9)
6. **Basic environment mode** - Hierarchical loading (base + prod with overrides)
7. **Non-strict mode with missing environment** - Succeed when env dir missing
8. **Strict mode with missing directories** - Fail when both common and env missing
9. **Default common directory** - Verify 'base' is the default common directory

## Test Data

The `prepare.yml` playbook creates test data in `/tmp/test-vars/`:

```
/tmp/test-vars/
├── pattern-test/
│   ├── vars1.yml          # Pattern test file 1
│   └── vars2.yml          # Pattern test file 2
└── env-test/
    ├── base/
    │   └── common.yml     # Base/common environment variables
    └── prod/
        └── prod.yml       # Production-specific variables
```

## CI/CD Integration

### GitLab CI Example

```yaml
test:molecule:
  stage: test
  image: quay.io/ansible/creator-ee:latest
  services:
    - podman:dind
  before_script:
    - pip install molecule molecule-podman ansible-core ansible-lint
  script:
    - cd reloaded
    - molecule test
  tags:
    - podman
```

### GitHub Actions Example

```yaml
name: Molecule Tests
on: [push, pull_request]
jobs:
  molecule:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install molecule molecule-podman ansible-core ansible-lint
      - name: Run Molecule tests
        run: |
          cd reloaded
          molecule test
```

## Troubleshooting

### Podman socket issues

If you encounter Podman connection issues:

```bash
# Start Podman socket
systemctl --user start podman.socket

# Verify Podman is working
podman ps
```

### Container image pull issues

If the container image fails to pull:

```bash
# Pre-pull the image
podman pull quay.io/ansible/creator-ee:latest
```

### Permission issues

If you encounter permission issues:

```bash
# Ensure Podman is in rootless mode
podman system info | grep -i rootless

# If needed, configure rootless Podman
podman system migrate
```

## Comparison with Old Tests

The Molecule tests replace the previous standalone playbooks:
- ❌ `test-load-vars-pattern.yml` (deprecated)
- ❌ `test-load-vars-environment.yml` (deprecated)

**Benefits of Molecule**:
- ✅ Isolated container environment (no host pollution)
- ✅ Reproducible across different systems
- ✅ Automatic setup and teardown
- ✅ Industry-standard Ansible testing approach
- ✅ Better CI/CD integration
- ✅ Supports multiple scenarios and drivers

## Additional Resources

- [Molecule Documentation](https://molecule.readthedocs.io/)
- [Ansible Testing Strategies](https://docs.ansible.com/ansible/latest/dev_guide/testing.html)
- [Podman Documentation](https://docs.podman.io/)
- [Collection Testing with Molecule](https://docs.ansible.com/ansible/latest/dev_guide/testing_collection.html)
