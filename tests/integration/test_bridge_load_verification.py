"""Independent load-resultant and moment checks on a 25 m bridge mesh."""
import openseespy.opensees as ops
import ospgrillage as og
import pytest


@pytest.fixture
def bridge():
    ops.wipe()
    model = og.create_grillage(bridge_name="Verification", long_dim=25, width=6, skew=0,
                              num_long_grid=3, num_trans_grid=21, edge_beam_dist=0, mesh_type="Oblique")
    material = og.create_material(material="steel", E=2e11, v=.3, rho=7850)
    section = og.create_section(A=.03, J=.0001, Iz=.01, Iy=.0002, Ay=1e8, Az=1e8)
    member = og.create_member(section=section, material=material)
    for name in ("edge_beam", "exterior_main_beam_1", "interior_main_beam",
                 "exterior_main_beam_2", "transverse_slab", "start_edge", "end_edge"):
        model.set_member(member, member=name)
    model.create_osp_model(pyfile=False)
    yield model
    ops.wipe()


def vertex(x, z, pressure):
    return og.create_load_vertex(x=x, y=0, z=z, p=pressure)


@pytest.mark.parametrize("factor", [-1.0, .5, 1.5])
def test_point_line_patch_and_compound_resultants(bridge, factor):
    point = og.create_load(point1=vertex(12.5, 3, -10000))
    line = og.create_load(point1=vertex(0, 3, -10000), point2=vertex(25, 3, -10000))
    patch = og.create_load(point1=vertex(0, 0, -1000), point2=vertex(25, 0, -1000),
                           point3=vertex(25, 6, -1000), point4=vertex(0, 6, -1000))
    compound = og.create_compound_load(name="compound")
    compound.add_load(point)
    compound.add_load(patch)
    for load, resultant in ((point, -10000), (line, -250000),
                            (patch, -150000), (compound, -160000)):
        case = og.create_load_case(name="resultant")
        case.add_load(load, load_factor=factor)
        commands = bridge._distribute_load_types_to_model(case)
        assert sum(args[2] for _, args, _ in commands) == pytest.approx(resultant * factor)


def test_simply_supported_bridge_uniform_load_moment(bridge):
    # Apply the same 10 kN/m tributary load to each girder as equivalent nodal
    # loads. Symmetry permits the independent w L² / 8 midspan moment check.
    for name, group_factor, case_factor in (("service", 1, 1), ("ultimate", 1.35, 1),
                                            ("external", 1, 1.35)):
        case = og.create_load_case(name=name)
        for node in ops.getNodeTags():
            x = ops.nodeCoord(node)[0]
            load = 10000 * 1.25 * (.5 if x in (0, 25) else 1)
            case.add_load(og.create_load(loadtype="nodal", node_tag=node, Fy=-load),
                          load_factor=group_factor)
        bridge.add_load_case(case, load_factor=case_factor)
    bridge.analyze()
    data = bridge.get_results()
    moments = {name: float(abs(data.forces.sel(Loadcase=name, Component="Mz_i")).max())
               for name in ("service", "ultimate", "external")}
    expected = 10000 * 25 ** 2 / 8
    assert moments["service"] == pytest.approx(expected, rel=.001)
    assert moments["ultimate"] == pytest.approx(1.35 * expected, rel=.001)
    assert moments["ultimate"] == pytest.approx(moments["external"], rel=1e-8)
    ops.reactions()
    for support_x in (0, 25):
        reaction = sum(ops.nodeReaction(node, 2) for node in ops.getNodeTags()
                       if ops.nodeCoord(node)[0] == support_x)
        assert reaction == pytest.approx(3 * 10000 * 25 / 2 * 1.35, rel=1e-7)


@pytest.mark.parametrize("bounds", [(2, 23, 1, 5), (1.25, 23.75, 0, 6)])
def test_partial_and_mesh_aligned_patch_resultants(bridge, bounds):
    x1, x2, z1, z2 = bounds
    patch = og.create_load(point1=vertex(x1, z1, -1000), point2=vertex(x2, z1, -1000),
                           point3=vertex(x2, z2, -1000), point4=vertex(x1, z2, -1000))
    case = og.create_load_case(name="partial")
    case.add_load(patch)
    commands = bridge._distribute_load_types_to_model(case)
    assert sum(args[2] for _, args, _ in commands) == pytest.approx(-1000 * (x2-x1) * (z2-z1))
