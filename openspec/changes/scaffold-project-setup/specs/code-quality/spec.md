# Spec: Code Quality Tools

## ADDED Requirements

### Requirement: ruff must be configured for linting

The project SHALL use ruff for fast Python linting with project-specific rules.

#### Scenario: ruff lints all Python code
```
GIVEN the project source code
WHEN running `ruff check .`
THEN all Python files are analyzed
AND style violations are reported
AND fixable issues can be auto-fixed with --fix
```

#### Scenario: ruff configuration follows project conventions
```
GIVEN the [tool.ruff] section in pyproject.toml
WHEN examining linting rules
THEN configuration specifies:
  - line-length = 100
  - target-version = "py313"
  - select includes: E (pycodestyle errors), F (pyflakes), I (isort), N (pep8-naming), UP (pyupgrade)
  - exclude patterns for .git, __pycache__, .pytest_cache, .ruff_cache, dist, *.egg-info
AND rules enforce project naming conventions (snake_case, PascalCase, UPPER_SNAKE_CASE)
```

### Requirement: uv format must be configured for code formatting

The project SHALL use uv's built-in formatter for consistent code style.

#### Scenario: code can be formatted automatically
```
GIVEN Python source files
WHEN running `uv run ruff format .`
THEN code is formatted consistently
AND line length respects configured limit
AND formatting matches Black-compatible style
```

#### Scenario: formatting check can run in CI
```
GIVEN formatted code
WHEN running `uv run ruff format --check .`
THEN command succeeds if code is properly formatted
AND command fails with exit code 1 if formatting needed
AND outputs list of files that would be reformatted
```

### Requirement: pre-commit hooks must enforce code quality

Git pre-commit hooks SHALL run automated checks before commits.

#### Scenario: pre-commit configuration exists
```
GIVEN the .pre-commit-config.yaml file
WHEN examining hook configuration
THEN hooks are defined for:
  - ruff linting (with auto-fix)
  - ruff formatting
  - trailing whitespace removal
  - end-of-file fixing
  - YAML syntax checking
AND hooks run on commit
```

#### Scenario: pre-commit hooks can be installed
```
GIVEN pre-commit is installed
WHEN running `pre-commit install`
THEN git hooks are installed in .git/hooks/
AND hooks run automatically on git commit
AND failed hooks prevent commit
```

#### Scenario: pre-commit can run on all files
```
GIVEN the repository with pre-commit hooks
WHEN running `pre-commit run --all-files`
THEN all configured hooks execute on all files
AND violations are reported
AND auto-fixable issues are corrected
```

### Requirement: Type checking configuration must be present

The project SHALL be configured for optional type checking with mypy or pyright.

#### Scenario: Type hints can be validated
```
GIVEN type hints in Python code
WHEN running type checker (mypy or pyright)
THEN type errors are reported
AND configuration excludes test files from strict checking
AND gradual typing is supported
```

## Tool Configuration

### ruff Configuration (pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "*.egg-info",
    "data",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "SIM", # flake8-simplify
]

[tool.ruff.lint.pep8-naming]
# Enforce naming conventions from project.md
classmethod-decorators = ["classmethod"]
```

### pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

### pre-commit Configuration (.pre-commit-config.yaml)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```
