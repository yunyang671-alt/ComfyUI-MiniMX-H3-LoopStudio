"""CPU-only lifecycle checks; never import the real queue or load models."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("minimx_platform_config", Path(__file__).resolve().parents[1] / "platform_config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class OptionalServiceTests(unittest.TestCase):
    def test_default_does_not_import_queue(self):
        with patch.dict(config.os.environ, {}, clear=True), patch.object(config.importlib, "import_module") as load:
            result = config.initialize_batch_service()
        load.assert_not_called()
        self.assertFalse(result["batch_enabled"])

    def test_only_explicit_one_enables_service(self):
        for value in ("0", "true", "yes", ""):
            with self.subTest(value=value), patch.dict(config.os.environ, {config.BATCH_ENV: value}, clear=True), patch.object(config.importlib, "import_module") as load:
                self.assertFalse(config.initialize_batch_service()["batch_enabled"])
                load.assert_not_called()

    def test_enabled_loads_existing_service(self):
        with patch.dict(config.os.environ, {config.BATCH_ENV: "1"}, clear=True), patch.object(config.importlib, "import_module") as load:
            result = config.initialize_batch_service()
        load.assert_called_once_with(".batch_service", config.__package__)
        self.assertTrue(result["batch_enabled"])
        self.assertFalse(result["runninghub_member_supported"])

    def test_storage_failure_does_not_break_generation_registration(self):
        with patch.dict(config.os.environ, {config.BATCH_ENV: "1"}, clear=True), patch.object(config.importlib, "import_module", side_effect=PermissionError("read-only user directory")), patch.object(config.logging, "exception"):
            result = config.initialize_batch_service()
        self.assertTrue(result["batch_requested"])
        self.assertFalse(result["batch_enabled"])
        self.assertEqual(result["batch_error_type"], "PermissionError")


if __name__ == "__main__":
    unittest.main()
