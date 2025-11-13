# ForgeERP Extension - API Reference

Complete API reference for the ForgeERP extension.

## ForgeERPTestBase

Main test base class that extends `SimpleTestBase` with ForgeERP-specific functionality.

### Navigation Methods

#### `go_to_setup() -> ForgeERPTestBase`

Navigate to setup page.

#### `go_to_provision() -> ForgeERPTestBase`

Navigate to provisioning page.

#### `go_to_status(client_name: Optional[str] = None, environment: Optional[str] = None) -> ForgeERPTestBase`

Navigate to status page. If client_name and environment are provided, navigates to specific status page.

#### `go_to_deploy() -> ForgeERPTestBase`

Navigate to deployment page.

#### `go_to_diagnostics() -> ForgeERPTestBase`

Navigate to diagnostics page.

#### `navigate_menu(menu_text: str) -> ForgeERPTestBase`

Navigate using the main menu. Menu text can be: Home, Setup, Provision, Status, Deploy, Diagnostics.

### Form Methods

#### `fill_provision_form(client_name: str, environment: str = "dev", database_type: Optional[str] = None, namespace: Optional[str] = None, **kwargs) -> ForgeERPTestBase`

Fill the provisioning form.

#### `fill_deploy_form(client_name: str, environment: str = "dev", chart_name: str = "generic", chart_version: Optional[str] = None, **kwargs) -> ForgeERPTestBase`

Fill the deployment form.

#### `fill_diagnostics_form(client_name: str, environment: str = "dev") -> ForgeERPTestBase`

Fill the diagnostics form.

#### `submit_form(button_selector: Optional[str] = None, wait_for_response: bool = True, container_selector: Optional[str] = None) -> ForgeERPTestBase`

Submit a form and wait for HTMX response.

### HTMX Methods

#### `wait_for_htmx_swap(container_selector: str, timeout: Optional[int] = None) -> ForgeERPTestBase`

Wait for HTMX swap to complete in a container.

#### `wait_for_htmx_loading(indicator_selector: str, timeout: Optional[int] = None, wait_for_hidden: bool = True) -> ForgeERPTestBase`

Wait for HTMX loading indicator to appear or disappear.

#### `detect_htmx_error(container_selector: str) -> Optional[str]`

Detect error messages in HTMX response container.

#### `get_htmx_result(container_id: str, wait_for_swap: bool = True, timeout: Optional[int] = None) -> str`

Get text content from HTMX result container.

#### `wait_for_htmx_response(container_selector: str, timeout: Optional[int] = None, check_for_errors: bool = True) -> ForgeERPTestBase`

Wait for HTMX response and optionally check for errors.

### Component Methods

#### `click_button(text: str, context: Optional[str] = None) -> ForgeERPTestBase`

Click a button by its visible text.

#### `fill_input_by_label(label: str, value: str, context: Optional[str] = None) -> ForgeERPTestBase`

Fill an input field by its visible label.

#### `select_option_by_label(label: str, option: str, context: Optional[str] = None) -> ForgeERPTestBase`

Select an option in a dropdown by its visible label.

#### `wait_for_modal(timeout: int = 10000) -> ForgeERPTestBase`

Wait for a modal to appear.

#### `close_modal() -> ForgeERPTestBase`

Close any open modal.

#### `get_card_content(card_selector: str) -> str`

Get text content from a card.

### Validation Methods

#### `assert_no_errors() -> ForgeERPTestBase`

Assert that no errors are displayed on the page.

#### `assert_success_message(expected_text: str) -> ForgeERPTestBase`

Assert that a success message is displayed.

#### `assert_status_display(client_name: str, environment: str) -> ForgeERPTestBase`

Assert that status is displayed for a client.

#### `assert_provision_success(client_name: str) -> ForgeERPTestBase`

Assert that provisioning was successful.

### Workflow Methods

#### `provision_client(client_name: str, environment: str = "dev", **options) -> ForgeERPTestBase`

