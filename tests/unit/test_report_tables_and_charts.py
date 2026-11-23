from osdagbridge.core.boq.boq_generator import diaphragm_tonnage
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.summary_values import component_ratios
from osdagbridge.core.utils import common as keys


def test_live_loads_follow_saved_checkbox_values():
    tex = ch3_loads({
        keys.KEY_LL_IRC_CLASS_A: "False", keys.KEY_LL_IRC_CLASS_SV: True,
        keys.KEY_BL_IRC_CLASS_SV: False, keys.KEY_FOOTPATH: "None",
        keys.KEY_LL_CUSTOM_VEHICLES: [{"name": "Site & delivery"}],
    })
    assert "Class A &" not in tex
    assert "Class SV & 3776.85 & --- & No" in tex
    assert r"Site \& delivery" in tex
    assert "Footway pressure & Not applicable" in tex


def test_ratios_keep_failures_missing_data_and_zero_distinct():
    ratios = component_ratios({
        "design_results": {"per_girder": {
            "G1": {"checks": [{"dcr": 2.16}]}, "EB1": {"checks": [{"dcr": 9}]}
        }},
        "deck_design_results": {"ur_shear": 0},
        "end_diaphragm_design_results": {"G1-G2": {"diagonal": {
            "compression": {"Member.efficiency": 0.49, "Member.Slenderness": 150}
        }}},
    })
    assert ratios == {"Plate girders": 2.16, "Deck slab": 0,
                      "Cross bracing": None, "End diaphragms": 0.6}


def test_diaphragm_takeoff_counts_both_supports_and_requires_all_pairs():
    inputs = {keys.KEY_TS_NO_OF_GIRDERS: 2, keys.KEY_TS_GIRDER_SPACING: 2.5}
    outputs = {"member_properties.end_diaphragm_details.G1G2.type": "Rolled Beam",
               "transverse_member_design.ed.section_properties.end_diaphragm.G1G2.M": 20}
    assert diaphragm_tonnage(inputs, outputs) == 0.1
    inputs[keys.KEY_TS_NO_OF_GIRDERS] = 3
    assert diaphragm_tonnage(inputs, outputs) is None


def test_final_geometry_replaces_stale_input_area_and_mass():
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    inputs = {keys.KEY_SPAN: 25, keys.KEY_TS_NO_OF_GIRDERS: 3,
              "member_properties.girder_details.section_properties.area": 0.02388012,
              "member_properties.girder_details.section_properties.mass": 187.4}
    outputs = {"design_results": {
        "D_mm": 1390, "tw_mm": 8, "bf_top_mm": 420, "tf_top_mm": 18,
        "bf_bot_mm": 420, "tf_bot_mm": 18,
    }}
    result = calculate_material_quantities(inputs, outputs)
    # Clear web is 1390 - 18 - 18 = 1354 mm, giving 25952 mm².
    assert float(result["steel_girders_vol_total"]) == 1.9464
    assert float(result["steel_girders_wt_total"]) == 15.2792
    assert result["rebar_deck_wt_total"] == "Not calculated"


def test_skew_girders_follow_longitudinal_mesh_lines():
    from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
    from collections import defaultdict
    result = PlateGirderAnalysisResults(None, None, edge_dist=1)
    nodes, elements = {}, {}
    for line in range(5):
        for station in range(3):
            nodes[line * 3 + station] = (station * 12.5 + line * .3, 0, line * 2.3)
        for station in range(2):
            elements[line * 2 + station] = (line * 3 + station, line * 3 + station + 1)
    result.build_grillage_connectivity = lambda: (nodes, elements, defaultdict(set))
    girders, _ = result.build_girders(False)
    assert list(girders) == ["EB1", "G1", "G2", "G3", "EB2"]
    assert all(girder["length"] == 25 for girder in girders.values())
    assert girders["G2"]["path"] == [6, 7, 8]


def test_deflection_check_retains_failure_and_governing_combination():
    from osdagbridge.core.reports.summary_values import governing_check
    outputs = {"design_results": {"per_girder": {
        "G2": {"per_lc": {"1.0 LL": {"checks": [
            {"id": 13, "demand": 32.146, "capacity": 31.25,
             "demand_unit": "mm", "capacity_unit": "mm", "status": "FAIL"}
        ]}}}
    }}}
    check = governing_check(outputs, 13)
    assert check[0] > 1
    assert check[3:] == ("G2", "1.0 LL")


def test_barrier_area_legacy_units_and_missing_geometry():
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    inputs = {keys.KEY_SPAN: 25, keys.KEY_TS_NO_OF_GIRDERS: 3,
              "typical_section.crash_barrier.density": 25,
              "typical_section.crash_barrier.load": 7.557,
              "typical_section.crash_barrier.area": 302282.768}
    result = calculate_material_quantities(inputs, {})
    assert float(result["crash_barrier_vol_total"]) == 15.11
    inputs["typical_section.crash_barrier.area"] = .302282768
    result = calculate_material_quantities(inputs, {})
    assert float(result["crash_barrier_vol_total"]) == 15.11
    del inputs["typical_section.crash_barrier.load"]
    assert calculate_material_quantities(inputs, {})["crash_barrier_vol_total"] == "Not calculated"
