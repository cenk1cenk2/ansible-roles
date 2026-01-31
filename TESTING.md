# Testing Documentation for load_vars Plugin

## Overview

The `cenk1cenk2.reloaded.load_vars` plugin is tested using **Molecule** with **Podman** as the container driver, following Ansible community best practices for collection testing.

## Why Molecule?

Molecule provides several advantages over standalone playbook testing:

1. **Isolation** - Tests run in containers, preventing host pollution
2. **Reproducibility** - Same environment every time across different systems
3. **Industry Standard** - Recommended by Ansible for collection testing
4. **CI/CD Ready** - Easy integration with GitLab CI, GitHub Actions, etc.
5. **Comprehensive** - Supports prepare, converge, verify lifecycle
6. **Multiple Scenarios** - Can test different configurations easily

## Quick Start

```bash
# Install dependencies
pip install molecule molecule-podman ansible-core ansible-lint

# Run all tests
cd reloaded
molecule test

# Or use the convenience script
cd reloaded
./test-molecule.sh
```

## Test Coverage

The Molecule test suite covers **9 comprehensive test scenarios**:

### Pattern Mode (5 tests)
- Basic pattern matching with `*.yml`
- Non-strict mode behavior (no files)
- Strict mode failure (no files)
- Specific pattern matching
- Parameter validation (missing mode/root)

### Environment Mode (4 tests)
- Hierarchical loading (base + environment)
- Variable precedence (env overrides base)
- Non-strict mode with missing environment
- Strict mode failure (no directories)
- Default common directory behavior

## Test Infrastructure

```
reloaded/
├── molecule/
│   ├── README.md              # Detailed Molecule documentation
│   └── default/               # Default test scenario
│       ├── molecule.yml       # Molecule config (Podman driver)
│       ├── requirements.yml   # Galaxy requirements
│       ├── prepare.yml        # Test environment setup
│       ├── converge.yml       # Main test playbook (9 tests)
│       └── verify.yml         # Smoke tests
└── test-molecule.sh           # Convenience wrapper script
```

## Running Tests

### Full Test Suite (Recommended)

```bash
cd reloaded
molecule test
```

This runs: create → prepare → converge → verify → destroy

### Development Mode (Faster)

```bash
cd reloaded
molecule converge  # Run tests, keep container
# ... make changes ...
molecule converge  # Re-run tests quickly
molecule destroy   # Clean up when done
```

### Verbose Output

```bash
molecule test -vvvv  # Maximum verbosity
```

## CI/CD Integration

See `reloaded/molecule/README.md` for GitLab CI and GitHub Actions examples.

## Deprecated Test Files

The following files are **deprecated** and replaced by Molecule:
- `test-load-vars-pattern.yml` - Use `molecule test` instead
- `test-load-vars-environment.yml` - Use `molecule test` instead
- `test-vars/` directory - Test data now created in container by `prepare.yml`

These files are kept for reference but should not be used for testing.

## Requirements

- **Podman** - Container runtime (rootless mode supported)
- **Python 3.8+** - For Ansible and Molecule
- **Python packages**:
  - `molecule` - Test orchestration
  - `molecule-podman` - Podman driver
  - `ansible-core` - Ansible engine
  - `ansible-lint` - YAML/playbook linting

## Troubleshooting

See `reloaded/molecule/README.md` for detailed troubleshooting guidance.

## Documentation

- [Molecule Testing README](./reloaded/molecule/README.md) - Comprehensive guide
- [Molecule Official Docs](https://molecule.readthedocs.io/)
- [Ansible Testing Guide](https://docs.ansible.com/ansible/latest/dev_guide/testing.html)

## Summary

✅ **Industry-standard testing** using Molecule
✅ **Container isolation** with Podman
✅ **9 comprehensive tests** covering all scenarios
✅ **CI/CD ready** for automated testing
✅ **Easy to run** with `molecule test`
