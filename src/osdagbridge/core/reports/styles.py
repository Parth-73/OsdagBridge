"""Shared page geometry, typography, table and chart styles."""
from .report_utils import _tex

CHART_COLOR = "#476b73"
FAIL_COLOR = "#b63834"

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper, left=18mm,right=18mm,top=16mm,bottom=18mm,includeheadfoot,headheight=18pt,footskip=26pt]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    skip=3pt,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{0pt}
\setlength{\LTpost}{6pt}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Prevent tables from overflowing past the page bottom:
% if fewer than 5 baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}

\definecolor{osdagGreen}{HTML}{91B014}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{\small """ + pn + r""" \quad """ + jn + r"""}
  \fancyhead[R]{\small """ + rd + r""" \quad """ + rv + r"""}
  \fancyfoot[L]{\footnotesize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\footnotesize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrulewidth}{0.6pt}
  \renewcommand{\footrulewidth}{0.4pt}
}
\fancypagestyle{plain}[main]{}
\fancypagestyle{firstpage}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

\newcolumntype{\ProjectDetailsColumns}{|L{5.5cm}|L{8.5cm}|}
\newcolumntype{\TypicalSectionDetailsColumns}{|L{5.5cm}|p{10.0cm}|}
\newcolumntype{\GirderGeneralInformationColumns}{|L{2.2cm}|L{1.8cm}|p{3.8cm}|p{3.8cm}|p{3.8cm}|}
\newcolumntype{\GirderSectionDimensionsColumns}{|L{1.8cm}|L{2.3cm}|L{1.8cm}|p{4.8cm}|p{4.8cm}|}
\newcolumntype{\GirderRestraintAndStiffenerDetailsColumns}{|L{1.4cm}|p{2.2cm}|p{2.2cm}|p{3.0cm}|p{2.4cm}|p{2.2cm}|}
\newcolumntype{\MemberPropertiesColumns}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|C{1.8cm}|}
\newcolumntype{\VehicleLiveLoadsColumns}{|L{4.5cm}|L{8cm}|C{2cm}|}
\newcolumntype{\LoadCombinationsColumns}{|C{4.0cm}|p{11.5cm}|}
\newcolumntype{\ReactionsAtSupportsColumns}{|>{\centering\arraybackslash}p{5.2cm}|>{\centering\arraybackslash}p{5.2cm}|>{\centering\arraybackslash}p{5.2cm}|}
\newcolumntype{\DeflectionSummaryLiveLoadTotalColumns}{|L{7cm}|p{8.5cm}|}
\newcolumntype{\IntermediateStiffenerChecksColumns}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\newcolumntype{\GirderSectionPropertiesFinalOptimizedColumns}{|C{2.5cm}|L{8.0cm}|>{\centering\arraybackslash}p{5.0cm}|}
\newcolumntype{\GirderSectionClassificationColumns}{|C{2.5cm}|L{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{4.0cm}|}
\newcolumntype{\StiffenerDesignSummaryColumns}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}p{6.5cm}|}
\newcolumntype{\EndPanelStiffenerChecksColumns}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\newcolumntype{\ServiceabilityDeflectionChecksColumns}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\newcolumntype{\ServiceabilityFatigueAssessmentColumns}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\newcolumntype{\GirderDesignSummaryDcrUtilizationColumns}{|C{1.6cm}|>{\centering\arraybackslash}p{3.6cm}|C{2.4cm}|C{2.0cm}|C{2.1cm}|C{1.7cm}|C{1.5cm}|}
\newcolumntype{\ShearConnectorCapacityColumns}{|L{3.6cm}|C{5.6cm}|>{\centering\arraybackslash}p{2.6cm}|L{3.0cm}|}
\newcolumntype{\ShearConnectorSpacingColumns}{|L{3.2cm}|>{\centering\arraybackslash}p{4.3cm}|>{\centering\arraybackslash}p{4.3cm}|C{2.0cm}|}
\newcolumntype{\TransverseShearAndDetailingChecksColumns}{|L{5.3cm}|>{\arraybackslash}p{7.2cm}|C{2.0cm}|}
\newcolumntype{\DeckSlabFlexureCheckColumns}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\newcolumntype{\DeckSlabCantileverOverhangFlexureColumns}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\newcolumntype{\CrackWidthCheckDeckSlabColumns}{|L{7cm}|>{\arraybackslash}p{8.5cm}|}
\newcolumntype{\ReinforcementDetailingSummaryDeckSlabColumns}{|L{5.5cm}|>{\centering\arraybackslash}p{4.1cm}|>{\centering\arraybackslash}p{4.1cm}|C{1.8cm}|}
\newcolumntype{\CrossBracingConnectionAndSectionColumns}{|C{2.0cm}|L{2.0cm}|L{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\newcolumntype{\CrossBracingSlendernessRatioCheckColumns}{|C{2.2cm}|L{2.2cm}|L{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\newcolumntype{\CrossBracingDesignCapacitySummaryColumns}{|C{2.0cm}|L{1.8cm}|C{2.2cm}|C{3.0cm}|C{1.8cm}|C{1.8cm}|C{1.2cm}|C{1.8cm}|}
\newcolumntype{\OverallDesignCheckSummaryAllColumns}{|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|}
\newcolumntype{\BillOfMaterialsColumns}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\newcolumntype{\IrcCodesColumns}{|c|c|p{13cm}|}
\newcolumntype{\FinalGirderGeometryAndGoverningColumns}{|L{1.8cm}|L{2cm}|L{4.5cm}|L{4.1cm}|C{1.5cm}|}
\newcolumntype{\ReportGeneratorColumns}{|L{4cm}|L{10cm}|}

\newcolumntype{\VehicleClassColumns}{|L{4.1cm}|C{2.6cm}|C{2.7cm}|C{2.8cm}|C{2.4cm}|}
\newcolumntype{\AnalysisDemandColumns}{|
>{\centering\arraybackslash}p{3.1cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.6cm}|
>{\centering\arraybackslash}p{1.6cm}|}
% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\newcommand{\reporthead}[1]{\hline\rowcolor{osdagGreen!14}#1\\\hline\endfirsthead\hline\rowcolor{osdagGreen!14}#1\\\hline\endhead}
\newcommand{\reportrowgap}{3pt}
\raggedbottom
\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}
\begin{document}
"""
