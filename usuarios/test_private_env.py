import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.conf import settings
from django.test import SimpleTestCase
from petcare_core.runtime_env import load_private_environment


class PrivateEnvironmentTests(SimpleTestCase):
    def test_values_are_parsed_without_shell_execution(self):
        with TemporaryDirectory(dir=settings.BASE_DIR) as folder:
            path=Path(folder)/'private.env'
            path.write_text("DB_PASSWORD='literal-$value-#test'\nDB_USER=sample\n",encoding='utf-8')
            with patch.dict(os.environ,{'PETCARE_ENV_FILE':str(path)},clear=True):
                load_private_environment()
                self.assertEqual(os.environ['DB_PASSWORD'],'literal-$value-#test')

    def test_process_environment_has_priority(self):
        with TemporaryDirectory(dir=settings.BASE_DIR) as folder:
            path=Path(folder)/'private.env';path.write_text('DB_USER=from_file\n',encoding='utf-8')
            with patch.dict(os.environ,{'PETCARE_ENV_FILE':str(path),'DB_USER':'from_process'},clear=True):
                load_private_environment();self.assertEqual(os.environ['DB_USER'],'from_process')

    def test_explicit_missing_file_fails_without_disclosing_values(self):
        with TemporaryDirectory(dir=settings.BASE_DIR) as folder:
            with patch.dict(os.environ,{'PETCARE_ENV_FILE':str(Path(folder)/'absent')},clear=True):
                with self.assertRaises(RuntimeError):load_private_environment()
