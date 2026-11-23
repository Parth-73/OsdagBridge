# =============================================================================
# OsdagBridge — BOQ (Bill of Quantities) Generator
# =============================================================================

import logging
import math
from typing import Any

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)

logger = logging.getLogger("osdagbridge.core.boq_generator")


def resolve_girder_value(source: dict, base_key: str, i: int = 0) -> Any:
    """Resolve a girder property from an input/output dict, tolerating both the
    per-girder dynamic key scheme and the legacy scalar key.
    """
    candidates = [
        f"{base_key}.G{i + 1}.M1",
        base_key,
        f"{base_key}.G1.M1"
    ]
    for key in candidates:
        if key in source:
            return source[key]
    raise KeyError(base_key)


def diaphragm_tonnage(inputs, outputs):
    """Sum section mass per metre times member length at both supports."""
    try:
        count = int(inputs[KEY_TS_NO_OF_GIRDERS])
        spacing = float(inputs[KEY_TS_GIRDER_SPACING])
        lengths = outputs.get("end_diaphragm_forces_dict", {}).get("lengths", {})
        total_kg = 0.0
        for i in range(1, count):
            pair = f"G{i}G{i + 1}"
            config = f"member_properties.end_diaphragm_details.{pair}"
            section = "transverse_member_design.ed.section_properties"
            kind = outputs[f"{config}.type"]
            if kind == "Cross Bracing":
                length = lengths[f"G{i}-G{i + 1}"]["diagonal"]
                members = [("end_diaphragm", 2 * length)]
                for chord in ("top_chord", "bottom_chord"):
                    if outputs[f"{config}.{chord}"]:
                        members.append((chord, spacing))
            elif kind in {"Rolled Beam", "Welded Beam"}:
                members = [("end_diaphragm", spacing)]
            else:
                return None
            for member, length in members:
                total_kg += 2 * length * float(outputs[f"{section}.{member}.{pair}.M"])
        return total_kg / 1000 if count > 1 else None
    except (KeyError, TypeError, ValueError):
        return None