Execute complete provisioning workflow.

#### `deploy_application(client_name: str, environment: str = "dev", chart_name: str = "generic", **options) -> ForgeERPTestBase`

Execute complete deployment workflow.

#### `check_status(client_name: str, environment: str = "dev") -> ForgeERPTestBase`

Check status of a provisioned client.

#### `run_diagnostics(client_name: Optional[str] = None, environment: Optional[str] = None) -> ForgeERPTestBase`

Run diagnostics. If client_name and environment are provided, runs client-specific diagnostics.

## ForgeERPSelectors

Class containing common ForgeERP selectors.

### Navigation Selectors

- `NAV_HOME` - Home navigation link
- `NAV_SETUP` - Setup navigation link
- `NAV_PROVISION` - Provision navigation link
- `NAV_STATUS` - Status navigation link
- `NAV_DEPLOY` - Deploy navigation link
- `NAV_DIAGNOSTICS` - Diagnostics navigation link

### Form Field Selectors

- `FIELD_CLIENT_NAME` - Client name input
- `FIELD_ENVIRONMENT` - Environment select/input
- `FIELD_DATABASE_TYPE` - Database type select
- `FIELD_NAMESPACE` - Namespace input
- `FIELD_CHART_NAME` - Chart name input
- `FIELD_CHART_VERSION` - Chart version input

### HTMX Container Selectors

- `HTMX_PROVISION_RESULT` - Provision result container
- `HTMX_DEPLOY_RESULT` - Deploy result container
- `HTMX_STATUS_RESULT` - Status result container
- `HTMX_DIAGNOSTICS_SUMMARY` - Diagnostics summary container
- `HTMX_CLIENT_DIAGNOSTICS` - Client diagnostics container

### Helper Methods

#### `get_nav_link(page: str) -> str`

Get navigation link selector for a page.

#### `get_htmx_result_container(page: str) -> str`

Get HTMX result container selector for a page.

#### `get_loading_indicator(page: str) -> str`

Get loading indicator selector for a page.

#### `get_form_field_selector(field_name: str) -> List[str]`

Get selectors for a form field by name.

## HTMX Helper

ForgeERP uses `HTMXHelper` from the core module for HTMX interactions.

The `ForgeERPTestBase` provides access via `self.htmx` which is an instance of `HTMXHelper`.

