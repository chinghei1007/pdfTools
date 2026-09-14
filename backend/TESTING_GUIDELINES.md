# Unit Testing Guidelines for PDF Tools Backend

## Framework and Layout

- **Framework**: `unittest` (Python standard library)
- **Test files**: Live next to source files with `test_` prefix
  - Example: `apis/toolkitAPI.py` → `apis/test_toolkitAPI.py`
- **Imports**: Explicit imports, no globals
- **Structure**: One `TestCase` class per module, with test methods for each function/endpoint

## What Every Test File Must Cover

1. **Happy path**: Documented successful behavior
2. **Error paths**: All possible error conditions (400, 401, 403, 404, 413, 415, 422)
3. **Boundary inputs**: Empty files, zero pages, maximum limits, edge cases
4. **Authentication/Authorization**: Owner isolation, session validation
5. **Data validation**: Invalid inputs, missing required fields

## Naming Conventions

- Test classes: `PascalCase` ending with `Test` (e.g., `ToolkitAPITest`)
- Test methods: `snake_case` starting with `test_`
- Test descriptions: Behavior-first strings
  - Good: "rejects invalid file types"
  - Bad: "test_upload_invalid_file"
- Regression tests: Include issue reference if applicable

## Mocking Policy

- Mock at system boundaries only: filesystem, database, network
- NEVER mock the module under test or its pure helpers
- Use `unittest.mock` for external dependencies
- Restore all mocks in `tearDown`

## Test Structure Template

```python
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from apis.toolkitAPI import router
from component.pymupdfService import store


class ModuleNameTest(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp = tempfile.TemporaryDirectory()
        self.previous_root = store.ROOT
        store.ROOT = Path(self.temp.name)
        self.client = TestClient(app)
        # Setup test data

    def tearDown(self):
        """Clean up test fixtures"""
        self.client.close()
        store.ROOT = self.previous_root
        self.temp.cleanup()

    def test_happy_path(self):
        """Test successful operation"""
        # Arrange
        # Act
        # Assert
        pass

    def test_error_condition(self):
        """Test error handling"""
        # Arrange
        # Act
        # Assert error response
        pass


if __name__ == "__main__":
    unittest.main()
```

## API Endpoint Testing Checklist

For each endpoint, test:

### GET Endpoints
- [ ] Valid request returns 200 with correct data
- [ ] Missing authentication returns 401
- [ ] Invalid parameters return 400/422
- [ ] Non-existent resource returns 404
- [ ] Pagination/limits work correctly

### POST Endpoints
- [ ] Valid request returns 200/201 with correct response
- [ ] Missing required fields return 422
- [ ] Invalid data types return 422
- [ ] Missing authentication returns 401
- [ ] Missing mutation header returns 403
- [ ] File upload limits enforced (size, type)
- [ ] Output files are created and accessible

### File Operations
- [ ] File upload with valid PDF
- [ ] File upload with invalid content
- [ ] File upload exceeding size limit
- [ ] File download returns correct content
- [ ] Preview generation works
- [ ] Preview caching works

### Job Operations
- [ ] Job creation and tracking
- [ ] Job history retrieval
- [ ] Job detail retrieval
- [ ] Failed job handling
- [ ] Secret redaction in job options

## Coverage Strategy

### Priority 1: Core API (toolkitAPI.py)
- All 9 endpoints must have comprehensive tests
- Focus on: authentication, file operations, job management, history

### Priority 2: Engine APIs (pypdfAPI.py, pymupdfAPI.py)
- Test all public endpoints
- Focus on: PDF operations, validation, error handling

### Priority 3: Service Components
- Test pure functions and utilities
- Focus on: helpers, validators, processors

## Running Tests

```bash
# Run all tests
python3 -m unittest discover -s . -p "test_*.py" -v

# Run specific test file
python3 -m unittest apis.test_toolkitAPI -v

# Run specific test
python3 -m unittest apis.test_toolkitAPI.ToolkitAPITest.test_bootstrap -v
```

## Code Quality

- Keep tests independent (no shared state)
- Use temporary directories for file operations
- Clean up all resources in tearDown
- Avoid sleep() - use mocks for timing
- Tests should be fast (< 1 second each)
- Use subTest() for parameterized tests

## Example Test Patterns

### Testing File Upload
```python
def test_upload_valid_pdf(self):
    # Create test PDF
    with pymupdf.open() as doc:
        doc.new_page().insert_text((40, 70), "Test content")
        pdf_bytes = doc.tobytes()
    
    response = self.client.post(
        "/api/v1/files",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        headers={"x-toolkit-request": "1"}
    )
    
    self.assertEqual(response.status_code, 200)
    self.assertIn("id", response.json())
```

### Testing Authentication
```python
def test_missing_authentication(self):
    response = self.client.get("/api/v1/bootstrap")
    # Should set cookie and return 200
    self.assertEqual(response.status_code, 200)
    self.assertIn("pdf_toolkit_client", response.cookies)
```

### Testing Error Handling
```python
def test_invalid_file_type(self):
    response = self.client.post(
        "/api/v1/files",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers={"x-toolkit-request": "1"}
    )
    self.assertEqual(response.status_code, 415)
```

## Continuous Integration

- All tests must pass before merging
- Add new tests for new features
- Update tests when behavior changes
- Run full test suite on CI
