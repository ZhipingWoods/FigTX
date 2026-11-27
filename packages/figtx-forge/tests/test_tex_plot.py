import shutil

import pytest
from PIL import Image

from figtx_forge.cli import main
from figtx_forge.plot import run_plot
from figtx_forge.tex import compile_table, table_shape

BOOKTABS = r"""\begin{tabular}{lcc}
\toprule
Method & Acc & F1 \\
\midrule
Ours & \textbf{91.2} & 88.0 \\
Base & 85.1 & 80.3 \\
\bottomrule
\end{tabular}
"""


def test_table_shape():
    tex = r"\begin{tabular}{lcc}\toprule A&B&C\\ \midrule 1&2&3\\ \bottomrule\end{tabular}"
    assert table_shape(tex) == {"rows": 2, "cols": 3, "multicolumn": 0, "multirow": 0}


def test_table_shape_colspec_variants():
    assert table_shape(r"\begin{tabular}{@{}l|*{3}{c}p{2cm}@{}} a\\ \end{tabular}")["cols"] == 5
    assert table_shape(r"\begin{tabularx}{\linewidth}{lXX} a&b&c\\ \end{tabularx}")["cols"] == 3
    t = table_shape(r"\begin{tabular}{ccc}\multicolumn{2}{c}{A} & \multirow{2}{*}{B}\\ 1&2&3\\ \end{tabular}")
    assert (t["rows"], t["multicolumn"], t["multirow"]) == (2, 1, 1)


@pytest.mark.skipif(not shutil.which("tectonic"), reason="no tectonic")
def test_compile_booktabs(tmp_path):
    p = tmp_path / "t.tex"
    p.write_text(BOOKTABS)
    r = compile_table(p, tmp_path / "t.png")
    assert r["ok"], r["log_tail"]
    assert Image.open(r["png"]).width > 100


@pytest.mark.skipif(not shutil.which("tectonic"), reason="no tectonic")
def test_compile_strips_table_float(tmp_path):
    p = tmp_path / "t.tex"
    p.write_text("\\begin{table}[t]\n\\centering\n\\caption{Results}\\label{tab:x}\n" + BOOKTABS + "\\end{table}\n")
    assert compile_table(p, tmp_path / "t.png")["ok"]


def test_tex_missing_tectonic(tmp_path, monkeypatch, capsys):
    p = tmp_path / "t.tex"
    p.write_text(BOOKTABS)
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert main(["tex", str(p), "-o", str(tmp_path / "x.png")]) == 2
    assert "tectonic" in capsys.readouterr().err


def test_run_plot_collects_png(tmp_path):
    s = tmp_path / "plot.py"
    s.write_text("import matplotlib.pyplot as plt\nplt.plot([1, 2])\nplt.savefig('a.png')\n")
    r = run_plot(s, tmp_path / "out")
    assert r["ok"], r["stderr_tail"]
    assert [p.split("/")[-1] for p in r["files"]] == ["a.png"]
    assert (tmp_path / "out" / "a.png").exists()


def test_run_plot_error(tmp_path):
    s = tmp_path / "bad.py"
    s.write_text("raise ValueError('boom')\n")
    r = run_plot(s, tmp_path / "out")
    assert r["ok"] is False and "ValueError" in r["stderr_tail"]
