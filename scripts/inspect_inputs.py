#!/usr/bin/env python3
"""Read-only deposition evidence inspector; Python 3.7+, standard library only.

All outputs are observations, never instructions to change input data. Actual
and test acquisitions are separate. MRC data arrays are never read: only the
first 1024 bytes are inspected and hashed. Run --help for CLI examples.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET

SCHEMA_VERSION = "1.0"
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
MAX_EVIDENCE = 8


def decode_text(data):
    for encoding in ("utf-8-sig", "gb18030", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace"), "utf-8-replacement"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def evidence(line=None, text=None, **extra):
    result = {"line": line}
    if text is not None:
        result["text"] = text[:240]
    result.update(extra)
    return result


def field(value, unit, path, ev=(), coverage=None, status="observed", **extra):
    nonfinite = []
    def clean(item):
        if isinstance(item, float) and not math.isfinite(item):
            nonfinite.append(True)
            return None
        if isinstance(item, dict):
            return {key: clean(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(val) for val in item]
        return item
    value = clean(value)
    if nonfinite:
        status = "invalid"
        extra["reason"] = "Non-finite source value replaced by null; do not use this field"
    result = {"value": value, "unit": unit, "source_file": str(path),
              "evidence": list(ev)[:MAX_EVIDENCE],
              "coverage": coverage or {"scope": "this file only"}, "status": status}
    result.update(extra)
    return result


def unknown(unit, path, coverage=None, reason="No explicit source value found"):
    return field(None, unit, path, coverage=coverage, status="unknown", reason=reason)


def numeric_summary(values):
    unique = sorted(set(values))
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return {"minimum": unique[0], "maximum": unique[-1],
            "unique_values": unique[:64], "unique_count": len(unique)}


def numeric_evidence(records):
    """Retain both extrema before early samples, so ranges have auditable lines."""
    if not records:
        return []
    chosen = [min(records, key=lambda rec: rec[0]), max(records, key=lambda rec: rec[0])]
    chosen += list(records)[:MAX_EVIDENCE]
    output, seen = [], set()
    for _, ev, *_ in chosen:
        key = json.dumps(ev, sort_keys=True)
        if key not in seen:
            output.append(ev)
            seen.add(key)
    return output[:MAX_EVIDENCE]


def make_result(path, kind, role, data, scope="entire file"):
    return {"kind": kind, "role": role, "source_file": str(path), "fields": {},
            "warnings": [], "integrity": {"hash_scope": scope,
            "sha256_before": sha256(data), "bytes_inspected": len(data)}}


def finish_integrity(result, path, size=None):
    with open(path, "rb") as stream:
        current = stream.read(size) if size is not None else stream.read()
    result["integrity"]["sha256_after"] = sha256(current)
    result["integrity"]["unchanged_in_inspected_scope"] = (
        result["integrity"]["sha256_before"] == sha256(current))
    if not result["integrity"]["unchanged_in_inspected_scope"]:
        result["warnings"].append("Input changed during inspection; do not use these observations.")
    return result


def parse_log(path, role="actual", expected_movies=None):
    if role == "test":
        expected_movies = None  # a test file never measures formal acquisition coverage
    path = Path(path)
    data = path.read_bytes()
    text, encoding = decode_text(data)
    result = make_result(path, "serialem_log", role, data)
    result["encoding"] = encoding
    records, declarations, targets = {}, [], []
    explicit = defaultdict(list)
    target = None
    successful_target = None
    successful_line = None
    duplicate_saves, conflicting_saves, excluded_measured = 0, [], 0
    acquisition_warnings = []
    for number, line in enumerate(text.splitlines(), 1):
        ev = evidence(number, line.strip())
        declaration = re.search(r"defined\s+Range\s+and\s+Step.*?\[\s*(" + NUM +
                                r")\s*,\s*(" + NUM + r")\s*\].*?\[\s*(" + NUM + r")", line, re.I)
        if declaration:
            declarations.append((tuple(float(v) for v in declaration.groups()), ev))
        match = re.search(r"\bTargetDefocus\s*=\s*(" + NUM + r")\s*(?:um|microns?|µm|μm)\b", line, re.I)
        if match:
            target = (float(match.group(1)), ev)
            targets.append(target)
            successful_target = None  # never reuse a previous successful target after a new request
        if re.search(r"Focusing\s+was\s+succeeded|Autofocus\s+(?:was\s+)?successful", line, re.I):
            successful_target = target
            successful_line = number
        if re.search(r"Measured\s+def(?:ocus|oucs)", line, re.I):
            excluded_measured += 1
        if re.search(r"^\s*WARNING:.*(?:Column valves closed|beam off|acquiring image)", line, re.I):
            acquisition_warnings.append(ev)
        movie = re.search(r"(\d+)\s+frames\s+(?:are\s+being|were)\s+saved\s+to\s+(.+?)\s*$", line, re.I)
        if movie:
            movie_path = movie.group(2).strip().strip('"')
            key = movie_path.replace("/", "\\").casefold()
            rec = {"path": movie_path, "frames": int(movie.group(1)), "saved_line": number,
                   "target_defocus_um": successful_target[0] if successful_target else None,
                   "target_line": successful_target[1]["line"] if successful_target else None,
                   "focus_success_line": successful_line if successful_target else None}
            if key in records:
                duplicate_saves += 1
                if (records[key]["frames"], records[key]["target_defocus_um"]) != (rec["frames"], rec["target_defocus_um"]):
                    conflicting_saves.append(rec)
            else:
                records[key] = rec
        # Explicit settings only. A timing interval, "took", or frame count is not exposure.
        rules = {
            "exposure_time": (r"(?:\bExposureTime|\b(?:Record\s+)?exposure\s+time)\s*(?:\((?:s|seconds?)\))?\s*[:=]\s*(" + NUM + r")\s*(?:s(?:ec(?:onds?)?)?\b|$)", "s"),
            "pixel_spacing": (r"\b(?:PixelSpacing|pixel\s+(?:spacing|size))\s*[:=]\s*(" + NUM + r")\s*(?:A(?:ngstroms?)?|Å)\b", "angstrom"),
            "voltage": (r"\b(?:Voltage|accelerating\s+voltage)\s*[:=]\s*(" + NUM + r")\s*kV\b", "kV"),
            "exposure_dose": (r"\b(?:ExposureDose|(?:total\s+)?dose)\s*[:=]\s*(" + NUM + r")\s*(?:e[-−]?\s*/\s*(?:A|Å)(?:\^?2|²))", "electron/angstrom^2"),
        }
        for name, (pattern, unit) in rules.items():
            found = re.search(pattern, line, re.I)
            if found:
                explicit[name].append((float(found.group(1)), ev, unit))
    movies = list(records.values())
    linked = [rec for rec in movies if rec["target_defocus_um"] is not None]
    coverage = {"unique_movies": len(movies), "movies_with_successful_target": len(linked),
                "expected_movies": expected_movies,
                "scope": ("test/script candidate movie saves only; formal batch coverage is not applicable" if role == "test" else
                          "movie saves in this file; batch completeness requires an external inventory"),
                "status": ("test_only" if role == "test" else "partial" if expected_movies and len(movies) < expected_movies else
                           "matches_expected_count" if expected_movies == len(movies) else
                           "exceeds_expected_count" if expected_movies else "unknown")}
    if expected_movies:
        coverage["fraction"] = len(movies) / expected_movies
    result["coverage"] = coverage
    f = result["fields"]
    f["movie_count"] = field(len(movies), "movies", path,
                              [evidence(rec["saved_line"], rec["path"]) for rec in movies], coverage)
    f["frames_per_movie"] = field(numeric_summary([r["frames"] for r in movies]), "frames", path,
                                   [evidence(r["saved_line"], r["path"]) for r in movies], coverage,
                                   status="observed" if movies else "unknown")
    observed_values = [r["target_defocus_um"] for r in linked]
    target_records = [(r["target_defocus_um"],
        evidence(r["target_line"], f"TargetDefocus={r['target_defocus_um']}; saved movie", movie=r["path"],
                 saved_line=r["saved_line"], focus_success_line=r["focus_success_line"])) for r in linked]
    f["successful_movie_target_defocus"] = field(numeric_summary(observed_values), "um_signed", path,
        numeric_evidence(target_records),
        coverage, status="observed" if linked else "unknown")
    negative = [-v * 1000 for v in observed_values if v <= 0]
    f["observed_underfocus_range"] = field(
        {"minimum": min(negative), "maximum": max(negative)} if negative else None,
        "nm_underfocus_magnitude", path, f["successful_movie_target_defocus"]["evidence"], coverage,
        status="calculated" if negative else "unknown",
        reason="Magnitude of explicitly logged successful negative targets; not CTF-estimated defocus")
    unique_decl = list(dict.fromkeys(d[0] for d in declarations))
    f["declared_target_range"] = field(
        [{"minimum": min(d[0], d[1]), "maximum": max(d[0], d[1]), "step": d[2]} for d in unique_decl] or None,
        "um_signed", path, [d[1] for d in declarations], coverage,
        status="declared" if declarations else "unknown")
    for name, unit in (("exposure_time", "s"), ("pixel_spacing", "angstrom"),
                       ("voltage", "kV"), ("exposure_dose", "electron/angstrom^2")):
        vals = explicit[name]
        f[name] = (field(numeric_summary([v[0] for v in vals]), unit, path, numeric_evidence(vals), coverage)
                   if vals else unknown(unit, path, coverage))
    result["movie_records"] = movies
    result["excluded"] = {"measured_defocus_lines": excluded_measured,
                          "reason": "Intermediate autofocus/stage-Z measurements are not acquisition target settings"}
    result["deduplication"] = {"key": "case-insensitive normalized saved movie path",
                               "duplicate_save_lines": duplicate_saves, "conflicting_save_examples": conflicting_saves[:8]}
    if acquisition_warnings:
        result["warnings"].append({"code": "acquisition_warning_in_source", "count": len(acquisition_warnings),
                                   "examples": acquisition_warnings[:8],
                                   "reason": "A saved filename does not prove a usable exposure or accepted reconstruction input."})
    if declarations and observed_values:
        outside = [v for v in set(observed_values) if not any(min(d[0], d[1]) - 1e-8 <= v <= max(d[0], d[1]) + 1e-8 for d in unique_decl)]
        if outside:
            result["warnings"].append({"code": "observed_targets_outside_declared_range", "values_um_signed": sorted(outside)})
    if any(v > 0 for v in observed_values):
        result["warnings"].append("Positive target defocus detected; underfocus magnitude summary excludes these values.")
    if conflicting_saves:
        result["warnings"].append("Repeated movie paths have inconsistent values; do not silently choose one.")
    if role == "test":
        result["warnings"].append("Test/script candidate only: do not replace actual acquisition evidence with these values.")
    return finish_integrity(result, path)


MDOC_FIELDS = {
    "ExposureTime": ("exposure_time", "s", 1),
    "TargetDefocus": ("target_defocus", "um_signed", 1),
    "Defocus": ("measured_defocus", "um_signed", 1),
    "PixelSpacing": ("pixel_spacing", "angstrom", 1),
    "ExposureDose": ("exposure_dose", "electron/angstrom^2", 1),
    "NumSubFrames": ("frames_per_movie", "frames", 1),
    "Voltage": ("voltage", "kV", 1),
    "Magnification": ("magnification", "fold", 1),
    "Binning": ("binning", "factor", 1),
    "ImageSize": ("image_size", "pixels", 2),
    "FilterSlitAndLoss": ("filter_slit_and_loss", "eV_width_and_loss", 2),
}


def parse_mdoc(path, role="actual", expected_movies=None):
    if role == "test":
        expected_movies = None
    path = Path(path)
    data = path.read_bytes()
    text, encoding = decode_text(data)
    result = make_result(path, "serialem_mdoc", role, data)
    result["encoding"] = encoding
    entries = defaultdict(list)
    paths, section_count, bad = {}, 0, []
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"\[\s*ZValue\s*=", line, re.I):
            section_count += 1
        match = re.match(r"\s*(\w+)\s*=\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        ev = evidence(number, line.strip(), section=section_count)
        if key == "SubFramePath":
            normalized = value.strip('"').replace("/", "\\").casefold()
            paths.setdefault(normalized, (value.strip('"'), ev))
        if key in MDOC_FIELDS:
            name, unit, count = MDOC_FIELDS[key]
            try:
                values = [float(part) for part in value.split()]
                if len(values) != count or not all(math.isfinite(v) for v in values):
                    raise ValueError("invalid arity or non-finite value")
                if name in ("frames_per_movie", "image_size", "binning") and any(v != int(v) for v in values):
                    raise ValueError("expected integer")
                parsed = values[0] if count == 1 else values
                entries[name].append((parsed, ev, unit))
            except ValueError as error:
                bad.append({"line": number, "field": key, "reason": str(error)})
    coverage = {"unique_movies": len(paths) if paths else None,
                "zvalue_sections": section_count, "expected_movies": expected_movies,
                "scope": ("test mdoc candidate only; formal batch coverage is not applicable" if role == "test" else
                          "this mdoc only; section count does not prove complete batch coverage"),
                "status": ("test_only" if role == "test" else "partial" if expected_movies and paths and len(paths) < expected_movies else
                           "matches_expected_count" if paths and expected_movies == len(paths) else "unknown")}
    result["coverage"] = coverage
    f = result["fields"]
    for _, (name, unit, count) in MDOC_FIELDS.items():
        vals = entries[name]
        if not vals:
            f[name] = unknown(unit, path, coverage)
        elif count == 1:
            f[name] = field(numeric_summary([v[0] for v in vals]), unit, path, numeric_evidence(vals), coverage)
        else:
            unique = list(dict.fromkeys(tuple(v[0]) for v in vals))
            f[name] = field(list(unique[0]) if len(unique) == 1 else [list(v) for v in unique],
                            unit, path, [v[1] for v in vals], coverage,
                            status="observed" if len(unique) == 1 else "conflict")
    f["movie_count"] = field(len(paths) if paths else None, "movies", path,
                              [p[1] for p in paths.values()], coverage,
                              status="observed" if paths else "unknown")
    f["subframe_paths"] = field([p[0] for p in paths.values()], "path", path,
                                 [p[1] for p in paths.values()], coverage,
                                 status="observed" if paths else "unknown")
    slit = entries["filter_slit_and_loss"]
    # SerialEM stores width=0 when the slit is out. This is a state marker,
    # not an observed zero-eV active slit width to copy into OneDep.
    if not slit:
        f["filter_slit_state"] = unknown(None, path, coverage)
        f["filter_slit_active"] = unknown("boolean", path, coverage)
        f["filter_slit_width"] = unknown("eV", path, coverage)
        f["filter_energy_loss"] = unknown("eV", path, coverage)
    else:
        active = [v for v in slit if v[0][0] > 0]
        inactive = [v for v in slit if v[0][0] == 0]
        invalid = [v for v in slit if v[0][0] < 0]
        mixed = bool(active and inactive)
        state = "invalid" if invalid else "mixed" if mixed else "slit_in" if active else "slit_out"
        f["filter_slit_state"] = field(state, None, path, [v[1] for v in slit], coverage,
                                        "invalid" if invalid else "conflict" if mixed else "observed")
        f["filter_slit_active"] = field(None if invalid or mixed else bool(active), "boolean", path,
                                         [v[1] for v in slit], coverage,
                                         "invalid" if invalid else "conflict" if mixed else "observed")
        if invalid or mixed:
            f["filter_slit_width"] = field(None, "eV", path, [v[1] for v in slit], coverage,
                "invalid" if invalid else "conflict",
                reason="Negative width or mixed slit-in/slit-out states; review per-movie source settings")
            f["filter_energy_loss"] = field(None, "eV", path, [v[1] for v in slit], coverage,
                "invalid" if invalid else "conflict", reason="No single active filter state")
            result["warnings"].append("Energy-filter slit state is mixed/invalid; do not auto-fill one batch-wide active width.")
        elif inactive:
            f["filter_slit_width"] = field(None, "eV", path, [v[1] for v in inactive], coverage,
                "inactive", reason="FilterSlitAndLoss width=0 means slit out; zero is not an active slit width")
            f["filter_energy_loss"] = field(None, "eV", path, [v[1] for v in inactive], coverage,
                "inactive", reason="Slit out; raw loss setting is retained in filter_slit_and_loss")
        else:
            f["filter_slit_width"] = field(numeric_summary([v[0][0] for v in active]), "eV", path,
                numeric_evidence([(v[0][0], v[1]) for v in active]), coverage)
            f["filter_energy_loss"] = field(numeric_summary([v[0][1] for v in active]), "eV", path,
                numeric_evidence([(v[0][1], v[1]) for v in active]), coverage)
    if bad:
        result["warnings"].append({"code": "unparsed_mdoc_settings", "examples": bad[:8]})
    if role == "test":
        result["warnings"].append("Test mdoc candidate only; actual data take precedence, with conflicts retained.")
    return finish_integrity(result, path)


def parse_mrc(path):
    path = Path(path)
    with path.open("rb") as stream:
        data = stream.read(1024)
    result = make_result(path, "mrc_header", "actual", data, "first 1024 bytes only")
    result["coverage"] = {"scope": "header only; voxel data were not read or validated"}
    if len(data) < 1024:
        result["warnings"].append("Header shorter than 1024 bytes.")
        return finish_integrity(result, path, 1024)
    candidates = []
    for endian in ("<", ">"):
        dims = struct.unpack_from(endian + "3i", data, 0)
        mode = struct.unpack_from(endian + "i", data, 12)[0]
        axes = struct.unpack_from(endian + "3i", data, 64)
        grid = struct.unpack_from(endian + "3i", data, 28)
        lengths = struct.unpack_from(endian + "3f", data, 40)
        sane = all(0 < n <= 10000000 for n in dims) and mode in (0, 1, 2, 3, 4, 6, 12, 16)
        if sane:
            score = (set(axes) == {1, 2, 3}) + (all(0 < n <= 10000000 for n in grid))
            score += all(math.isfinite(v) and 0 < v < 1e12 for v in lengths)
            stamp = data[212:216]
            score += 2 * ((endian == "<" and stamp[:2] in (b"DA", b"DD")) or
                          (endian == ">" and stamp[:2] == b"\x11\x11"))
            candidates.append((score, endian))
    if not candidates:
        result["warnings"].append("Neither byte order has plausible dimensions/mode; not a usable MRC header.")
        return finish_integrity(result, path, 1024)
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        result["warnings"].append("Ambiguous byte order; no header values selected.")
        return finish_integrity(result, path, 1024)
    endian = candidates[0][1]
    read_i = lambda offset, count=1: list(struct.unpack_from(endian + str(count) + "i", data, offset))
    read_f = lambda offset, count=1: list(struct.unpack_from(endian + str(count) + "f", data, offset))
    coverage = result["coverage"]
    def add(name, value, unit, offset, status="observed"):
        result["fields"][name] = field(value, unit, path,
            [evidence(None, byte_offset=offset, origin="MRC header")], coverage, status=status)
    dims, mode, grid, lengths, axes = read_i(0, 3), read_i(12)[0], read_i(28, 3), read_f(40, 3), read_i(64, 3)
    add("byte_order", "little" if endian == "<" else "big", None, 212)
    add("dimensions_storage_crs", dims, "voxels", 0)
    add("mode", mode, "MRC mode", 12)
    add("starts_crs", read_i(16, 3), "voxels", 16)
    add("sampling_grid_xyz", grid, "voxels", 28)
    add("cell_lengths_xyz", lengths, "angstrom", 40)
    add("cell_angles", read_f(52, 3), "degrees", 52)
    add("axis_mapping_crs_to_xyz", axes, "axis indices", 64)
    add("origin_xyz", read_f(196, 3), "angstrom", 196)
    add("header_minimum", read_f(76)[0], "map units", 76)
    add("header_maximum", read_f(80)[0], "map units", 80)
    add("header_mean", read_f(84)[0], "map units", 84)
    add("header_rms", read_f(216)[0], "map units", 216)
    if all(n > 0 for n in grid) and all(math.isfinite(v) and v > 0 for v in lengths):
        spacing = [v / n for v, n in zip(lengths, grid)]
        add("pixel_spacing_xyz", spacing, "angstrom", 28, "calculated")
    else:
        result["fields"]["pixel_spacing_xyz"] = unknown("angstrom", path, coverage, "Invalid/zero cell length or sampling grid")
    if set(axes) != {1, 2, 3}:
        result["warnings"].append("Axis mapping is not a permutation of 1,2,3.")
    if data[208:212] != b"MAP ":
        result["warnings"].append("Missing MAP signature; may be an older CCP4/MRC variant. Verify format before use.")
    nsymbt = read_i(92)[0]
    bpp = {0: 1, 1: 2, 2: 4, 3: 4, 4: 8, 6: 2, 12: 2, 16: 3}[mode]
    expected_size = 1024 + nsymbt + dims[0] * dims[1] * dims[2] * bpp
    add("extended_header_bytes", nsymbt, "bytes", 92)
    result["file_size_check"] = {"actual_bytes": path.stat().st_size, "expected_minimum_bytes": expected_size,
                                 "status": "truncated" if path.stat().st_size < expected_size or nsymbt < 0 else "size_plausible"}
    if result["file_size_check"]["status"] == "truncated":
        result["warnings"].append("File size is smaller than header-declared voxel data, or extended header is invalid.")
    result["warnings"].append("Header statistics are stored metadata, not recomputed density statistics. Matching grids do not prove map/half-map correspondence.")
    return finish_integrity(result, path, 1024)


def local_tag(tag):
    return tag.rsplit("}", 1)[-1]


def parse_fsc(path, threshold=0.143):
    path = Path(path)
    data = path.read_bytes()
    text, encoding = decode_text(data)
    result = make_result(path, "fsc_xml", "actual", data)
    result["encoding"] = encoding
    coverage = {"scope": "this FSC curve only; pairing with maps/mask requires provenance"}
    result["coverage"] = coverage
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        result["warnings"].append({"code": "invalid_xml", "reason": str(error)})
        return finish_integrity(result, path)
    xaxis = root.get("xaxis", "")
    normalized = xaxis.lower().replace("å", "a").replace("angstroms", "a").replace("angstrom", "a")
    freq_axis = bool(re.search(r"(?:a\s*[-^]\s*1|1\s*/\s*a|a⁻¹|inverse\s*a)", normalized))
    distance_axis = bool(re.search(r"resolution.*\(\s*a\s*\)", normalized)) and not freq_axis
    ev = [evidence(1, f"xaxis={xaxis}; title={root.get('title', '')}")]
    f = result["fields"]
    f["xaxis"] = field(xaxis, None, path, ev, coverage,
                       status="observed" if freq_axis or distance_axis else "unknown")
    f["title"] = field(root.get("title"), None, path, ev, coverage)
    f["threshold"] = field(threshold, "FSC", path, [], coverage, "analysis_setting")
    points = []
    coordinate_lines = [text.count("\n", 0, match.start()) + 1
                        for match in re.finditer(r"<(?:[\w.-]+:)?coordinate(?:\s[^>]*)?>", text)]
    coordinate_index = 0
    invalid_coordinates = 0
    for node in root.iter():
        if local_tag(node.tag) != "coordinate":
            continue
        line_number = coordinate_lines[coordinate_index] if coordinate_index < len(coordinate_lines) else None
        coordinate_index += 1
        values = {local_tag(child.tag): child.text for child in node}
        try:
            x, y = float(values["x"]), float(values["y"])
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError("non-finite")
            points.append((x, y, line_number, coordinate_index))
        except (KeyError, TypeError, ValueError):
            invalid_coordinates += 1
            result["warnings"].append("Invalid coordinate skipped; check source curve.")
    f["coordinate_count"] = field(len(points), "coordinates", path, ev, coverage)
    if invalid_coordinates:
        f["first_descending_resolution"] = unknown("angstrom", path, coverage, "Invalid source coordinate; no interpolation across gaps")
        result["warnings"].append("At least one invalid coordinate prevents reliable crossing interpolation.")
        return finish_integrity(result, path)
    if not (freq_axis or distance_axis):
        f["first_descending_resolution"] = unknown("angstrom", path, coverage, "Unknown axis units; no conversion guessed")
        result["warnings"].append("Unrecognized FSC x-axis. Supply documented units before interpreting resolution.")
        return finish_integrity(result, path)
    freqs = [(x if freq_axis else (1.0 / x if x > 0 else math.nan), y) for x, y, _, _ in points]
    if any(not math.isfinite(x) or x < 0 for x, _ in freqs) or any(a[0] >= b[0] for a, b in zip(freqs, freqs[1:])):
        f["first_descending_resolution"] = unknown("angstrom", path, coverage, "Frequency coordinate order is invalid/non-increasing")
        result["warnings"].append("Coordinates are not ordered in strictly increasing spatial frequency; no sorting or crossing guess performed.")
        return finish_integrity(result, path)
    crossings = []
    for index, ((x0, y0), (x1, y1)) in enumerate(zip(freqs, freqs[1:])):
        direction = "descending" if y0 >= threshold > y1 else "ascending" if y0 < threshold <= y1 else None
        if direction:
            frequency = x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)
            crossings.append({"direction": direction, "from_coordinate_1based": index + 1,
                              "to_coordinate_1based": index + 2, "frequency_inverse_angstrom": frequency,
                              "resolution_angstrom": 1.0 / frequency if frequency > 0 else None,
                              "from_line": points[index][2], "to_line": points[index + 1][2]})
    first = next((cross for cross in crossings if cross["direction"] == "descending"), None)
    f["first_descending_resolution"] = field(first["resolution_angstrom"] if first else None,
        "angstrom", path, [evidence(first["from_line"], coordinate_1based=first["from_coordinate_1based"],
                                  next_coordinate_1based=first["to_coordinate_1based"],
                                  next_line=first["to_line"])] if first else [],
        coverage, status="calculated" if first else "unknown",
        reason="Linear interpolation in spatial frequency at the first downward threshold crossing")
    f["first_descending_frequency"] = field(first["frequency_inverse_angstrom"] if first else None,
        "inverse_angstrom", path, f["first_descending_resolution"]["evidence"], coverage,
        status="calculated" if first else "unknown")
    result["crossings"] = crossings
    if len(crossings) > 1:
        result["warnings"].append("Later oscillations/crossings exist; the last crossing was not selected.")
    if any(y < -1.000001 or y > 1.000001 for _, y, _, _ in points):
        result["warnings"].append("Correlation values outside [-1,1]; verify XML content.")
    return finish_integrity(result, path)


def hybrid36_decode(width, text):
    """Decode wwPDB-style decimal/upper/lower hybrid-36 fixed-width values."""
    if len(text) != width or not text.strip():
        raise ValueError("missing or wrong-width integer")
    first = text[0]
    if first in " -+0123456789":
        return int(text)
    if "A" <= first <= "Z":
        if not all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in text):
            raise ValueError("invalid upper-case hybrid-36 value")
        return int(text, 36) - 10 * 36 ** (width - 1) + 10 ** width
    if "a" <= first <= "z":
        if not all(c in "0123456789abcdefghijklmnopqrstuvwxyz" for c in text):
            raise ValueError("invalid lower-case hybrid-36 value")
        return int(text, 36) + 16 * 36 ** (width - 1) + 10 ** width
    raise ValueError("invalid fixed-width integer")


ELEMENTS_TWO = set("HE LI BE NE NA MG AL SI CL AR CA SC TI CR MN FE CO NI CU ZN GA GE AS SE BR KR RB SR ZR NB MO TC RU RH PD AG CD IN SN SB TE XE CS BA LA CE PR ND PM SM EU GD TB DY HO ER TM YB LU HF TA RE OS IR PT AU HG TL PB BI PO AT RN FR RA AC TH PA NP PU AM CM BK CF ES FM MD NO LR RF DB SG BH HS MT DS RG CN NH FL MC LV TS OG".split())


def atom_element(line):
    explicit = line[76:78].strip().upper() if len(line) >= 78 else ""
    if explicit:
        return explicit, "element column"
    name = line[12:16]
    letters = re.sub(r"[^A-Za-z]", "", name).upper()
    if not letters:
        return "?", "unknown"
    if name.startswith(" ") or name[0].isdigit():
        return letters[0], "inferred atom alignment"
    return letters[:2] if letters[:2] in ELEMENTS_TWO else letters[0], "inferred atom alignment"


def stat_summary(values):
    if not values:
        return None
    return {"minimum": min(values), "maximum": max(values), "mean": sum(values) / len(values),
            "all_zero": all(v == 0 for v in values), "unique_count": len(set(values))}


def parse_pdb(path):
    path = Path(path)
    data = path.read_bytes()
    text, encoding = decode_text(data)
    result = make_result(path, "pdb_fixed_columns", "actual", data)
    result["encoding"] = encoding
    coverage = {"scope": "entire coordinate file; no density fit or stereochemistry validation performed"}
    result["coverage"] = coverage
    counts = Counter()
    elements = Counter()
    atom_ids, serials, ter_serials = {}, {}, {}
    model_atoms = defaultdict(set)
    model_occurrences = Counter()
    duplicate_ids, duplicate_serials, bad, hybrid_examples = [], [], [], []
    duplicate_serial_keys = set()
    serial_record_collisions = []
    conect, segments, current_segment = [], [], None
    b_values, occupancy_values = [], []
    b_ev, occupancy_ev = [], []
    model_index, model_number, inside_model = 1, 1, False
    explicit_models = 0
    chain_segment_counts = Counter()

    def end_segment(terminated=False):
        nonlocal current_segment
        if current_segment:
            current_segment["terminated_by_TER"] = terminated
            segments.append(current_segment)
            chain_segment_counts[(current_segment["model_index"], current_segment["chain"])] += 1
            current_segment = None

    for number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.ljust(80)
        record = line[:6].strip()
        if record == "MODEL":
            end_segment()
            explicit_models += 1
            model_index = explicit_models
            try:
                model_number = int(line[10:14])
            except ValueError:
                model_number = None
                bad.append({"line": number, "reason": "Invalid MODEL number"})
            model_occurrences[model_number] += 1
            inside_model = True
        elif record == "ENDMDL":
            end_segment()
            inside_model = False
        elif record in ("ATOM", "HETATM"):
            counts["atoms"] += 1
            counts[record] += 1
            chain = line[21]
            if not current_segment or current_segment["model_index"] != model_index or current_segment["chain"] != chain:
                end_segment()
                current_segment = {"model_index": model_index, "model_number": model_number,
                                   "chain": chain, "start_line": number, "atoms": 0, "residues": []}
            current_segment["atoms"] += 1
            current_segment["end_line"] = number
            try:
                serial = hybrid36_decode(5, line[6:11])
                if line[6].isalpha() and len(hybrid_examples) < 8:
                    hybrid_examples.append({"line": number, "encoded": line[6:11], "decoded": serial})
                serial_key = (model_index, serial)
                if serial_key in ter_serials:
                    counts["atom_TER_serial_collisions"] += 1
                    if len(serial_record_collisions) < 8:
                        serial_record_collisions.append({"line": number, "first_line": ter_serials[serial_key],
                                                        "model_index": model_index, "serial": serial})
                if serial_key in serials:
                    counts["duplicate_atom_serial_records"] += 1
                    duplicate_serial_keys.add(serial_key)
                    if len(duplicate_serials) < 8:
                        duplicate_serials.append({"line": number, "first_line": serials[serial_key], "model_index": model_index, "serial": serial})
                else:
                    serials[serial_key] = number
                model_atoms[model_index].add(serial)
            except ValueError as error:
                bad.append({"line": number, "reason": "Invalid atom serial: " + str(error)})
            try:
                resseq = hybrid36_decode(4, line[22:26])
            except ValueError:
                resseq = line[22:26]
                bad.append({"line": number, "reason": "Invalid residue number"})
            residue = (resseq, line[26], line[17:20].strip())
            if residue not in current_segment["residues"]:
                current_segment["residues"].append(residue)
            key = (model_index, chain, resseq, line[26], line[17:20], line[12:16], line[16])
            if key in atom_ids:
                counts["duplicate_atom_identity_records"] += 1
                if len(duplicate_ids) < 8:
                    duplicate_ids.append({"line": number, "first_line": atom_ids[key], "model_index": model_index,
                                          "chain": chain, "residue": resseq, "residue_name": line[17:20].strip(),
                                          "atom_name": line[12:16].strip(), "altloc": line[16].strip()})
            else:
                atom_ids[key] = number
            element, origin = atom_element(line)
            elements[element] += 1
            counts["hydrogen_isotope_atoms" if element in ("H", "D", "T") else "heavy_or_unidentified_atoms"] += 1
            if origin != "element column":
                counts["elements_inferred_from_name"] += 1
            try:
                xyz = [float(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54))]
                if not all(math.isfinite(v) for v in xyz):
                    raise ValueError("non-finite")
            except ValueError:
                counts["invalid_coordinate_records"] += 1
                if len(bad) < 16:
                    bad.append({"line": number, "reason": "Invalid/non-finite x,y,z"})
            for label, start, end, values, evs in (("occupancy", 54, 60, occupancy_values, occupancy_ev),
                                                   ("B_factor", 60, 66, b_values, b_ev)):
                try:
                    value = float(line[start:end])
                    if not math.isfinite(value):
                        raise ValueError("non-finite")
                    values.append(value)
                    if len(evs) < 8:
                        evs.append(evidence(number, line[start:end].strip()))
                    if value < 0:
                        counts["negative_" + label + "_records"] += 1
                except ValueError:
                    counts["invalid_" + label + "_records"] += 1
        elif record == "TER":
            counts["TER_records"] += 1
            try:
                ter_serial = hybrid36_decode(5, line[6:11])
                ter_key = (model_index, ter_serial)
                if ter_key in serials or ter_key in ter_serials:
                    counts["atom_TER_serial_collisions" if ter_key in serials else "duplicate_TER_serial_records"] += 1
                    if len(serial_record_collisions) < 8:
                        serial_record_collisions.append({"line": number,
                            "first_line": serials.get(ter_key, ter_serials.get(ter_key)), "model_index": model_index,
                            "serial": ter_serial})
                ter_serials[(model_index, ter_serial)] = number
            except ValueError:
                counts["invalid_TER_serial_records"] += 1
            end_segment(True)
        elif record == "CONECT":
            counts["CONECT_records"] += 1
            try:
                refs = [hybrid36_decode(5, raw_line[start:start + 5])
                        for start in range(6, min(len(raw_line), 31), 5) if raw_line[start:start + 5].strip()]
                if len(refs) >= 2:
                    conect.append((model_index if inside_model else None, refs, number))
                else:
                    counts["CONECT_without_bond_records"] += 1
            except ValueError as error:
                counts["invalid_CONECT_records"] += 1
                bad.append({"line": number, "reason": "Invalid CONECT: " + str(error)})
    end_segment()
    dangling, ambiguous, valid_refs = [], [], 0
    for context, refs, number in conect:
        relevant = [context] if context is not None else list(model_atoms)
        for model in relevant:
            for serial in refs:
                if serial not in model_atoms[model]:
                    counts["unresolved_CONECT_references"] += 1
                    if len(dangling) < 8:
                        dangling.append({"line": number, "model_index": model, "serial": serial,
                                         "references_TER_instead_of_atom": (model, serial) in ter_serials})
                else:
                    valid_refs += 1
                    if (model, serial) in duplicate_serial_keys:
                        counts["ambiguous_CONECT_references"] += 1
                        if len(ambiguous) < 8:
                            ambiguous.append({"line": number, "model_index": model, "serial": serial})
    signatures = Counter(tuple(r[2] for r in seg["residues"]) for seg in segments)
    counts["segments"] = len(segments)
    counts["models_with_atoms"] = len(model_atoms)
    counts["hydrogen_atoms"] = elements["H"]
    counts["heavy_atoms"] = counts["atoms"] - counts["hydrogen_isotope_atoms"]
    f = result["fields"]
    f["counts"] = field(dict(counts), "records/atoms", path, [evidence(1, "Fixed-column full-file scan")], coverage, "calculated")
    f["elements"] = field(dict(elements), "atoms", path, [evidence(1, "Element column, falling back to aligned atom name")], coverage, "calculated")
    f["B_factor"] = field(stat_summary(b_values), "angstrom^2", path, b_ev, coverage, "calculated")
    f["occupancy"] = field(stat_summary(occupancy_values), "fraction", path, occupancy_ev, coverage, "calculated")
    f["segment_chain_counts"] = field([{"model_index": key[0], "chain": key[1], "segments": value}
        for key, value in sorted(chain_segment_counts.items())], "segments", path,
        [evidence(seg["start_line"], chain=seg["chain"], model_index=seg["model_index"]) for seg in segments], coverage, "calculated")
    f["segment_residue_signatures"] = field([{"residue_names": list(key), "segments": value}
        for key, value in signatures.items()], "three_letter_codes", path,
        [evidence(seg["start_line"], residues=seg["residues"]) for seg in segments], coverage, "calculated")
    result["diagnostics"] = {"duplicate_atom_identity_examples": duplicate_ids,
                             "duplicate_atom_serial_examples": duplicate_serials,
                             "hybrid36_atom_serial_examples": hybrid_examples,
                             "serial_record_collision_examples": serial_record_collisions,
                             "unresolved_CONECT_examples": dangling,
                             "ambiguous_CONECT_examples": ambiguous,
                             "valid_CONECT_reference_checks": valid_refs,
                             "parse_error_examples": bad[:16]}
    if duplicate_ids:
        result["warnings"].append("Within a model, chain/residue/atom/altloc identity is repeated across molecules. TER separates segments but does not create a unique chain identifier.")
    if counts["atoms"] > 99999 or counts["segments"] > 62:
        result["warnings"].append("Large coordinate assembly: prepare a validated PDBx/mmCIF representation with unique molecule identifiers; do not simply rename the extension.")
    if b_values and all(v == 0 for v in b_values):
        result["warnings"].append("All B factors are zero. Check the final refinement output/provenance; this alone does not prove refinement failed.")
    if hybrid_examples:
        result["warnings"].append("Hybrid-36 serials were decoded; their presence alone is not an atom-serial error.")
    if any(v > 1 for v in model_occurrences.values()):
        result["warnings"].append("Repeated MODEL labels detected; model instances were kept separate by occurrence.")
    if dangling:
        result["warnings"].append("CONECT has unresolved atom references; a TER serial is not an atom serial.")
    if ambiguous:
        result["warnings"].append("CONECT references duplicated atom serials; atom identity is ambiguous.")
    if serial_record_collisions:
        result["warnings"].append("ATOM/TER serial numbers collide or TER serials are repeated within a model.")
    result["warnings"].append("No coordinate conversion, hydrogen removal, chirality assignment, model-map fit, or bond geometry validation was performed.")
    return finish_integrity(result, path)


def compare_maps(results):
    maps = [r for r in results if r["kind"] == "mrc_header"]
    comparisons = []
    names = ("dimensions_storage_crs", "pixel_spacing_xyz", "axis_mapping_crs_to_xyz", "starts_crs", "origin_xyz")
    for i, first in enumerate(maps):
        for second in maps[i + 1:]:
            differences, unavailable = [], []
            for name in names:
                left = first["fields"].get(name, {}).get("value")
                right = second["fields"].get(name, {}).get("value")
                if left is None or right is None or any(v is None for v in left + right):
                    unavailable.append(name)
                elif any(not math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-5) for a, b in zip(left, right)):
                    differences.append({"field": name, "first_value": left, "second_value": right})
            comparisons.append({"files": [first["source_file"], second["source_file"]],
                                "status": "different_grid" if differences else "unknown" if unavailable else "same_header_grid",
                                "differences": differences, "unavailable": unavailable,
                                "limitation": "Header compatibility cannot prove a matched primary/half-map pair or model-map alignment."})
    return comparisons


def values_equivalent(first, second):
    """Numeric semantic equality with a narrow float32-rounding tolerance.

    Booleans remain booleans. The tolerance is 0.2 ppm plus 1e-8 absolute,
    enough for MRC float32 metadata but far below meaningful setting changes.
    No unit conversions, shape normalization, or subset/range matching occurs.
    """
    if isinstance(first, bool) or isinstance(second, bool):
        return isinstance(first, bool) and isinstance(second, bool) and first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isfinite(first) and math.isfinite(second) and math.isclose(first, second, rel_tol=2e-7, abs_tol=1e-8)
    if isinstance(first, dict) and isinstance(second, dict):
        return first.keys() == second.keys() and all(values_equivalent(first[key], second[key]) for key in first)
    if isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        return len(first) == len(second) and all(values_equivalent(a, b) for a, b in zip(first, second))
    return type(first) is type(second) and first == second


def unique_equivalent_values(values):
    output = []
    for value in values:
        if not any(values_equivalent(value, present) for present in output):
            output.append(value)
    return output


def acquisition_summary(results):
    acquisition = [r for r in results if r["kind"] in ("serialem_log", "serialem_mdoc")]
    names = ("exposure_time", "frames_per_movie", "pixel_spacing", "exposure_dose", "voltage",
             "successful_movie_target_defocus", "target_defocus", "filter_slit_width",
             "filter_slit_state", "filter_slit_active", "filter_slit_and_loss", "image_size")
    output = {}
    for name in names:
        actual_sources = [r["fields"][name] for r in acquisition if r["role"] == "actual" and name in r["fields"]]
        actual = [f for f in actual_sources if f["value"] is not None]
        inactive = [f for f in actual_sources if f["status"] == "inactive"]
        invalid_or_conflict = [f for f in actual_sources if f["status"] in ("invalid", "conflict")]
        candidate = [r["fields"][name] for r in acquisition if r["role"] == "test" and name in r["fields"] and r["fields"][name]["value"] is not None]
        distinct = unique_equivalent_values([f["value"] for f in actual])
        candidate_distinct = unique_equivalent_values([f["value"] for f in candidate])
        conflicted = len(distinct) > 1 or bool(actual and inactive) or bool(invalid_or_conflict)
        equal_candidate_set = len(distinct) == len(candidate_distinct) and all(
            any(values_equivalent(a, b) for b in candidate_distinct) for a in distinct)
        output[name] = {"status": "conflict" if conflicted else "actual_observed" if actual else "inactive" if inactive else "unknown",
                        "actual_evidence": actual, "inactive_evidence": inactive,
                        "invalid_or_conflict_evidence": invalid_or_conflict, "test_candidates": candidate,
                        "test_actual_differ": bool(actual and candidate and not equal_candidate_set),
                        "selected_value": actual[0]["value"] if len(distinct) == 1 and not conflicted else None,
                        "rule": "Never fill a missing actual field from a test candidate without explicit batch confirmation."}
    return output


def inspect(args):
    results = []
    for kind, role, paths in (("log", "actual", args.log), ("log", "test", args.test_log),
                              ("mdoc", "actual", args.mdoc), ("mdoc", "test", args.test_mdoc),
                              ("mrc", "actual", args.map), ("fsc", "actual", args.fsc), ("pdb", "actual", args.pdb)):
        for path in paths:
            try:
                if kind == "log":
                    result = parse_log(path, role, args.expected_movies if role == "actual" else None)
                elif kind == "mdoc":
                    result = parse_mdoc(path, role, args.expected_movies if role == "actual" else None)
                else:
                    result = {"mrc": parse_mrc, "fsc": parse_fsc, "pdb": parse_pdb}[kind](path)
                results.append(result)
            except (OSError, ValueError, struct.error) as error:
                results.append({"kind": kind, "role": role, "source_file": str(path), "fields": {},
                                "warnings": [{"code": "input_error", "reason": str(error)}], "error": True})
    return {"schema_version": SCHEMA_VERSION, "read_only": True,
            "policy": "No historical batch defaults. Actual/test evidence remain separate. Unknown values are not guessed.",
            "inputs": results, "acquisition_summary": acquisition_summary(results),
            "map_comparisons": compare_maps(results),
            "limitations": ["MRC density arrays were not read; hashes cover their headers only.",
                            "Input hashes demonstrate unchanged inspected bytes, not source authenticity.",
                            "This inspector does not validate acquisition completeness, map provenance, or atomic model quality."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", action="append", default=[], help="Actual SerialEM text log (repeatable)")
    parser.add_argument("--test-log", "--shottest", dest="test_log", action="append", default=[],
                        help="Test/script/shottest text candidate; never actual by default (repeatable)")
    parser.add_argument("--mdoc", action="append", default=[], help="Actual SerialEM mdoc (repeatable)")
    parser.add_argument("--test-mdoc", action="append", default=[], help="Test mdoc candidate (repeatable)")
    parser.add_argument("--map", action="append", default=[], help="MRC/CCP4 map, read only first 1024 bytes (repeatable)")
    parser.add_argument("--fsc", action="append", default=[], help="FSC XML (repeatable)")
    parser.add_argument("--pdb", action="append", default=[], help="PDB coordinate file, fixed-column inspection (repeatable)")
    parser.add_argument("--expected-movies", type=int,
                        help="Externally known full ACTUAL batch movie count; never applied to test/script candidates")
    args = parser.parse_args(argv)
    if args.expected_movies is not None and args.expected_movies <= 0:
        parser.error("--expected-movies must be positive")
    if not any((args.log, args.test_log, args.mdoc, args.test_mdoc, args.map, args.fsc, args.pdb)):
        parser.error("provide at least one input file")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    result = inspect(args)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if any(r.get("error") for r in result["inputs"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