def calculate_material_quantities(inputs: dict, outputs: dict) -> dict:
    """Calculate quantities (steel tonnage, concrete volume, rebar, studs)
    needed for the material take-off summary (Chapter 7).
    """
    quantities = {
        "steel_girders_vol_formula": "Not calculated",
        "steel_girders_qty": "Not calculated",
        "steel_girders_vol_total": "Not calculated",
        "steel_girders_wt_single": "Not calculated",
        "steel_girders_wt_total": "Not calculated",
        
        "steel_bracing_vol_formula": "Not calculated",
        "steel_bracing_qty": "Not calculated",
        "steel_bracing_vol_total": "Not calculated",
        "steel_bracing_wt_single": "Not calculated",
        "steel_bracing_wt_total": "Not calculated",

        "bracing_top_vol_formula": "Not calculated",
        "bracing_top_qty": "Not calculated",
        "bracing_top_vol_total": "Not calculated",
        "bracing_top_wt_single": "Not calculated",
        "bracing_top_wt_total": "Not calculated",

        "bracing_bot_vol_formula": "Not calculated",
        "bracing_bot_qty": "Not calculated",
        "bracing_bot_vol_total": "Not calculated",
        "bracing_bot_wt_single": "Not calculated",
        "bracing_bot_wt_total": "Not calculated",

        "bracing_diag_vol_formula": "Not calculated",
        "bracing_diag_qty": "Not calculated",
        "bracing_diag_vol_total": "Not calculated",
        "bracing_diag_wt_single": "Not calculated",
        "bracing_diag_wt_total": "Not calculated",
        
        "concrete_deck_vol_formula": "Not calculated",
        "concrete_deck_qty": "Not calculated",
        "concrete_deck_vol_total": "Not calculated",
        "concrete_deck_wt_single": "Not calculated",
        "concrete_deck_wt_total": "Not calculated",
        
        "rebar_deck_vol_formula": "Not calculated",
        "rebar_deck_qty": "Not calculated",
        "rebar_deck_vol_total": "Not calculated",
        "rebar_deck_wt_single": "Not calculated",
        "rebar_deck_wt_total": "Not calculated",
        
        "shear_studs_vol_formula": "Not calculated",
        "shear_studs_qty": "Not calculated",
        "shear_studs_vol_total": "Not calculated",
        "shear_studs_wt_single": "Not calculated",
        "shear_studs_wt_total": "Not calculated",

        "crash_barrier_vol_formula": "Not calculated",
        "crash_barrier_qty": "Not calculated",
        "crash_barrier_vol_total": "Not calculated",
        "crash_barrier_wt_single": "Not calculated",
        "crash_barrier_wt_total": "Not calculated",
    }
    try:
        span_val = inputs.get(KEY_SPAN)
        n_girders_val = inputs.get(KEY_TS_NO_OF_GIRDERS)
        if span_val is None or n_girders_val is None:
            return quantities
            
        try:
            span = float(span_val)
            n_girders = int(n_girders_val)
        except Exception:
            return quantities

        if span <= 0 or n_girders <= 0:
            return quantities

        # 1. Concrete deck volume (Cu.m) and Weight (MT)
        overall_width_val = inputs.get("typical_section.overall_bridge_width")
        deck_thickness_val = inputs.get(KEY_TS_DECK_THICKNESS)
        
        if overall_width_val is not None and deck_thickness_val is not None:
            try:
                overall_width = float(overall_width_val)
                deck_thickness = float(deck_thickness_val) / 1000.0  # mm to m
                if overall_width > 0 and deck_thickness > 0:
                    concrete_vol = span * overall_width * deck_thickness
                    quantities["concrete_deck_vol_formula"] = f"${overall_width:.2f}\\text{{ m}} \\times {deck_thickness:.2f}\\text{{ m}} \\times {span:.2f}\\text{{ m}} = {concrete_vol:.2f}\\text{{ m}}^3$"
                    quantities["concrete_deck_qty"] = "1"
                    quantities["concrete_deck_vol_total"] = f"{concrete_vol:.2f}"
                    quantities["concrete_deck_wt_single"] = f"{(concrete_vol * 2.5):.2f}"
                    quantities["concrete_deck_wt_total"] = f"{(concrete_vol * 2.5):.2f}"

                    # A measured reinforcement take-off needs layer extents, laps and anchorage.
                    # The former 120 kg/m³ allowance was unrelated to the designed schedule.
            except Exception:
                pass

        # 3. Steel Girders (Cu.m) and Weight (MT)
        final = outputs.get("design_results") or {}
        try:
            depth, web, top_width, top_thick, bot_width, bot_thick = (
                float(final[key]) for key in
                ("D_mm", "tw_mm", "bf_top_mm", "tf_top_mm", "bf_bot_mm", "tf_bot_mm")
            )
            web_depth = depth - top_thick - bot_thick
            if min(web_depth, web, top_width, top_thick, bot_width, bot_thick) <= 0:
                raise ValueError("Invalid final girder dimensions")
            girder_area = (web_depth * web + top_width * top_thick + bot_width * bot_thick) / 1e6
            girder_vol = girder_area * span
            total_volume = n_girders * girder_vol
            quantities.update({
                "steel_girders_vol_formula": "$" + f"{girder_area:.8f} \\mathrm{{m}}^2 \\times {span:g} \\mathrm{{m}}$",
                "steel_girders_qty": str(n_girders),
                "steel_girders_vol_total": f"{total_volume:.5f}",
                "steel_girders_wt_single": f"{girder_vol * 7.85:.4f}",
                "steel_girders_wt_total": f"{total_volume * 7.85:.4f}",
            })
        except (KeyError, TypeError, ValueError):
            logger.info("Final girder geometry unavailable for take-off")

        # 4. Shear Stud Connectors (Cu.m) and Weight (MT)
        spacing_mm = 0.0
        studs_per_sec = 0
        stud_d = 0.0
        stud_h_mm = 0.0

        spacing_val = outputs.get("steeldesign.details.shear.longitudinal_spacing")
        studs_val = outputs.get("steeldesign.details.shear.studs_per_section")
        stud_d_val = outputs.get("steeldesign.details.shear.diameter") or inputs.get("design_options.shear_studs.diameter")
        stud_h_val = outputs.get("steeldesign.details.shear.height") or inputs.get("design_options.shear_studs.height")

        if spacing_val is not None and studs_val is not None and stud_d_val is not None and stud_h_val is not None:
            try:
                spacing_mm = float(spacing_val)
                studs_per_sec = int(studs_val)
                stud_d = float(stud_d_val)
                stud_h_mm = float(stud_h_val)
            except Exception:
                pass

        if spacing_mm > 0.0 and studs_per_sec > 0 and stud_d > 0.0 and stud_h_mm > 0.0:
            stud_h = stud_h_mm / 1000.0  # mm to m
            n_sections = math.ceil(span * 1000.0 / spacing_mm) + 1
            total_studs = n_girders * studs_per_sec * n_sections
            
            stud_area = (math.pi * (stud_d / 1000.0) ** 2) / 4.0
            stud_vol = stud_area * stud_h
            quantities["shear_studs_vol_formula"] = f"${stud_area:.6f}\\text{{ m}}^2 \\times {stud_h:.3f}\\text{{ m}} = {stud_vol:.6f}\\text{{ m}}^3$"
            quantities["shear_studs_qty"] = str(total_studs)
            
            studs_total_vol = total_studs * stud_vol
            quantities["shear_studs_vol_total"] = f"{studs_total_vol:.2f}"
            
            # density of steel = 7850 kg/m^3 = 7.85 tonnes/m^3
            single_stud_wt = stud_vol * 7.85
            total_studs_wt = studs_total_vol * 7.85
            quantities["shear_studs_wt_single"] = f"{single_stud_wt:.6f}"
            quantities["shear_studs_wt_total"] = f"{total_studs_wt:.3f}"
        else:
            quantities["shear_studs_vol_formula"] = "Not calculated"
            quantities["shear_studs_qty"] = "Not calculated"
            quantities["shear_studs_vol_total"] = "Not calculated"
            quantities["shear_studs_wt_single"] = "Not calculated"
            quantities["shear_studs_wt_total"] = "Not calculated"

        # 5. Final cross-bracing sections at the stations recorded by the mesh.
        geometry = (outputs.get("crossbracing_forces_dict") or {}).get("geometry", {})
        for part, section, length_key, multiplier, enabled in (
            ("top", "top_chord", "girder_spacing_m", 1, geometry.get("top_chord")),
            ("bot", "bottom_chord", "girder_spacing_m", 1, geometry.get("bottom_chord")),
            ("diag", "bracing", "diagonal_length_m", 2, True),
        ):
            try:
                stations = int(outputs["quantity_model.cross_bracing_stations"])
                length = float(geometry[length_key])
                if stations < 0 or length <= 0 or enabled is None:
                    raise ValueError("Incomplete cross-bracing geometry")
                count = (n_girders - 1) * stations * multiplier if enabled else 0
                total_volume = 0.0
                for pair_index in range(1, n_girders):
                    area = float(outputs[f"transverse_member_design.cb.section_properties.{section}.G{pair_index}G{pair_index + 1}.A"]) / 10000
                    if area <= 0:
                        raise ValueError("Invalid final bracing area")
                    total_volume += area * length * stations * multiplier if enabled else 0
                prefix = f"bracing_{part}"
                quantities[f"{prefix}_qty"] = str(count)
                quantities[f"{prefix}_vol_formula"] = "Sum of final member areas times lengths"
                quantities[f"{prefix}_vol_total"] = f"{total_volume:.5f}"
                quantities[f"{prefix}_wt_single"] = f"{total_volume * 7.85 / count:.6f}" if count else "Not applicable"
                quantities[f"{prefix}_wt_total"] = f"{total_volume * 7.85:.5f}"
            except (KeyError, ValueError, TypeError):
                for suffix in ("qty", "vol_formula", "vol_total", "wt_single", "wt_total"):
                    quantities[f"bracing_{part}_{suffix}"] = "Not calculated"

        # 6. Crash Barrier (Cu.m) and Weight (MT)
        KEY_CB_AREA = "typical_section.crash_barrier.area"
        cb_area = 0.0
        cb_area_val = inputs.get(KEY_CB_AREA)
        
        if cb_area_val is not None:
            try:
                area = float(cb_area_val)
                unit = inputs.get("quantity_model.crash_barrier_area_unit")
                if unit == "m2":
                    cb_area = area
                elif unit == "mm2":
                    cb_area = area / 1e6
                else:
                    # Older files store either mm² defaults or m² GUI values under
                    # the same key. Resolve only when the applied line load agrees.
                    density = float(inputs["typical_section.crash_barrier.density"])
                    line_load = float(inputs["typical_section.crash_barrier.load"])
                    for candidate in (area, area / 1e6):
                        if math.isclose(candidate * density, line_load, rel_tol=0.01):
                            cb_area = candidate
                            break
            except Exception:
                pass
        
        if cb_area > 0.0:
            cb_vol = cb_area * span
            quantities["crash_barrier_vol_formula"] = f"${cb_area:.5f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {cb_vol:.5f}\\text{{ m}}^3$"
            quantities["crash_barrier_qty"] = "2"
            
            cb_total_vol = 2 * cb_vol
            quantities["crash_barrier_vol_total"] = f"{cb_total_vol:.2f}"
            
            single_cb_wt = cb_vol * 2.5
            total_cb_wt = cb_total_vol * 2.5
            quantities["crash_barrier_wt_single"] = f"{single_cb_wt:.2f}"
            quantities["crash_barrier_wt_total"] = f"{total_cb_wt:.2f}"
        else:
            quantities["crash_barrier_vol_formula"] = "Not calculated"
            quantities["crash_barrier_qty"] = "Not calculated"
            quantities["crash_barrier_vol_total"] = "Not calculated"
            quantities["crash_barrier_wt_single"] = "Not calculated"
            quantities["crash_barrier_wt_total"] = "Not calculated"

    except Exception as exc:
        logger.warning(f"Error calculating material quantities: {exc}")

    diaphragm_mass = diaphragm_tonnage(inputs, outputs)
    if diaphragm_mass is not None:
        quantities["end_diaphragm_wt_total"] = f"{diaphragm_mass:.3f}"
    return quantities
