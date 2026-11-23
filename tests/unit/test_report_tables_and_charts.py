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
