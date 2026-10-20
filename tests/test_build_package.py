"""Public packaging tests use synthetic temporary trees only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_package.py"
spec = importlib.util.spec_from_file_location("build_package", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.root = self.directory / builder.NAME
        self.root.mkdir()
        self.write("VERSION", "0.1.0\n")
        for relative, title, _ in builder.MODULES:
            self.write(relative, "# " + title + "\n\nSynthetic package text.\n")
        self.write("README.md", "Synthetic fixture, not scientific evidence.\n")
        self.write("LICENSE-REVIEW.md", "Human choice is pending.\n")
        self.write("LICENSE-MIT.proposed", "Synthetic license placeholder used only by unit tests.\n")
        self.archive = self.root / "dist" / (builder.NAME + "-0.1.0.zip")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_builder(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *map(str, extra)],
                              capture_output=True, check=False)

    def test_archive_uses_explicit_allowlist_and_relative_manifest(self):
        private = ("records/entry.md", "config.local.json", "config.local/secrets.txt", "config/account.json",
                   ".git/config", "dist/unreviewed.txt", "references/private-case.md",
                   "scripts/unreviewed.py", "tests/validation-results.json", "__pycache__/cache.pyc")
        for relative in private:
            self.write(relative, "Private or unreviewed fixture; never package.\n")
        self.write("config.example.json", '{"mode": "fill-and-review"}\n')
        result = self.run_builder()
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertEqual(manifest["license_status"], "pending-human-review")
        self.assertNotIn(str(self.root), json.dumps(manifest))
        names = {record["path"] for record in manifest["files"]}
        self.assertTrue(names.isdisjoint(private))
        self.assertIn("config.example.json", names)
        for name in names:
            self.assertFalse(Path(name).is_absolute())
            self.assertNotIn("..", Path(name).parts)
        with zipfile.ZipFile(self.archive) as archive:
            actual = set(archive.namelist())
            expected = {builder.NAME + "/" + name for name in names | {"manifest.json"}}
            self.assertEqual(actual, expected)
        verify = self.run_builder("--verify-only")
        self.assertEqual(verify.returncode, 0, verify.stderr.decode("utf-8"))
        self.assertTrue(json.loads(verify.stdout.decode("utf-8"))["verified"])

    def test_verify_detects_modified_payload_without_rebuilding(self):
        self.assertEqual(self.run_builder().returncode, 0)
        self.write("README.md", "Changed after manifest.\n")
        before = (self.root / "manifest.json").read_bytes()
        result = self.run_builder("--verify-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Manifest content mismatch", result.stderr)
        self.assertEqual((self.root / "manifest.json").read_bytes(), before)

    def test_existing_extra_install_file_is_not_deleted_or_overwritten(self):
        installed = self.directory / "installed" / builder.NAME
        installed.mkdir(parents=True)
        extra = installed / "private-notes.txt"
        extra.write_text("Preserve me", encoding="utf-8")
        result = self.run_builder("--install-dir", installed)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"no files copied or deleted", result.stderr)
        self.assertEqual(extra.read_text(encoding="utf-8"), "Preserve me")
        self.assertFalse((installed / "SKILL.md").exists())

    def test_fresh_explicit_install_matches_payload(self):
        installed = self.directory / "installed" / builder.NAME
        result = self.run_builder("--install-dir", installed)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        for source in builder.payload_files(self.root):
            destination = installed / source.relative_to(self.root)
            self.assertEqual(source.read_bytes(), destination.read_bytes())

    def test_zip_cannot_overwrite_source_and_version_is_single_source(self):
        result = self.run_builder("--zip-output", self.root / "source.zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "source.zip").exists())
        self.write("VERSION", "0.2.0-rc.1\n")
        result = self.run_builder()
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertTrue((self.root / "dist" / (builder.NAME + "-0.2.0-rc.1.zip")).is_file())

    def test_outside_symlink_payload_is_rejected_when_supported(self):
        outside = self.directory / "private.md"
        outside.write_text("Private fixture", encoding="utf-8")
        link = self.root / "README.md"
        link.unlink()
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("This environment does not permit creating test symlinks")
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.archive.exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "Private fixture")


if __name__ == "__main__":
    unittest.main()
