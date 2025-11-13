# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Odoo Extra** (`playwright-simple[odoo]`)
  - `OdooTestBase` class for easy Odoo testing
  - Automatic version detection (Odoo 14-18)
  - Community and Enterprise edition support
  - Menu navigation (Community/Enterprise)
  - Field interaction (Many2one, Many2many, One2many, Char, Integer, Float, Date, Boolean, HTML)
  - View manipulation (List, Kanban, Form, Graph, Pivot)
  - Wizard and dialog handling
  - Workflow execution
  - YAML parser with Odoo-specific actions
  - Version-specific selectors with automatic fallback
  - Complete documentation and examples
- Core modules reorganized into `playwright_simple.core` package
  - Maintains backward compatibility
  - Cleaner structure for extensibility

### Changed
- Complete project structure with setup.py and pyproject.toml
- Comprehensive configuration system (TestConfig)
  - Support for YAML/JSON config files
  - Environment variable support
  - Runtime parameter overrides
  - Configuration validation
- SimpleTestBase class with full API
  - Navigation methods (go_to, back, forward, refresh, navigate)
  - Interaction methods (click, type, select, hover, drag, scroll)
  - Wait methods (wait, wait_for, wait_for_url, wait_for_text)
  - Assertion methods (assert_text, assert_visible, assert_url, assert_count, assert_attr)
  - Helper methods (login, fill_form, get_text, get_attr, is_visible, is_enabled)
  - Screenshot methods
- TestRunner for executing tests
  - Single test execution
  - Batch test execution
  - Parallel execution support
  - Test results and summary
- Video recording system
  - Per-test or global recording
  - Quality and codec configuration
  - Pause/resume support
- Screenshot system
  - Automatic screenshots on actions
  - Manual screenshots
  - Screenshot on failure
  - Full page and element screenshots
  - Smart organization by test name
- Custom cursor system
  - Multiple styles (arrow, dot, circle, custom)
  - Customizable color, size, animation
  - Click and hover effects
- Smart selector system
  - Automatic fallback strategies
  - Retry with exponential backoff
  - Helper methods (by_text, by_role, by_test_id, by_label)
- YAML parser for tests
  - Convert YAML test definitions to Python functions
  - Support for all test actions
- Complete documentation
  - README with quick start
  - API reference
  - Configuration guide
  - Examples guide
  - Troubleshooting guide
- Example tests
  - Basic Python examples
  - Advanced Python examples
  - YAML examples
  - Odoo integration example
  - E-commerce example
- CI/CD setup
  - GitHub Actions for testing
  - Automated publishing to PyPI
- Test suite
  - Unit tests for configuration
  - Unit tests for base class
  - Unit tests for runner

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Basic test execution
- Configuration via YAML/JSON
- Environment variable support
- Video recording
- Screenshot capture
- Custom cursor visualization

