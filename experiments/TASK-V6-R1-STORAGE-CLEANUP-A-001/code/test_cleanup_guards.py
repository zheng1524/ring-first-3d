import importlib.util
import os
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('execute_audit_batch.py')


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('cleanup_executor', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_protected_descendant_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / 'protected'
            parent.mkdir()
            child = parent / 'asset.bin'
            child.write_bytes(b'asset')
            self.assertTrue(self.module.is_protected(str(child), [str(parent)]))

    def test_changed_hash_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            item_path = pathlib.Path(tmp) / 'asset.bin'
            item_path.write_bytes(b'changed')
            item = {'path': str(item_path), 'realpath': str(item_path),
                    'file_type': 'regular', 'size_bytes': 7,
                    'sha256': '0' * 64}
            result = self.module.check_item(item, [], set())
            self.assertEqual(result['status'], 'SKIPPED')
            self.assertIn('SHA256', result['reason'])

    def test_hardlink_is_not_counted_as_reclaimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = pathlib.Path(tmp) / 'first'
            second = pathlib.Path(tmp) / 'second'
            first.write_bytes(b'x' * 100)
            os.link(first, second)
            self.assertEqual(self.module.recoverable_blocks(first.stat()), 0)

    def test_progress_journal_recovers_latest_item_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = pathlib.Path(tmp) / 'progress.ndjson'
            self.module.append_progress(journal, 0, {'status': 'DELETED', 'path': 'first'})
            self.module.append_progress(journal, 1, {'status': 'SKIPPED', 'path': 'second'})
            self.assertEqual(self.module.load_progress(journal), {
                0: {'status': 'DELETED', 'path': 'first'},
                1: {'status': 'SKIPPED', 'path': 'second'},
            })

    def test_proc_snapshot_sees_open_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'held.bin'
            path.write_bytes(b'held')
            with path.open('rb'):
                self.assertIn(str(path), self.module.proc_open_paths())


if __name__ == '__main__':
    unittest.main()
