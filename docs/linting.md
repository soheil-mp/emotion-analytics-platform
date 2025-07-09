# Linting Configuration

This document explains the linting setup for the emotion-clf-pipeline project and ensures that GitHub Actions workflows match the local pre-commit hooks exactly.

## Overview

The project uses a comprehensive linting setup with the following tools:

### Pre-commit Hooks (Basic Checks)
- **trim trailing whitespace**: Removes trailing spaces and tabs
- **fix end of files**: Ensures files end with a newline character
- **check yaml**: Validates YAML file syntax
- **check for added large files**: Prevents files >1MB from being committed
- **check for merge conflicts**: Detects merge conflict markers
- **check json**: Validates JSON file syntax
- **check toml**: Validates TOML file syntax
- **mixed line ending**: Detects mixed line endings (CRLF/LF)

### Python Code Quality Tools
- **flake8**: Python linting with custom configuration
  - Max line length: 88 characters
  - Ignores: E203 (whitespace before ':'), W503 (line break before binary operator)
  - Applies only to `src/` directory
- **black**: Python code formatter
  - Python version: 3.11
  - Applies only to `src/` directory
- **isort**: Import statement organizer
  - Profile: black (compatible with black formatter)
  - Applies only to `src/` directory

## Local Development

### Prerequisites
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Linting Locally
```bash
# Run all pre-commit hooks on all files
poetry run pre-commit run --all-files

# Run specific tools individually
poetry run flake8 --max-line-length=88 --extend-ignore=E203,W503 src/
poetry run black --check src/
poetry run isort --profile black --check-only src/

# Auto-fix formatting issues
poetry run black src/
poetry run isort --profile black src/
```

### Verification Script
Use the verification script to ensure your local setup matches the CI environment:

```bash
python scripts/verify_lint.py
```

## GitHub Actions Workflows

### Main Lint Workflow (`.github/workflows/lint.yaml`)
This is the primary workflow that runs on all pushes and pull requests:

- Uses the same Poetry and Python 3.11 setup as local development
- Caches pre-commit hooks for faster execution
- Runs `poetry run pre-commit run --all-files` (identical to local)
- Provides colored output and shows diffs on failure

### Explicit Lint Workflow (`.github/workflows/lint-explicit.yaml`)
This is an alternative workflow that runs each tool individually:

- Manually triggered via `workflow_dispatch`
- Implements each pre-commit hook step-by-step
- Provides detailed output and debugging information
- Can be enabled for troubleshooting or as a backup

## Configuration Files

### `.pre-commit-config.yaml`
Contains the exact configuration for all pre-commit hooks:
- Tool versions are pinned for reproducibility
- Arguments match the project's coding standards
- File patterns ensure tools only run on relevant files

### `pyproject.toml`
Contains tool-specific configurations:
```toml
[tool.flake8]
max-line-length = 88

[tool.isort]
profile = "black"
```

## Troubleshooting

### Common Issues

1. **Different results between local and CI**:
   - Ensure you're using the same Python version (3.11)
   - Run `poetry install` to sync dependencies
   - Clear pre-commit cache: `poetry run pre-commit clean`

2. **Pre-commit hooks not running**:
   - Install hooks: `poetry run pre-commit install`
   - Check git hooks: `ls -la .git/hooks/`

3. **Tool version mismatches**:
   - Check `.pre-commit-config.yaml` for pinned versions
   - Update local tools: `poetry run pre-commit autoupdate`

4. **File encoding issues**:
   - Ensure files are UTF-8 encoded
   - Check for binary files in text directories

### Debugging Commands

```bash
# Check pre-commit installation
poetry run pre-commit --version

# List available hooks
poetry run pre-commit hooks

# Run hooks in verbose mode
poetry run pre-commit run --all-files --verbose

# Check specific file
poetry run pre-commit run --files path/to/file.py

# Skip specific hooks (for debugging)
SKIP=flake8 poetry run pre-commit run --all-files
```

## Best Practices

1. **Commit frequently**: Run pre-commit hooks on smaller changesets
2. **Fix issues locally**: Don't rely on CI to catch linting issues
3. **Use auto-formatting**: Let black and isort fix formatting automatically
4. **Test before pushing**: Use the verification script before pushing changes
5. **Keep tools updated**: Regularly update pre-commit hook versions

## Integration with IDEs

### VS Code
Install recommended extensions:
- Python (Microsoft)
- Black Formatter
- isort
- Flake8

Configure settings in `.vscode/settings.json`:
```json
{
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=88", "--extend-ignore=E203,W503"],
    "editor.formatOnSave": true,
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### PyCharm
1. Install Black and isort plugins
2. Configure external tools for flake8
3. Set up file watchers for automatic formatting
4. Configure code style to match black settings

## Maintenance

### Updating Tool Versions
1. Update `.pre-commit-config.yaml` with new versions
2. Test locally: `poetry run pre-commit run --all-files`
3. Update `pyproject.toml` if needed
4. Run verification script: `python scripts/verify_lint.py`
5. Commit changes and verify CI passes

### Adding New Tools
1. Add tool to `.pre-commit-config.yaml`
2. Configure tool in `pyproject.toml` if needed
3. Update this documentation
4. Update the explicit workflow if necessary
5. Test thoroughly before committing
