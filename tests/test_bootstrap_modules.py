import pytest
from unittest.mock import patch, MagicMock
from lang.exceptions import DasmSyntaxError
from utils.modules import load_module


# 1. SUCCESS TEST: Module exists, has EXPORTS, and returns a valid object
@patch("importlib.import_module")
def test_load_module_success(mock_import):
    # Prepare a mocked module
    mock_module = MagicMock()
    mock_instance = "MyFactoryProduct"
    # EXPORTS must be callable, so set its return_value
    mock_module.EXPORTS.return_value = mock_instance
    mock_import.return_value = mock_module

    # Call the function under test
    result = load_module("plugins", "my_plugin")

    # Assertions
    assert result == "MyFactoryProduct"
    mock_import.assert_called_once_with("plugins.my_plugin")


# 2. SECURITY TEST: Attempted Path Traversal attack (e.g. "../") or invalid characters
@pytest.mark.parametrize("dir_name, module_name", [
    ("../malicious", "plugin"),       # Attempt to move up one directory
    ("plugins", "plugin;rm -rf /"),   # Disallowed special characters
    ("dir/sub", "name"),              # Slash in directory name
    ("plugins", "my-plugin"),         # Hyphen (if the regex disallows it)
])
def test_load_module_invalid_input_raises_error(dir_name, module_name):
    with pytest.raises(DasmSyntaxError) as exc_info:
        load_module(dir_name, module_name)

    assert "Bad name" in str(exc_info.value)


# 3. ERROR TEST: Module does not exist (ModuleNotFoundError)
@patch("importlib.import_module", side_effect=ModuleNotFoundError)
def test_load_module_not_found(mock_import):
    with pytest.raises(DasmSyntaxError) as exc_info:
        load_module("plugins", "nonexistent")

    assert "not found" in str(exc_info.value)


# 4. ERROR TEST: Module exists but has no EXPORTS attribute
@patch("importlib.import_module")
def test_load_module_missing_exports(mock_import):
    class DummyModuleWithoutExports:
        pass  # EXPORTS variable is missing

    mock_import.return_value = DummyModuleWithoutExports()

    with pytest.raises(DasmSyntaxError) as exc_info:
        load_module("plugins", "bad_plugin")

    assert "does not contain EXPORTS" in str(exc_info.value)


# 5. ERROR TEST: EXPORTS attribute exists but is not callable (e.g. a regular string)
@patch("importlib.import_module")
def test_load_module_exports_not_callable(mock_import):
    class DummyModuleInvalidExports:
        EXPORTS = "this is not a function or a class"  # String instead of a callable

    mock_import.return_value = DummyModuleInvalidExports()

    with pytest.raises(DasmSyntaxError) as exc_info:
        load_module("plugins", "string_plugin")

    assert "must be a function or a class" in str(exc_info.value)


@patch("importlib.import_module", side_effect=RuntimeError("boom"))
def test_load_module_import_error(mock_import):
    with pytest.raises(DasmSyntaxError) as exc_info:
        load_module("plugins", "broken_plugin")

    assert "Error importing module 'plugins/broken_plugin'" in str(exc_info.value)
    assert "boom" in str(exc_info.value)
