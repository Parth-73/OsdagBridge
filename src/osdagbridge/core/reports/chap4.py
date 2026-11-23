from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    def _merged_row(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return (
            _tex(lc)                              + r" & "
            + _fmt(bm_d.get('max_bm'))           + r" & "
            + _tex(bm_d.get('bm_girder', '---')) + r" & "
            + _fmt(bm_d.get('bm_location'))      + r" & "
            + _fmt(bm_d.get('max_sf'))           + r" & "
            + _tex(bm_d.get('sf_girder', '---')) + r" & "
            + _fmt(bm_d.get('sf_location'))      + r" & "
            + _fmt(rxn_d.get('left_kN'))         + r" & "
            + _fmt(rxn_d.get('right_kN'))        + r" \\[\reportrowgap]"
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    merged_body = ("\n\\hline\n").join(
        _merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc))
        for lc in all_lcs
    ) if all_lcs else r"--- & --- & --- & --- & --- & --- & --- & --- & --- \\[\reportrowgap]"

    reaction_rows = "\n".join(
        " & ".join((_tex(lc), _fmt(values.get("left_kN")), _fmt(values.get("right_kN"))))
        + r" \\\hline" for lc, values in rxn_summary.items()
    ) or r"\multicolumn{3}{c}{Analysis unavailable} \\\hline"

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    raw_live = _live_mm
    raw_total = _total_mm
    from .summary_values import governing_check
    live_check = governing_check(bridge.output_dict, 13)
    total_check = governing_check(bridge.output_dict, 14)
    def check_text(check):
        if check is None:
            return "Not assessed", "Not assessed", "Not assessed"
        ratio, demand, capacity, label, lc = check
        return (f"{demand:.3f} mm ({_tex(label)}, {_tex(lc)})",
                f"{capacity:.3f} mm", f"{ratio:.3f} --- " + ("PASS" if ratio <= 1 else "FAIL"))
    _live_str, _allow_live_str, _live_status = check_text(live_check)
    _total_str, _allow_total_str, _total_status = check_text(total_check)
    basis_note = (
        "The design checks use the member designer's composite-stiffness-adjusted displacement. "
        "The analysis diagrams show raw grillage displacement. "
        f"Raw 1.0 LL girder maximum is {_fmt(raw_live)} mm and raw DL + LL maximum is {_fmt(raw_total)} mm. "
        "These raw values are reported separately from the adjusted serviceability check. "
        "The 1.0 LL case includes the dynamic allowance applied by the live-load generator."
    )
    trace_lines = []
    for check in (live_check, total_check):
        if check is not None:
            _, _, _, girder, lc = check
            values = bridge.output_dict["design_results"]["per_girder"][girder]["per_lc"][lc]
            ratio = values.get("deflection_stiffness_ratio")
            if ratio is not None:
                trace_lines.append(
                    f"{girder}, {lc}: raw Dy={values['Dy_mm']:.5f} mm, "
                    f"Isteel={values['deflection_steel_I_mm4']:.3f} mm4, "
                    f"Icomp={values['deflection_composite_I_mm4']:.3f} mm4, "
                    f"r=max(Icomp/Isteel,1)={ratio:.6f}; design Dy=raw Dy/r."
                )
    for label, values in bridge.output_dict.get("report.grillage_stiffness", {}).items():
        trace_lines.append(f"{label} analysed steel E={values['E_Pa']:.4g} Pa, "
                           f"Iz={values['Iz_m4']:.8g} m4. Composite inertia is not assigned to these longitudinal elements.")
    trace_lines.append("The scalar adjustment uses final design-section properties; it is an approximate post-processing assumption, not a composite-model reanalysis.")
    basis_note += " " + " ".join(trace_lines)
    thermal_note = ""
    if not any(" TL" in str(lc) for lc in all_lcs):
        thermal_note = "No standalone temperature load result is available. The generated combination definitions do not establish that a missing thermal action was analysed."
    expression_groups = {}
    for lc in all_lcs:
        if ":" in lc:
            expression_groups.setdefault(lc.split(":", 1)[1].strip(), []).append(lc.split(":", 1)[0])
    matching = [", ".join(labels) for labels in expression_groups.values() if len(labels) > 1]
    unavailable = bridge.output_dict.get("report.unavailable_actions")
    combination_note = (
        "Combination labels list only the actions actually added to the solver. "
        "Unavailable actions are omitted, so identical applied expressions can legitimately give identical responses. "
        + ("Matching applied expressions occur for " + "; ".join(matching) + "." if matching else "")
    )
    if unavailable:
        combination_note += " Requested actions unavailable: " + ", ".join(unavailable) + ". Coverage is incomplete; no complete compliance claim is made."
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members use the saved steel girder properties, and transverse members represent the deck grid. The composite deflection adjustment is applied during design post-processing. This section summarizes the critical output from that analysis.

\noindent """ + _tex(thermal_note + " " + combination_note) + r"""
\vspace{1em}
\begingroup
\footnotesize

\begin{longtable}{\AnalysisDemandColumns}

\caption{\textbf{Summary of Maximum Demands}}\\
\hline
\textbf{Load case / combination}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\makecell{\textbf{End vertical}\\\textbf{force sums (kN)}}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Start}}
& \makecell{\textbf{Finish}}\\
\hline
\endfirsthead

\hline
\textbf{Load case / combination}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\makecell{\textbf{End vertical}\\\textbf{force sums (kN)}}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Start}}
& \makecell{\textbf{Finish}}\\
\hline
\endhead

""" + merged_body + r"""

\hline
\end{longtable}
\endgroup

\noindent End-force sums are derived from the first and last longitudinal member vertical forces. Direct nodal support reactions are not stored in the analysis dataset. Global x increases along the span, y is vertical, and z is transverse. End sums use Vi at the start and minus Vj at the finish, divided by 1000 to obtain kN. Locations are global x coordinates in metres.
\vspace{1em}
\begin{longtable}{\ReactionsAtSupportsColumns}
\caption{\textbf{Support-end Vertical Force Sums}}\\
\reporthead{\textbf{Load Case} & \textbf{Start-end sum (kN)} & \textbf{Finish-end sum (kN)}}
""" + reaction_rows + r"""
\end{longtable}

\vspace{1em}
\Needspace{14\baselineskip}
\begin{longtable}{\DeflectionSummaryLiveLoadTotalColumns}
\caption{\textbf{Deflection Summary (Live Load \& Total Load)}}\\
\reporthead{\textbf{parameter} & \textbf{value}}
\textnormal{Design deflection due to Live Load, $\delta_{LL}$} & """ + _live_str + r""" \\[\reportrowgap]
\hline
\textnormal{Allowable Live Load Deflection ($\Delta_{allow}$)} & """ + _allow_live_str + r""" \\[\reportrowgap]
\hline
\textnormal{Live Load UR and Status} & """ + _live_status + r""" \\[\reportrowgap]
\hline
\textnormal{Design deflection due to Total Load, $\delta_{total}$} & """ + _total_str + r""" \\[\reportrowgap]
\hline
\textnormal{Allowable Total Deflection ($\Delta_{allow}$)} & """ + _allow_total_str + r""" \\[\reportrowgap]
\hline
\textnormal{Total Load UR and Status} & """ + _total_status + r""" \\[\reportrowgap]
\hline
\end{longtable}

\vspace{1em}
\noindent """ + _tex(basis_note).replace("mm4", r"mm$^4$").replace("m4", r"m$^4$") + r"""
""" + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth') + r"""
"""

