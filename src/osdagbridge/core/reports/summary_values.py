from math import isfinite

from osdagbridge.core.bridge_types.plate_girder.results_data_post_processing import member_summary


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if isfinite(f) and f >= 0 and (out is None or f > out):
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Largest strength or slenderness utilization across the designed member cases."""
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for nature, raw in force_types.items():
                if not isinstance(raw, dict):
                    continue
                result = member_summary(raw)
                values = [result.get("efficiency")]
                slenderness = _max_float([result.get("slenderness")])
                if slenderness is not None and nature in {"tension", "compression"}:
                    values.append(slenderness / (400 if nature == "tension" else 250))
                best = _max_float([best, *values])
    return best


def component_ratios(outputs):
    girders = (outputs.get("design_results") or {}).get("per_girder", {})
    deck = outputs.get("deck_design_results") or {}
    return {
        "Plate girders": _max_float(check.get("dcr") for key, girder in girders.items()
                                   if not str(key).startswith("EB") for check in girder.get("checks", [])),
        "Deck slab": _max_float(v for key, v in deck.items() if key.startswith("ur_")),
        "Cross bracing": _max_member_efficiency(outputs.get("crossbracing_design_results")),
        "End diaphragms": _max_member_efficiency(outputs.get("end_diaphragm_design_results")),
    }
