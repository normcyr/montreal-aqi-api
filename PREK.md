# Prek Installation Guide

This project uses [Prek](https://github.com/j178/prek) for managing pre-commit hooks. Prek is a Rust-based reimplementation of pre-commit that is faster and more efficient.

## Installation

### Using Homebrew (macOS/Linux)

```bash
brew install prek
```

### Using pip

```bash
pip install prek
```

### Using cargo

```bash
cargo install prek
```

### Using uv (recommended)

```bash
uv pip install prek
```

For other installation methods, see the [official Prek documentation](https://github.com/j178/prek#installation).

## Setup

After installing Prek, initialize the pre-commit hooks:

```bash
prek install
```

This will install the git hooks defined in `.pre-commit-config.yaml`.

## Running Hooks

Run all hooks:

```bash
prek run
```

Run specific hook:

```bash
prek run ruff-format
```

Run hooks on the last commit:

```bash
prek run --last-commit
```

Run hooks on specific directory:

```bash
prek run --directory src/
```

List all available hooks:

```bash
prek list
```

## Why Prek?

- **Single Binary**: No Python or runtime dependencies needed
- **Faster**: 2-3x faster than pre-commit with better disk space usage
- **uv Integration**: Built-in support for [uv](https://github.com/astral-sh/uv) for Python dependency management
- **Monorepo Support**: Better workspace mode for larger projects
- **Parallel Execution**: Hooks can run in parallel by priority
- **Rust Implementations**: Built-in Rust-native implementations of common hooks

## Migrating from pre-commit

If you have pre-commit installed, you can safely migrate to Prek:

1. Keep your existing `.pre-commit-config.yaml` unchanged
2. Install Prek using one of the methods above
3. Run `prek install` to set up the git hooks
4. You can now safely remove pre-commit: `pip uninstall pre-commit`

The configuration is fully compatible between the two tools.