See [Core API Documentation](../../API.md#htmx-helper) for details on HTMX methods.

### Available via `test.htmx`:

- `wait_for_htmx_swap()` - Wait for HTMX swap to complete
- `wait_for_htmx_loading()` - Wait for HTMX loading indicator
- `detect_htmx_error()` - Detect error messages in HTMX response
- `get_htmx_result()` - Get text content from HTMX result container
- `wait_for_htmx_response()` - Wait for HTMX response and optionally check for errors
- `is_htmx_swapping()` - Check if HTMX is currently swapping content

## Generic Methods from SimpleTestBase

The following generic methods are available directly from `SimpleTestBase` (inherited by `ForgeERPTestBase`):

- `click_button(text, context=None)` - Click button by visible text
- `fill_by_label(label, value, context=None)` - Fill field by label
- `select_by_label(label, option, context=None)` - Select option by label
- `wait_for_modal(modal_selector=None, timeout=None)` - Wait for modal
- `close_modal(close_button_selector=None)` - Close modal
- `get_card_content(card_selector, description="")` - Get card content

See [Core API Documentation](../../API.md) for details.

## ForgeERPComponents

Helper class for ForgeERP-specific UI components.

### Methods

#### `fill_provision_form(client_name: str, environment: str = "dev", database_type: Optional[str] = None, namespace: Optional[str] = None, **kwargs) -> None`

Fill the provisioning form.

#### `fill_deploy_form(client_name: str, environment: str = "dev", chart_name: str = "generic", chart_version: Optional[str] = None, **kwargs) -> None`

Fill the deployment form.

#### `fill_diagnostics_form(client_name: str, environment: str = "dev") -> None`

Fill the diagnostics form.

#### `submit_form(button_selector: Optional[str] = None, wait_for_response: bool = True, container_selector: Optional[str] = None) -> None`

Submit a form and wait for HTMX response.

## ForgeERPWorkflows

Helper class for complete ForgeERP workflows.

### Methods

#### `provision_client(client_name: str, environment: str = "dev", **options) -> None`

Execute complete provisioning workflow.

#### `deploy_application(client_name: str, environment: str = "dev", chart_name: str = "generic", **options) -> None`

Execute complete deployment workflow.

#### `check_status(client_name: str, environment: str = "dev") -> str`

Check status of a provisioned client.

#### `run_diagnostics(client_name: Optional[str] = None, environment: Optional[str] = None) -> str`

Run diagnostics.

---

## ForgeERPYAMLParser

YAML parser with ForgeERP-specific actions support.

Extends `YAMLParser` from core with ForgeERP-specific actions for user-friendly YAML test definitions.

### Class Methods

#### `parse_file(yaml_path: Path) -> Dict[str, Any]`

Parse YAML test file with support for inheritance and composition (inherited from core).

#### `to_python_function(yaml_data: Dict[str, Any]) -> Callable`

Convert YAML test definition to Python function with ForgeERP support.

#### `load_test(yaml_path: Path) -> tuple[str, Callable]`

Load test from YAML file (inherited from core).

#### `load_tests(yaml_dir: Path) -> List[tuple[str, Callable]]`

Load all tests from YAML directory (inherited from core).

### Supported YAML Actions

#### Navigation
- `go_to_setup:` - Navigate to setup page
- `go_to_provision:` - Navigate to provision page
- `go_to_status:` - Navigate to status page (with optional `client_name` and `environment`)
- `go_to_deploy:` - Navigate to deploy page
- `go_to_diagnostics:` - Navigate to diagnostics page

#### Form Interactions
- `fill_provision_form:` - Fill provisioning form (dict with `client_name`, `environment`, `database_type`, `namespace`)
- `fill_deploy_form:` - Fill deployment form (dict with `client_name`, `environment`, `chart_name`, `chart_version`)
- `fill_diagnostics_form:` - Fill diagnostics form (dict with `client_name`, `environment`)
- `submit_form:` - Submit form (optional dict with `button_selector`, `wait_for_response`, `container_selector`)

#### Workflows
- `provision_client:` - Complete provisioning workflow (dict or simple client_name string)
- `deploy_application:` - Complete deployment workflow (dict or simple client_name string)
- `check_status:` - Check client status (dict or simple client_name string)
- `run_diagnostics:` - Run diagnostics (dict with optional `client_name` and `environment`, or empty for summary)

#### HTMX Actions
- `wait_for_htmx_swap:` - Wait for HTMX swap (container selector, optional `timeout`)
- `wait_for_htmx_loading:` - Wait for HTMX loading (optional indicator selector, `timeout`, `wait_for_hidden`)
- `get_htmx_result:` - Get HTMX result (container_id, optional `wait_for_swap`, `timeout`)

#### Validation
- `assert_no_errors:` - Assert no errors (optional dict with `result_container_selector`, `wait_after_error`)

#### Generic Actions
All generic actions from `SimpleTestBase` are also supported:
- `go_to:` - Navigate to URL
- `click:` - Click element (selector or button text)
- `type:` - Type text (dict with `selector` and `text`)
- `wait:` - Wait for seconds
- `screenshot:` - Take screenshot

### Example YAML

```yaml
name: provision_client_test
base_url: http://localhost:8000

config:
  cursor:
    color: "#6366f1"
  video:
    enabled: true

steps:
  - go_to_provision:
  - fill_provision_form:
      client_name: "my-client"
      environment: "dev"
      database_type: "postgresql"
  - submit_form:
  - assert_no_errors:
```

