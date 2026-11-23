"""Verify factors survive combination construction, distribution and solver execution."""
from types import SimpleNamespace

import openseespy.opensees as ops
import pytest
import ospgrillage as og
from ospgrillage.osp_grillage import OspGrillage
from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel


def distribute(case):
    model = object.__new__(OspGrillage)
    return model._distribute_load_types_to_model(case)


def test_distinct_combination_factors_reach_independent_solver_responses():
    load = og.create_load(loadtype="nodal", node_tag=2, Fy=-1000)
    results = {}
    cases = []
    for label, factor in (("BASIC-test", 1.35), ("SLS-test", 1.0)):
        case = og.create_load_case(name=label)
        case.add_load(load, load_factor=factor)
        cases.append(case)
        commands = distribute(case)
        assert commands[0][1][2] == -1000 * factor
        ops.wipe()
        ops.model("basic", "-ndm", 3, "-ndf", 6)
        ops.node(1, 0, 0, 0)
        ops.node(2, 5, 0, 0)
        ops.fix(1, 1, 1, 1, 1, 1, 1)
        ops.geomTransf("Linear", 1, 0, 0, 1)
        ops.element("elasticBeamColumn", 1, 1, 2, .02, 2e11, 8e10, .0001, .001, .001, 1)
        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        for command, args, kwargs in commands:
            getattr(ops, command)(*args, **kwargs)
        ops.system("BandGeneral")
        ops.numberer("Plain")
        ops.constraints("Plain")
        ops.integrator("LoadControl", 1)
        ops.algorithm("Linear")
        ops.analysis("Static")
        assert ops.analyze(1) == 0
        results[label] = ops.nodeDisp(2, 2)
    ops.wipe()
    assert results["BASIC-test"] / results["SLS-test"] == pytest.approx(1.35)
    assert load.Fy == -1000
    assert distribute(cases[0])[0][1][2] == -1350


def test_combination_builder_preserves_nested_group_coefficients():
    backend = BridgeGrillageModel()
    source = og.create_load_case(name="DL")
    source.add_load(og.create_load(loadtype="nodal", node_tag=2, Fy=-1000), load_factor=.5)
    backend.dead_load_combination = source
    registered = []
    model = SimpleNamespace(add_load_case=lambda case: registered.append(case))
    with pytest.warns(UserWarning):
        backend.create_uls_combinations(model=model)
    basic = [case for case in registered if case.name.startswith("BASIC")]
    assert basic
    assert distribute(basic[0])[0][1][2] == pytest.approx(-675)
    assert source.load_groups[0]["factor"] == .5


def test_compound_group_scales_forces_and_moments_once():
    compound = og.create_compound_load(name="group")
    compound.add_load(og.create_load(loadtype="nodal", node_tag=2, Fy=-10, Mz=4))
    case = og.create_load_case(name="negative")
    case.add_load(compound, load_factor=-2)
    assert distribute(case)[0][1][2] == 20
    assert distribute(case)[0][1][-1] == -8


def test_analysis_extractor_preserves_loadcase_values_and_locations():
    import numpy as np
    import xarray as xr
    from osdagbridge.core.bridge_types.plate_girder.results_data import build_load_effects_cache, build_forces_summary
    ds = xr.Dataset({"forces": (("Loadcase", "Element", "Component"),
                               np.array([[[10, -10, 4, -4]], [[20, -20, 8, -8]]]) * 1000.)},
                    coords={"Loadcase": ["BASIC-test", "SLS-test"], "Element": [1],
                            "Component": ["Mz_i", "Mz_j", "Vy_i", "Vy_j"]})
    handler = SimpleNamespace(
        ds=ds,
        classify_loadcases=lambda: {"all": ["BASIC-test", "SLS-test"]},
        build_girders=lambda verbose=False: ({"G1": {"elements": [1], "element_map": [(1, 1, 2)]}}, {}),
        build_grillage_connectivity=lambda: ({1: [0, 0, 0], 2: [25, 0, 0]}, {}, {}),
    )
    cache = build_load_effects_cache(handler)
    summary = build_forces_summary(handler, cache)
    assert summary["load_cases"]["BASIC-test"]["max_bm"] == 10
    assert summary["load_cases"]["SLS-test"]["max_bm"] == 20
    assert summary["load_cases"]["SLS-test"]["bm_girder"] == "G1"
    assert summary["load_cases"]["SLS-test"]["bm_location"] == 0
    assert summary["reactions"]["BASIC-test"]["left_kN"] == 4
    assert summary["reactions"]["SLS-test"]["left_kN"] == 8
