# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


from .summary_values import component_ratios


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    final = output_dict.get("design_results") or {}
    dimensions = [final.get(key) for key in ("D_mm", "tw_mm", "bf_top_mm", "tf_top_mm", "bf_bot_mm", "tf_bot_mm")]
    sec = _tex("D / tw / btop / ttop / bbot / tbot (mm): " + " / ".join(str(value) if value is not None else "Not assessed" for value in dimensions))

    # ── Pull the stored result dicts once, then work off these locals ─────────
    # (no value is recomputed here — the pipeline already filled these in).
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}

    # Overall Design Status — girder checks only: Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):     # skip edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name

    ratios = component_ratios(output_dict)
    outcomes = {}
    for component, ratio in ratios.items():
        if component == "Plate girders" and failing:
            outcomes[component] = "Fail (" + ", ".join(failing) + ")"
        elif ratio is None:
            outcomes[component] = "Not assessed"
        else:
            outcomes[component] = "Fail" if ratio > 1 else "Pass"
    expected_girders = int(input_dict.get(KEY_TS_NO_OF_GIRDERS) or 0)
    assessed_girders = [key for key, value in per_girder.items() if not key.startswith("EB") and value.get("checks")]
    if len(assessed_girders) != expected_girders and not outcomes["Plate girders"].startswith("Fail"):
        outcomes["Plate girders"] = "Not assessed"
    missing_actions = output_dict.get("report.unavailable_actions")
    coverage = ("Not established" if missing_actions is None else
                "Incomplete: " + ", ".join(missing_actions) if missing_actions else
                "Available for requested combinations")
    failed = [name for name, status in outcomes.items() if status.startswith("Fail")]
    overall_design_status = ("Fail (" + ", ".join(failed) + ")" if failed else
                             "Incomplete" if "Not assessed" in outcomes.values() or missing_actions is None or missing_actions else "Pass")
    available = [(ratio, name) for name, ratio in ratios.items() if ratio is not None]
    overall_utilization_ratio = ""
    if available:
        maximum, component = max(available)
        overall_utilization_ratio = f"{maximum:.2f} ({component})"
        if component != "Plate girders":
            gov_name = component
    outcome_text = r" \\ ".join(_tex(name + ": " + status) for name, status in outcomes.items())

    gov = _tex(gov_name) if gov_name not in (None, '', 'None') else ''
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else ''

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    rows = []
    for label, member in labels:
        checks = (per_girder.get(label) or {}).get("checks", [])
        numeric = [(float(c["dcr"]), c.get("name", "")) for c in checks
                   if isinstance(c.get("dcr"), (int, float))]
        ratio, name = max(numeric, default=(None, ""))
        rows.append(" & ".join((_tex(label), _tex(member), sec, _tex(name),
                                "---" if ratio is None else f"{ratio:.2f}")) + r" \\\hline")
    table1 = (r"""\begin{longtable}{\FinalGirderGeometryAndGoverningColumns}
\caption*{Final girder geometry and governing checks}\\
\reporthead{Girder & Member & Section designation & Governing check & UR}
""" + "\n".join(rows) + r"\end{longtable}")

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}


\begin{tabular}{\ProjectDetailsColumns}
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING, " m")) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS, " mm")) + r""" \\
\hline
\textbf{Overall Design Status} & """ + (_tex(overall_design_status)) + r""" \\
\hline
\textbf{Analysis load coverage} & """ + _tex(coverage) + r""" \\
\hline
\textbf{Governing Check} & """ + gov + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}


""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

\vspace{0.4em}
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent """ + outcome_text + r"""

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:summary-assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

% Restore numbered chapter format
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{-30pt}{10pt}
"""
