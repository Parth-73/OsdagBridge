"""Compile real single-page and multipage tables when TeX tools are available."""
import shutil
import subprocess

import pytest

from osdagbridge.core.reports.styles import preamble


@pytest.mark.skipif(not shutil.which("pdflatex") or not shutil.which("pdftotext"),
                    reason="Requires a PDF compiler and text extractor")
@pytest.mark.parametrize("row_count", [2, 100])
def test_longtable_caption_and_continuation_headers(tmp_path, row_count):
    rows = "\n".join(f"{index} & Value \\\\ \\hline" for index in range(row_count))
    source = preamble("Regression", "", "2026-11-23")
    source += (r"\begin{longtable}{|p{3cm}|p{6cm}|}\caption{RegressionCaption}\\"
               r"\reporthead{HeadingToken & Value}" + rows
               + r"\end{longtable}\end{document}")
    (tmp_path / "table.tex").write_text(source, encoding="utf8")
    for _ in range(2):
        result = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "table.tex"],
                                cwd=tmp_path, capture_output=True)
        assert result.returncode == 0, result.stdout.decode(errors="replace")
    result = subprocess.run(["pdftotext", "-layout", "table.pdf", "-"], cwd=tmp_path,
                            capture_output=True, check=True)
    text = result.stdout.decode()
    pages = [page for page in text.split("\f") if "HeadingToken" in page]
    assert text.count("RegressionCaption") == 1
    assert len(pages) == 1 if row_count == 2 else len(pages) > 1
    assert all(page.count("HeadingToken") == 1 for page in pages)
