"""Behavior tests with temporary inputs; never touch real experiment data."""
import importlib.util
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inspect_inputs.py"
spec = importlib.util.spec_from_file_location("inspect_inputs", SCRIPT)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def atom(serial="    1", name=" CA ", chain="A", resseq="   1", element="C", b=0.0, xyz=(1, 2, 3)):
    return (f"ATOM  {serial} {name} ALA {chain}{resseq}    "
            f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{1.0:6.2f}{b:6.2f}          {element:>2}\n")


def mrc_bytes(spacing=0.932, endian="<", dims=(2, 3, 4), origin=(0, 0, 0)):
    header = bytearray(1024)
    struct.pack_into(endian + "4i", header, 0, *dims, 2)
    struct.pack_into(endian + "3i", header, 28, *dims)
    struct.pack_into(endian + "3f", header, 40, *(n * spacing for n in dims))
    struct.pack_into(endian + "3f", header, 52, 90, 90, 90)
    struct.pack_into(endian + "3i", header, 64, 1, 2, 3)
    struct.pack_into(endian + "3f", header, 76, -0.1, 0.2, 0.01)
    struct.pack_into(endian + "3f", header, 196, *origin)
    struct.pack_into(endian + "f", header, 216, 0.02)
    header[208:212] = b"MAP "
    header[212:216] = b"DA\x00\x00" if endian == "<" else b"\x11\x11\x00\x00"
    return bytes(header) + b"\x00" * (dims[0] * dims[1] * dims[2] * 4)


def fsc_xml(axis="Resolution (A-1)", points=((0.1, 0.5), (0.2, 0.1), (0.3, 0.2), (0.4, 0.0))):
    return '<fsc xaxis="' + axis + '">' + ''.join(
        f'<coordinate><x>{x}</x><y>{y}</y></coordinate>' for x, y in points) + '</fsc>'


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = self.directory / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def test_log_successful_movie_targets_only_and_path_deduplication(self):
        source = self.write("actual.log", """Measured defocus = -14.31 microns
defined Range and Step (um) => [ -0.4, -2.5 ], [ 0.1 ].
TargetDefocus = -2.6 um
Measured defocus = -1.8 microns
Focusing was succeeded.
57 frames are being saved to X:\\Movies\\a.tif
57 frames are being saved to x:/Movies/a.tif
TargetDefocus = -0.4 um
Focusing was succeeded.
57 frames were saved to X:\\Movies\\b.tif
TargetDefocus = -9 um
57 frames are being saved to X:\\Movies\\c.tif
ZLP search width 40 eV
Item took 2.6 min
""")
        before = source.read_bytes()
        result = inspector.parse_log(source, expected_movies=6)
        self.assertEqual(result["fields"]["movie_count"]["value"], 3)
        self.assertEqual(result["coverage"]["movies_with_successful_target"], 2)
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertEqual(result["fields"]["observed_underfocus_range"]["value"], {"minimum": 400.0, "maximum": 2600.0})
        self.assertEqual(result["fields"]["exposure_time"]["status"], "unknown")
        self.assertEqual(result["fields"]["frames_per_movie"]["value"], 57)
        self.assertEqual(result["deduplication"]["duplicate_save_lines"], 1)
        self.assertIsNone(result["movie_records"][-1]["target_defocus_um"])
        self.assertIn("observed_targets_outside_declared_range", [w.get("code") for w in result["warnings"] if isinstance(w, dict)])
        self.assertEqual(source.read_bytes(), before)
        self.assertTrue(result["integrity"]["unchanged_in_inspected_scope"])

    def test_test_candidate_never_fills_actual_missing_parameter(self):
        actual = inspector.parse_log(self.write("actual.log", "57 frames are being saved to A.tif\n"))
        candidate = inspector.parse_log(self.write("shottest.txt", "ExposureTime = 2.5 s\n"), role="test")
        summary = inspector.acquisition_summary([actual, candidate])["exposure_time"]
        self.assertIsNone(summary["selected_value"])
        self.assertEqual(summary["status"], "unknown")
        self.assertEqual(summary["test_candidates"][0]["value"], 2.5)

    def test_test_sources_do_not_receive_actual_batch_coverage_denominator(self):
        log = inspector.parse_log(self.write("test.log", "57 frames are being saved to X:\\test\\a.tif\n"),
                                  role="test", expected_movies=2)
        mdoc = inspector.parse_mdoc(self.write("test.mdoc", "NumSubFrames = 57\nSubFramePath = X:\\test\\a.tif\n"),
                                    role="test", expected_movies=2)
        for result in (log, mdoc):
            with self.subTest(kind=result["kind"]):
                self.assertEqual(result["coverage"]["unique_movies"], 1)
                self.assertIsNone(result["coverage"]["expected_movies"])
                self.assertNotIn("fraction", result["coverage"])
                self.assertEqual(result["coverage"]["status"], "test_only")

    def test_actual_and_test_conflict_is_explicit(self):
        actual = inspector.parse_log(self.write("actual.log", "Exposure time: 1.5 seconds\n"))
        candidate = inspector.parse_log(self.write("test.log", "Record exposure time (s): 2.5 s\n"), role="test")
        summary = inspector.acquisition_summary([actual, candidate])["exposure_time"]
        self.assertEqual(summary["selected_value"], 1.5)
        self.assertTrue(summary["test_actual_differ"])

    def test_conflicting_actual_sources_have_no_selected_value(self):
        first = inspector.parse_log(self.write("first.log", "ExposureTime = 1.5 s\n"))
        second = inspector.parse_log(self.write("second.log", "ExposureTime = 2.0 s\n"))
        summary = inspector.acquisition_summary([first, second])["exposure_time"]
        self.assertEqual(summary["status"], "conflict")
        self.assertIsNone(summary["selected_value"])

    def test_actual_integer_log_and_float_mdoc_frames_are_same_setting(self):
        log = inspector.parse_log(self.write("actual.log", "60 frames are being saved to X:\\new\\a.tif\n"))
        mdoc = inspector.parse_mdoc(self.write("actual.mdoc", "NumSubFrames = 60\n"))
        summary = inspector.acquisition_summary([log, mdoc])["frames_per_movie"]
        self.assertEqual(summary["status"], "actual_observed")
        self.assertEqual(summary["selected_value"], 60)
        self.assertEqual(len(summary["actual_evidence"]), 2)

    def test_numeric_rounding_tolerance_does_not_hide_actual_sampling_change(self):
        first = inspector.parse_mdoc(self.write("first.mdoc", "PixelSpacing = 0.932\n"))
        rounded = inspector.parse_mdoc(self.write("rounded.mdoc", "PixelSpacing = 0.9319999573722718\n"))
        changed = inspector.parse_mdoc(self.write("changed.mdoc", "PixelSpacing = 0.933\n"))
        self.assertEqual(inspector.acquisition_summary([first, rounded])["pixel_spacing"]["status"], "actual_observed")
        self.assertEqual(inspector.acquisition_summary([first, changed])["pixel_spacing"]["status"], "conflict")
        self.assertFalse(inspector.values_equivalent(False, 0))
        self.assertTrue(inspector.values_equivalent({"minimum": 60, "unique_values": [60]}, {"minimum": 60.0, "unique_values": [60.0]}))

    def test_mdoc_explicit_settings_units_and_filename_with_spaces(self):
        path = self.write("movie.mdoc", """PixelSpacing = 0.466
ImageSize = 11520 8184
[ZValue = 0]
ExposureTime = 1.9
ExposureDose = 35
TargetDefocus = -1.5
Defocus = -1.49
NumSubFrames = 57
FilterSlitAndLoss = 20 0
SubFramePath = X:\\a folder\\movie 001.tif
""")
        result = inspector.parse_mdoc(path, expected_movies=3)
        f = result["fields"]
        self.assertEqual(f["exposure_time"]["value"], 1.9)
        self.assertEqual(f["pixel_spacing"]["value"], 0.466)
        self.assertEqual(f["target_defocus"]["value"], -1.5)
        self.assertEqual(f["measured_defocus"]["value"], -1.49)
        self.assertEqual(f["image_size"]["value"], [11520.0, 8184.0])
        self.assertEqual(f["filter_slit_width"]["value"], 20)
        self.assertEqual(f["subframe_paths"]["value"], [r"X:\a folder\movie 001.tif"])
        self.assertEqual(f["exposure_time"]["evidence"][0]["line"], 4)
        self.assertEqual(result["coverage"]["status"], "partial")

    def test_mdoc_invalid_numeric_value_is_not_inferred(self):
        result = inspector.parse_mdoc(self.write("bad.mdoc", "ExposureTime = unknown\nNumSubFrames = 57\n"))
        self.assertEqual(result["fields"]["exposure_time"]["status"], "unknown")
        self.assertEqual(result["fields"]["frames_per_movie"]["value"], 57)
        self.assertTrue(result["warnings"])

    def test_mdoc_conflicting_image_shapes_require_review(self):
        result = inspector.parse_mdoc(self.write("mixed.mdoc", "ImageSize = 11520 8184\n[ZValue = 0]\nImageSize = 5760 4092\n"))
        self.assertEqual(result["fields"]["image_size"]["status"], "conflict")
        summary = inspector.acquisition_summary([result])["image_size"]
        self.assertEqual(summary["status"], "conflict")
        self.assertIsNone(summary["selected_value"])

    def test_mdoc_zero_filter_width_means_slit_out_not_observed_zero_width(self):
        result = inspector.parse_mdoc(self.write("slitout.mdoc", "FilterSlitAndLoss = 0 0\n"))
        fields = result["fields"]
        self.assertEqual(fields["filter_slit_and_loss"]["value"], [0.0, 0.0])
        self.assertEqual(fields["filter_slit_state"]["value"], "slit_out")
        self.assertFalse(fields["filter_slit_active"]["value"])
        self.assertIsNone(fields["filter_slit_width"]["value"])
        self.assertEqual(fields["filter_slit_width"]["status"], "inactive")
        summary = inspector.acquisition_summary([result])["filter_slit_width"]
        self.assertEqual(summary["status"], "inactive")
        self.assertIsNone(summary["selected_value"])

    def test_actual_slit_out_not_replaced_by_test_active_width(self):
        actual = inspector.parse_mdoc(self.write("actual.mdoc", "FilterSlitAndLoss = 0 0\n"))
        test = inspector.parse_mdoc(self.write("test.mdoc", "FilterSlitAndLoss = 20 0\n"), role="test")
        summary = inspector.acquisition_summary([actual, test])["filter_slit_width"]
        self.assertEqual(summary["status"], "inactive")
        self.assertIsNone(summary["selected_value"])
        self.assertEqual(summary["test_candidates"][0]["value"], 20.0)

    def test_mixed_slit_states_do_not_select_one_width_for_batch(self):
        result = inspector.parse_mdoc(self.write("mixedfilter.mdoc", "FilterSlitAndLoss = 0 0\n[ZValue = 1]\nFilterSlitAndLoss = 20 0\n"))
        self.assertEqual(result["fields"]["filter_slit_state"]["value"], "mixed")
        self.assertIsNone(result["fields"]["filter_slit_width"]["value"])
        self.assertEqual(result["fields"]["filter_slit_width"]["status"], "conflict")
        self.assertEqual(inspector.acquisition_summary([result])["filter_slit_width"]["status"], "conflict")

    def test_mrc_little_and_big_endian_pixel_spacing_and_header_hash(self):
        for endian in ("<", ">"):
            with self.subTest(endian=endian):
                path = self.write("map" + str(ord(endian)) + ".mrc", mrc_bytes(endian=endian))
                before = path.read_bytes()
                result = inspector.parse_mrc(path)
                self.assertEqual(result["fields"]["dimensions_storage_crs"]["value"], [2, 3, 4])
                self.assertAlmostEqual(result["fields"]["pixel_spacing_xyz"]["value"][0], 0.932, places=6)
                self.assertEqual(result["integrity"]["bytes_inspected"], 1024)
                self.assertEqual(result["integrity"]["hash_scope"], "first 1024 bytes only")
                self.assertTrue(result["integrity"]["unchanged_in_inspected_scope"])
                self.assertEqual(path.read_bytes(), before)

    def test_mrc_mismatched_sampling_is_detected(self):
        first = inspector.parse_mrc(self.write("first.mrc", mrc_bytes(0.932)))
        second = inspector.parse_mrc(self.write("second.mrc", mrc_bytes(1.0)))
        comparison = inspector.compare_maps([first, second])[0]
        self.assertEqual(comparison["status"], "different_grid")
        self.assertIn("pixel_spacing_xyz", [d["field"] for d in comparison["differences"]])

    def test_mrc_truncation_and_invalid_header(self):
        short = inspector.parse_mrc(self.write("short.mrc", b"short"))
        self.assertFalse(short["fields"])
        missing_payload = inspector.parse_mrc(self.write("truncated.mrc", mrc_bytes()[:1024]))
        self.assertEqual(missing_payload["file_size_check"]["status"], "truncated")

    def test_mrc_nonfinite_header_origin_does_not_escape_json_or_grid_comparison(self):
        result = inspector.parse_mrc(self.write("nanorigin.mrc", mrc_bytes(origin=(float("nan"), 0, 0))))
        other = inspector.parse_mrc(self.write("normal.mrc", mrc_bytes()))
        self.assertEqual(result["fields"]["origin_xyz"]["status"], "invalid")
        self.assertIsNone(result["fields"]["origin_xyz"]["value"][0])
        self.assertEqual(inspector.compare_maps([result, other])[0]["status"], "unknown")
        json.dumps(result, allow_nan=False)

    def test_fsc_uses_first_downward_crossing_not_last_oscillation(self):
        result = inspector.parse_fsc(self.write("curve.xml", fsc_xml()))
        expected_frequency = 0.1 + (0.143 - 0.5) * 0.1 / (0.1 - 0.5)
        self.assertAlmostEqual(result["fields"]["first_descending_resolution"]["value"], 1 / expected_frequency)
        self.assertEqual(len(result["crossings"]), 3)
        self.assertEqual(result["crossings"][0]["direction"], "descending")
        self.assertNotEqual(result["crossings"][0]["resolution_angstrom"], result["crossings"][-1]["resolution_angstrom"])

    def test_fsc_unknown_units_and_invalid_order_not_guessed(self):
        unknown = inspector.parse_fsc(self.write("unknown.xml", fsc_xml("index")))
        self.assertEqual(unknown["fields"]["first_descending_resolution"]["status"], "unknown")
        unordered = inspector.parse_fsc(self.write("unsorted.xml", fsc_xml(points=((0.2, 0.5), (0.1, 0.0)))))
        self.assertIsNone(unordered["fields"]["first_descending_resolution"]["value"])

    def test_fsc_direct_resolution_axis_converted_in_frequency(self):
        result = inspector.parse_fsc(self.write("distance.xml", fsc_xml("Resolution (Angstrom)", ((10, 0.5), (5, 0.1)))))
        self.assertAlmostEqual(result["fields"]["first_descending_frequency"]["value"], 0.18925)

    def test_fsc_evidence_points_to_actual_multiline_coordinate(self):
        xml = '<fsc xaxis="Resolution (A-1)">\n<coordinate><x>0.1</x><y>0.5</y></coordinate>\n<coordinate><x>0.2</x><y>0.1</y></coordinate>\n</fsc>'
        result = inspector.parse_fsc(self.write("lines.xml", xml))
        ev = result["fields"]["first_descending_resolution"]["evidence"][0]
        self.assertEqual(ev["line"], 2)
        self.assertEqual(ev["next_line"], 3)

    def test_fsc_invalid_coordinate_prevents_interpolation_across_gap(self):
        xml = '<fsc xaxis="Resolution (A-1)"><coordinate><x>0.1</x><y>0.5</y></coordinate><coordinate><x>0.15</x><y>bad</y></coordinate><coordinate><x>0.2</x><y>0.1</y></coordinate></fsc>'
        result = inspector.parse_fsc(self.write("badcoordinate.xml", xml))
        self.assertIsNone(result["fields"]["first_descending_resolution"]["value"])

    def test_pdb_chain_identity_repetition_and_hydrogen_counts(self):
        data = atom(name=" CA ") + atom(serial="    2", name="1HB ", element="H") + "TER       3      ALA A   1\n"
        data += atom(serial="    4", name=" CA ", xyz=(4, 5, 6)) + "TER       5      ALA A   1\n"
        result = inspector.parse_pdb(self.write("repeated.pdb", data))
        counts = result["fields"]["counts"]["value"]
        self.assertEqual(counts["atoms"], 3)
        self.assertEqual(counts["hydrogen_atoms"], 1)
        self.assertEqual(counts["heavy_atoms"], 2)
        self.assertEqual(counts["segments"], 2)
        self.assertEqual(counts["duplicate_atom_identity_records"], 1)
        self.assertEqual(result["diagnostics"]["duplicate_atom_identity_examples"][0]["first_line"], 1)

    def test_pdb_models_do_not_merge_atom_identity_or_serials(self):
        data = "MODEL        1\n" + atom() + "ENDMDL\nMODEL        2\n" + atom(xyz=(4, 5, 6)) + "ENDMDL\n"
        result = inspector.parse_pdb(self.write("models.pdb", data))
        counts = result["fields"]["counts"]["value"]
        self.assertEqual(counts["models_with_atoms"], 2)
        self.assertEqual(counts.get("duplicate_atom_identity_records", 0), 0)
        self.assertEqual(counts.get("duplicate_atom_serial_records", 0), 0)

    def test_hybrid36_and_conect_distinguishes_ter_serial_from_atoms(self):
        self.assertEqual(inspector.hybrid36_decode(5, "A0000"), 100000)
        self.assertEqual(inspector.hybrid36_decode(5, "a0000"), 43770016)
        self.assertEqual(inspector.hybrid36_decode(4, "A000"), 10000)
        data = atom(serial="99999") + atom(serial="A0000", name=" N  ", element="N")
        data += "TER   A0001      ALA A   1\nCONECT99999A0000\nCONECTA0000A0001\n"
        result = inspector.parse_pdb(self.write("hybrid.pdb", data))
        self.assertEqual(result["diagnostics"]["hybrid36_atom_serial_examples"][0]["decoded"], 100000)
        dangling = result["diagnostics"]["unresolved_CONECT_examples"]
        self.assertEqual(len(dangling), 1)
        self.assertTrue(dangling[0]["references_TER_instead_of_atom"])
        self.assertEqual(dangling[0]["serial"], 100001)

    def test_nonfinite_coordinates_reported_and_not_emitted_as_nan(self):
        result = inspector.parse_pdb(self.write("nan.pdb", atom(xyz=(float("nan"), 2, 3))))
        self.assertEqual(result["fields"]["counts"]["value"]["invalid_coordinate_records"], 1)
        json.dumps(result, allow_nan=False)

    def test_duplicate_serial_makes_conect_ambiguous(self):
        source = atom() + atom(name=" N  ", element="N") + atom(serial="    2", name=" O  ", element="O") + "CONECT    1    2\n"
        result = inspector.parse_pdb(self.write("duplicateserial.pdb", source))
        self.assertEqual(result["fields"]["counts"]["value"]["duplicate_atom_serial_records"], 1)
        self.assertEqual(result["fields"]["counts"]["value"]["ambiguous_CONECT_references"], 1)
        self.assertEqual(result["diagnostics"]["ambiguous_CONECT_examples"][0]["serial"], 1)

    def test_ter_serial_collision_is_separate_from_atom_identity_collision(self):
        result = inspector.parse_pdb(self.write("tercollision.pdb", atom() + "TER       1      ALA A   1\n"))
        self.assertEqual(result["fields"]["counts"]["value"]["atom_TER_serial_collisions"], 1)
        self.assertEqual(result["diagnostics"]["serial_record_collision_examples"][0]["first_line"], 1)

    def test_cli_utf8_and_missing_input_error(self):
        path = self.write("采集.log", "ExposureTime = 1.25 s\n")
        run = subprocess.run([sys.executable, str(SCRIPT), "--log", str(path)], capture_output=True, check=False)
        self.assertEqual(run.returncode, 0)
        parsed = json.loads(run.stdout.decode("utf-8"))
        self.assertEqual(parsed["acquisition_summary"]["exposure_time"]["selected_value"], 1.25)
        self.assertTrue(parsed["read_only"])
        missing = subprocess.run([sys.executable, str(SCRIPT), "--pdb", str(self.directory / "missing.pdb")], capture_output=True)
        self.assertEqual(missing.returncode, 1)
        self.assertTrue(json.loads(missing.stdout.decode("utf-8"))["inputs"][0]["error"])

    def test_forward_case_keeps_missing_actual_exposure_unknown_and_inputs_unchanged(self):
        fixture = Path(__file__).resolve().parent / "forward-case"
        inputs = [fixture / "actual.log", fixture / "new_movie.mdoc", fixture / "shottest.log"]
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
        run = subprocess.run([sys.executable, str(SCRIPT), "--log", str(inputs[0]),
                              "--mdoc", str(inputs[1]), "--test-log", str(inputs[2]),
                              "--expected-movies", "4"], capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8"))
        result = json.loads(run.stdout.decode("utf-8"))
        exposure = result["acquisition_summary"]["exposure_time"]
        self.assertEqual(exposure["status"], "unknown")
        self.assertIsNone(exposure["selected_value"])
        self.assertEqual(exposure["test_candidates"][0]["value"], 2.5)
        self.assertEqual(result["inputs"][0]["coverage"]["status"], "partial")
        self.assertEqual(result["inputs"][0]["fields"]["frames_per_movie"]["value"], 60)
        self.assertTrue(result["read_only"])
        self.assertEqual(before, {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs})


if __name__ == "__main__":
    unittest.main()
