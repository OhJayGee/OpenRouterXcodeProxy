# Contributing to OpenRouter Proxy for Xcode 26 Beta

Thank you for your interest in contributing to the OpenRouter Proxy! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker (for containerized development)
- Git
- An OpenRouter API key (for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/OpenRouterXcodeProxy.git
cd OpenRouterXcodeProxy
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/OhJayGee/OpenRouterXcodeProxy.git
```

## Development Setup

### Local Python Environment

1. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
cd proxy
pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```

### Docker Development

1. Build the Docker image:

```bash
cd proxy
docker build -t openrouter-proxy-dev .
```

2. Run the container:

```bash
docker run -p 8080:8080 openrouter-proxy-dev
```

### Environment Variables for Development

Create a `.env` file (git-ignored) for local development:

```bash
PORT=8080
DISABLE_SSL_VERIFY=false
MODEL_FILTER_FILE=filter-models.txt
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Fixes**: Fix issues and improve stability
2. **Features**: Add new functionality
3. **Documentation**: Improve or add documentation
4. **Tests**: Increase test coverage
5. **Performance**: Optimize code performance
6. **Refactoring**: Improve code structure and readability

### Development Workflow

1. **Create a branch** for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/modifications

2. **Make your changes** following our [Coding Standards](#coding-standards)

3. **Test your changes** thoroughly

4. **Commit your changes** with clear, descriptive messages:

```bash
git add .
git commit -m "Add feature: description of what you added"
```

Commit message guidelines:
- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Add detailed description after a blank line if needed
- Reference issues with `#issue-number`

5. **Push to your fork**:

```bash
git push origin feature/your-feature-name
```

6. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: Maximum 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings (except when single quotes avoid escaping)
- **Imports**: Grouped and sorted (standard library, third-party, local)

### Code Organization

```python
# Standard library imports
import os
import sys

# Third-party imports
import requests
from flask import Flask

# Local imports (if any)
from .utils import helper_function
```

### Docstrings

Use Google-style docstrings for all functions, classes, and modules:

```python
def example_function(param1, param2):
    """
    Brief description of the function.

    Detailed description if needed, explaining what the function does,
    its purpose, and any important notes.

    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When param1 is invalid

    Example:
        >>> example_function("test", 42)
        True
    """
    pass
```

### Comments

- Write self-documenting code when possible
- Use comments to explain **why**, not **what**
- Keep comments up-to-date with code changes

```python
# Good: Explains why
# Skip "OPENROUTER PROCESSING" messages as they break Xcode Intelligence
if ": OPENROUTER PROCESSING" in line:
    continue

# Bad: States the obvious
# Check if line contains OPENROUTER PROCESSING
if ": OPENROUTER PROCESSING" in line:
    continue
```

### Error Handling

- Use specific exception types
- Provide helpful error messages
- Log errors appropriately

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    logger.error(f"Request to {url} timed out after 30 seconds")
    raise
except requests.HTTPError as e:
    logger.error(f"HTTP error occurred: {e}")
    raise
```

## Testing

### Running Tests

Run the test suite:

```bash
cd proxy
python -m pytest test_app.py -v
```

Run with coverage:

```bash
python -m pytest test_app.py -v --cov=app --cov-report=html
```

### Writing Tests

All new features and bug fixes should include tests:

```python
def test_new_feature():
    """Test description"""
    # Arrange
    test_data = create_test_data()

    # Act
    result = function_under_test(test_data)

    # Assert
    assert result == expected_value
```

### Test Coverage

- Aim for 80%+ code coverage
- Test both success and failure cases
- Test edge cases and boundary conditions
- Mock external API calls

Example test structure:

```python
from unittest.mock import Mock, patch
import pytest

@patch('app.requests.get')
def test_get_models_success(mock_get):
    """Test successful model retrieval"""
    # Mock the response
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "test/model", "created": 123}]
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Test the endpoint
    with app.test_client() as client:
        response = client.get('/v1/models',
                            headers={'Authorization': 'Bearer test-key'})

    assert response.status_code == 200
    assert "test/model" in response.get_json()["data"][0]["id"]
```

## Submitting Changes

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** (if applicable)
5. **Fill out the PR template** completely

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated

## Related Issues
Fixes #(issue number)

## Screenshots (if applicable)
```

### Review Process

1. A maintainer will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

**Response Times:**
- Initial review: Within 7 days
- Follow-up reviews: Within 3-5 days

## Reporting Bugs

### Before Submitting a Bug Report

- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant information

### Bug Report Template

```markdown
**Describe the bug**
Clear and concise description of the bug

**To Reproduce**
Steps to reproduce:
1. Start proxy with '...'
2. Send request to '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment:**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.5]
- Proxy version: [e.g., commit hash or release]
- Xcode version: [e.g., 26 Beta 3]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information
```

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
**Feature Description**
Clear description of the proposed feature

**Problem it Solves**
What problem does this feature address?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Screenshots, mockups, examples, etc.
```

## Documentation

### Documentation Standards

- Keep documentation up-to-date with code
- Use clear, concise language
- Include code examples
- Add screenshots where helpful

### Types of Documentation

1. **README.md**: Overview and quick start
2. **API.md**: API reference
3. **ARCHITECTURE.md**: System design and architecture
4. **Inline comments**: Code-level documentation
5. **Docstrings**: Function/class documentation

### Documentation Changes

Documentation improvements are always welcome:

- Fix typos and grammar
- Clarify confusing sections
- Add missing examples
- Improve formatting

Small documentation fixes can be submitted directly via PR without an issue.

## Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **OpenRouter Discord**: For OpenRouter-specific questions

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes (for significant contributions)
- Project documentation (for major features)

## Development Tips

### Useful Commands

```bash
# Format code with black
black proxy/app.py

# Lint with flake8
flake8 proxy/app.py --max-line-length=100

# Type checking with mypy (if using type hints)
mypy proxy/app.py

# Run tests with verbose output
pytest proxy/test_app.py -vv

# Run specific test
pytest proxy/test_app.py::test_get_models -v

# Build Docker image
docker build -t openrouter-proxy:dev ./proxy

# Run with environment variables
PORT=9090 DISABLE_SSL_VERIFY=true python proxy/app.py
```

### Debugging

Enable debug mode:

```python
# In app.py (for development only)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
```

Add verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Working with Git

Keep your fork updated:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

Rebase your feature branch:

```bash
git checkout feature/your-feature
git rebase main
```

Clean up commits:

```bash
git rebase -i HEAD~3  # Interactive rebase last 3 commits
```

## Questions?

If you have questions not covered here:

1. Check the [README](README.md) and [API documentation](API.md)
2. Search [existing issues](https://github.com/OhJayGee/OpenRouterXcodeProxy/issues)
3. Ask in [GitHub Discussions](https://github.com/OhJayGee/OpenRouterXcodeProxy/discussions)
4. Open a new issue with the `question` label

---

**Thank you for contributing to OpenRouter Proxy for Xcode 26 Beta!** 🎉

Your contributions help make AI integration in Xcode better for everyone.
