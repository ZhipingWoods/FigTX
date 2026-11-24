#!/usr/bin/env python3
r"""论文图复刻 · TikZ 部分（架构图 / 机制示意图）。

对应参考图：
  05-架构-整体流程与模块放大
  06-机制-张量结构和缓存复用
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

# 架构图专用样式：参考图用的是浅蓝/橙/粉/绿配色
ARCH_STYLES = r"""
\definecolor{fxblue}{HTML}{CCE1F2}
\definecolor{fxblue2}{HTML}{E8F2FA}
\definecolor{fxorg}{HTML}{F9A03F}
\definecolor{fxorgd}{HTML}{C4701A}
\definecolor{fxpnk}{HTML}{FADBD8}
\definecolor{fxpnkd}{HTML}{D98880}
\definecolor{fxgrn}{HTML}{D5F0D0}
\definecolor{fxgrnd}{HTML}{7CB342}
\definecolor{fxbluepad}{HTML}{3B6CF0}
\definecolor{fxkv}{HTML}{8C1D2F}
\definecolor{fxscale}{HTML}{FBF0C4}
\definecolor{fxmatmul}{HTML}{DCDCDC}
\definecolor{fxrelu}{HTML}{FBE4E0}
\definecolor{fxcolblue}{HTML}{D6E8F7}
\definecolor{fxgreen2}{HTML}{78B808}
\definecolor{fxred2}{HTML}{A81838}
\tikzset{
  box/.style={draw=black!55, line width=.5pt, rounded corners=3pt, align=center,
              font=\scriptsize, inner sep=3pt, minimum height=7mm},
  blu/.style={box, fill=fxblue},
  blu2/.style={box, fill=fxblue2},
  org/.style={box, fill=fxorg, draw=fxorgd, font=\scriptsize\bfseries},
  pnk/.style={box, fill=fxpnk, draw=fxpnkd},
  grn/.style={box, fill=fxgrn, draw=fxgrnd},
  arr/.style={-{Stealth[length=1.6mm,width=1.2mm]}, line width=.55pt, draw=black!75},
  lab/.style={font=\tiny, text=black!70, inner sep=1pt},
}
"""


def fig05() -> str:
    return r"""
\begin{tikzpicture}[x=1cm, y=0.871cm,
  box/.style={draw=black, line width=1.2pt, rounded corners=4pt, align=center,
              font=\scriptsize, inner sep=2.2pt, minimum height=6.2mm},
  org/.style={box, fill=fxorg, draw=black!65, font=\scriptsize\bfseries},
  pnk2/.style={box, fill=fxpnk, draw=black!40},
  lin/.style={box, fill=white},
  arr/.style={-{Stealth[length=2.0mm,width=1.6mm]}, line width=.8pt, draw=black!90},
  lab2/.style={font=\tiny, text=black!80, inner sep=1pt},
  ttl/.style={font=\small\bfseries, align=center},
]

% ================= 分隔线 =================
\draw[dashed, line width=1.1pt, black!80] (14.55,-0.2) -- (14.55,11.6);
\draw[dashed, line width=1.1pt, black!80] (0.0,6.95) -- (14.40,6.95);

% ================= (a) 训练流水线 =================
% 前三组：叠层彩色帧；第四组：灰色（t=1 已完全去噪）
\foreach \i/\x in {0/-0.30, 1/3.00, 2/6.30}{
  \begin{scope}[shift={(\x,9.55)}]
    \foreach \k in {5,4,3,2,1,0}{
      \begin{scope}[shift={(\k*0.12,\k*0.12)}]
        \clip[rounded corners=3pt] (0,0) rectangle (2.20,2.20);
        % 纯 TikZ 绘制的"照片感"占位（不依赖外部图片）
        \fill[black!90] (0,0) rectangle (2.20,2.20);
        \fill[cyan!45!black, opacity=0.55] (0.10,0.10) rectangle (1.20,1.65);
        \fill[red!70!black, opacity=0.50] (0.95,0.35) rectangle (2.10,1.20);
        \fill[magenta!70!black, opacity=0.40] (0.25,0.62) rectangle (0.85,1.95);
        \fill[orange!85!black, opacity=0.55] (1.45,0.20) rectangle (2.05,0.95);
        \fill[white, opacity=0.12] (0.15,0.15) rectangle (0.55,0.55);
      \end{scope}
      \draw[black!50, line width=1.0pt, rounded corners=3pt]
        (\k*0.11,\k*0.11) rectangle ++(2.20,2.20);
    }
  \end{scope}
}
% 第四组：灰色叠层
\begin{scope}[shift={(8.90,9.45)}]
  \foreach \k in {5,4,3,2,1,0}{
    \fill[black!30, rounded corners=3pt] (\k*0.11,\k*0.11) rectangle ++(2.20,2.20);
    \draw[black!50, line width=1.0pt, rounded corners=3pt] (\k*0.11,\k*0.11) rectangle ++(2.20,2.20);
  }
\end{scope}

% 块标签
\node[font=\small] at (0.95,9.15) {$Block^0_{t=0}$};
\node[font=\small] at (4.25,9.15) {$Block^1_{t=0.2}$};
\node[font=\small] at (7.55,9.15) {$Block^2_{t=0.7}$};
\node[font=\small] at (10.10,9.15) {$Block^3_{t=1}$};

% 上方跨块弧线
\foreach \i/\j/\bend in {0/1/28, 0/2/24, 0/3/20, 1/2/28, 1/3/24, 2/3/28}{
  \draw[arr, draw=teal!70!black, line width=1.2pt]
    (\i*3.30+1.10, 11.85) to[bend left=\bend] (\j*3.30+1.10, 11.85);
}

% 因果线性注意力小图（放在左半区右侧，x 10.3–13.6）
\begin{scope}[shift={(12.35,10.60)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r>\c ? 0 : 2}
      \ifnum\pgfmathresult=0
        \fill[black!18] (\c*0.34,-\r*0.34) rectangle ++(0.32,0.32);
      \else
        \fill[green!72!black] (\c*0.34,-\r*0.34) rectangle ++(0.32,0.32);
      \fi
    }
  }
  \draw[black!65, line width=1.2pt] (0,0.38) rectangle (1.54,-1.16);
  \node[font=\footnotesize] at (-0.15,0.50) {$d$};
  \node[font=\footnotesize] at (0.72,0.50) {$d$};
  \node[font=\tiny, anchor=north west, align=left] at (0.0,-1.10) {$\sum_{i=1}^{k}K_iV_i$\\Cumulative Sum};

\end{scope}
\node[font=\footnotesize, anchor=south] at (12.78,11.80) {Causal Linear Attention};

\node[font=\large\bfseries] at (7.40,8.15) {(a). Block-wise autoregressive training pipeline};

% ================= (b) 整体架构 =================
% 输入：叠层帧（放大到 2.15，起始行与原图对齐）
\begin{scope}[shift={(0.15,3.15)}]
  \foreach \k in {5,4,3,2,1,0}{
    \begin{scope}[shift={(\k*0.11,\k*0.11)}]
      \clip[rounded corners=2pt] (0,0) rectangle (2.15,2.15);
        % 纯 TikZ 绘制的输入叠层占位
        \fill[black!88] (0,0) rectangle (2.15,2.15);
        \fill[cyan!45!black, opacity=0.55] (0.12,0.12) rectangle (1.35,1.55);
        \fill[red!70!black, opacity=0.50] (1.05,0.40) rectangle (2.02,1.10);
        \fill[magenta!65!black, opacity=0.38] (0.30,0.70) rectangle (0.90,1.95);
      \draw[black!60, line width=0.8pt, rounded corners=2pt] (0,0) rectangle (2.15,2.15);
    \end{scope}
  }
\end{scope}
\node[font=\small] at (1.30,2.72) {$[1\!+\!T, H, W, 3]$};

% AutoEncoder：左窄右宽八边形梯形（加高到 2.45、加宽到 3.15）
\begin{scope}[shift={(4.45,2.95)}]
  \fill[fxblue2] (0.00,0.64) -- (0.60,0.00) -- (2.85,0.00) -- (2.25,0.64) -- (2.25,1.81) -- (2.85,2.45) -- (0.60,2.45) -- (0.00,1.81) -- cycle;
  \draw[black!70, line width=1.1pt] (0.00,0.64) -- (0.60,0.00) -- (2.85,0.00) -- (2.25,0.64) -- (2.25,1.81) -- (2.85,2.45) -- (0.60,2.45) -- (0.00,1.81) -- cycle;
  \node[font=\normalsize] at (1.42,1.22) {AutoEncoder};
\end{scope}
\draw[arr, line width=1.4pt] (2.55,4.18) -- (4.45,4.18);

% N x 大框：加高、深色描边
\fill[fxblue, opacity=.62, rounded corners=12pt] (7.55,2.75) rectangle (14.35,6.20);
\draw[black!75, line width=1.2pt, rounded corners=12pt] (7.55,2.75) rectangle (14.35,6.20);
\node[font=\large\bfseries, text=red!70!black, anchor=south west] at (7.75,2.88) {$\mathbf{N\times}$};

% 三列背景带（更明显）
\fill[fxpnk, opacity=.85, rounded corners=5pt] (9.95,2.90) rectangle (11.45,6.05);
\fill[fxgrn, opacity=.70, rounded corners=5pt] (12.15,2.90) rectangle (13.35,6.05);

% 大号竖排标签（原图里这是最醒目的元素）
\node[font=\Large, rotate=90] at (8.85,4.47) {Linear Attn};
\node[font=\Large, rotate=90] at (10.70,4.47) {Cross Attn};
\node[font=\Large, rotate=90] at (12.75,4.47) {Mix FFN};

% 大 ⊕ 在框内右侧
\node[circle, draw=black!85, line width=1.1pt, fill=white, minimum size=0.52cm,
      inner sep=0pt, font=\large] (plus) at (13.85,4.47) {$+$};

\draw[arr, line width=1.2pt] (7.55,4.22) -- (8.40,4.22);
\draw[arr, line width=1.2pt] (9.30,4.22) -- (9.85,4.22);
\draw[arr, line width=1.2pt] (11.55,4.22) -- (12.05,4.22);
\draw[arr, line width=1.2pt] (13.45,4.22) -- (plus.west);
\draw[arr, line width=1.2pt] (plus.east) -- (14.95,4.22);

% 彩色图标：雪花（大）/ 火焰（大），置于框外上方
\begin{scope}[shift={(7.30,6.35)}]
  \foreach \a in {0,60,120,180,240,300}{
    \draw[cyan!75!black, line width=1.6pt] (0,0) -- (\a:0.34);
    \draw[cyan!75!black, line width=1.2pt] (\a:0.18) -- (\a+30:0.26);
  }
  \fill[cyan!75!black] (0,0) circle (0.06);
\end{scope}
\begin{scope}[shift={(14.05,6.40)}]
  \fill[orange!95!black] (0,-0.30) .. controls (-0.26,0.06) and (-0.13,0.24) .. (0,0.38)
                        .. controls (0.13,0.24) and (0.26,0.06) .. (0,-0.30) -- cycle;
  \fill[red!85!black] (0,-0.22) .. controls (-0.13,0.00) and (-0.07,0.11) .. (0,0.18)
                      .. controls (0.07,0.11) and (0.13,0.00) .. (0,-0.22) -- cycle;
  \fill[yellow!85!white] (0,-0.14) .. controls (-0.06,0.00) and (-0.03,0.05) .. (0,0.09)
                        .. controls (0.03,0.05) and (0.06,0.00) .. (0,-0.14) -- cycle;
\end{scope}

% 文本分支（框更大）
\node[draw=black!75, line width=1.1pt, rounded corners=6pt, fill=white, minimum width=3.6cm,
      minimum height=1.15cm, font=\footnotesize, align=left, inner sep=4pt] (capbox)
  at (1.95,1.45) {\textbf{\textit{A cyberpunk cat with a}}\\[1pt]\textbf{\textit{sian that says "SANA"}}};
\node[pnk2, line width=1.1pt, minimum width=2.05cm, minimum height=1.05cm, font=\small] (rw) at (5.25,1.45) {Rewriter};
\node[pnk2, line width=1.1pt, minimum width=2.35cm, minimum height=1.05cm, font=\small] (llm) at (8.05,1.45) {Small LLM};
\node[pnk2, line width=1.1pt, minimum width=1.95cm, minimum height=1.05cm, font=\small] (te) at (10.85,1.45) {Time Emb};
\draw[arr, line width=1.2pt] (capbox.east) -- (rw.west);
\draw[arr, line width=1.2pt] (rw.east) -- (llm.west);
\draw[arr, line width=1.2pt] (llm.east) -- (te.west);
% 两条上箭头分别指向 Cross Attn 与 Mix FFN 底部
\draw[arr, line width=1.2pt] (8.05,2.45) -- (8.05,2.72) -- (10.70,2.72) -- (10.70,2.80);
\draw[arr, line width=1.2pt] (10.85,2.45) -- (10.85,2.72) -- (12.75,2.72) -- (12.75,2.80);

\node[font=\Large\bfseries] at (7.4,0.05) {(b). Architecture overview of our SANA-Video.};

% ================= (c) Linear DiT module =================
% ---- 面板标题（在框上方）
\node[font=\large\bfseries] at (18.40,12.55) {Linear Attention};
\node[font=\large\bfseries] at (24.15,12.55) {Mix-FFN};

% ---- Linear Attention 面板（方块按原图配色 + 加粗）
\fill[fxblue, opacity=.62, rounded corners=10pt] (14.55,1.45) rectangle (22,12);

\node[box, fill=fxscale, draw=black!85, line width=1.3pt, minimum width=2.55cm, minimum height=1.15cm, font=\small\bfseries] (sc) at (18.4,10.9) {Scale};
\node[box, fill=fxmatmul, draw=black!85, line width=1.3pt, minimum width=3.00cm, minimum height=1.15cm, font=\small\bfseries] (mm1) at (18.4,9.55) {MatMul};
\node[box, fill=fxmatmul, draw=black!85, line width=1.3pt, minimum width=3.00cm, minimum height=1.15cm, font=\small\bfseries] (mm0) at (19.15,8) {MatMul};

\node[box, fill=fxorg, draw=black!85, line width=1.3pt, minimum width=2.20cm, minimum height=1.15cm, font=\small\bfseries] (ropeL) at (16.15,6.4) {3D RoPE};
\node[box, fill=fxorg, draw=black!85, line width=1.3pt, minimum width=2.20cm, minimum height=1.15cm, font=\small\bfseries] (ropeR) at (20.65,6.4) {3D RoPE};
\node[box, fill=fxrelu, draw=black!85, line width=1.3pt, minimum width=1.95cm, minimum height=1.05cm, font=\small\bfseries] (rl) at (16.15,4.95) {ReLU};
\node[box, fill=fxrelu, draw=black!85, line width=1.3pt, minimum width=1.95cm, minimum height=1.05cm, font=\small\bfseries] (rr) at (20.65,4.95) {ReLU};
\node[box, fill=white, draw=black!85, line width=1.3pt, minimum width=1.95cm, minimum height=1.05cm, font=\small\bfseries] (lnQ) at (16.15,3.55) {Linear};
\node[box, fill=white, draw=black!85, line width=1.3pt, minimum width=1.95cm, minimum height=1.05cm, font=\small\bfseries] (lnK) at (18.4,3.55) {Linear};
\node[box, fill=white, draw=black!85, line width=1.3pt, minimum width=1.95cm, minimum height=1.05cm, font=\small\bfseries] (lnV) at (20.65,3.55) {Linear};

\node[font=\small] at (16.15,2.8) {$Q$};
\node[font=\small] at (18.4,2.8) {$K$};
\node[font=\small] at (20.65,2.8) {$V$};

\draw[arr, line width=1.1pt] (lnQ) -- (rl);
\draw[arr, line width=1.1pt] (rl) -- (ropeL);
\draw[arr, line width=1.1pt] (lnK) -- (rr);
\draw[arr, line width=1.1pt] (rr) -- (ropeR);
\draw[arr, line width=1.1pt] (ropeL.north) |- (17.75,8);
\draw[arr, line width=1.1pt] (ropeR.north) -- (20.65,7.2) -- (20.95,7.2) -- (20.95,8) -- (20.7,8);
\draw[arr, line width=1.1pt] (lnV.north) -- (20.65,3.2) -- (21.7,3.2) -- (21.7,8) -- (21.1,8);
\draw[arr, line width=1.1pt] (mm0.north) -- (19.15,8.95);
\draw[arr, line width=1.1pt] (mm1) -- (sc);
\draw[arr, line width=1.1pt] (sc.north) -- (18.4,11.6);

\node[font=\footnotesize, fill=white, inner sep=1pt] at (16.95,10.05) {$n\times d$};
\node[font=\footnotesize, fill=white, inner sep=1pt] at (20.55,8.45) {$n\times d$};
\node[font=\footnotesize, fill=white, inner sep=1pt] at (16.75,7.55) {$d\times n$};
\node[font=\footnotesize, fill=white, inner sep=1pt] at (21.55,7.35) {$d\times d$};

\node[font=\small, anchor=east] at (21.85,2.3) {Cost: $\mathcal{O}(n)$};

% ---- Mix-FFN 面板
\fill[fxblue, opacity=.62, rounded corners=10pt] (22.35,1.45) rectangle (26.6,12);

\node[box, fill=fxorg, draw=black!85, line width=1.3pt, minimum width=3.30cm, minimum height=1.45cm,
      font=\small\bfseries, align=center] (tmp) at (24.15,10.5)
  {Temporal\\$3\times1\times1$ ConvLayer};
\node[box, fill=fxgrn, draw=black!85, line width=1.3pt, minimum width=3.30cm, minimum height=1.15cm, font=\small\bfseries] (c1a) at (24.15,8.85) {$1\times1$ ConvLayer};
\node[box, fill=fxgrn, draw=black!85, line width=1.3pt, minimum width=3.30cm, minimum height=1.15cm, font=\small\bfseries] (c2) at (24.15,6.05) {$1\times3\times3$ ConvLayer};
\node[box, fill=fxgrn, draw=black!85, line width=1.3pt, minimum width=3.30cm, minimum height=1.15cm, font=\small\bfseries] (c3) at (24.15,3.55) {$1\times1$ ConvLayer};
\node[circle, draw=black!85, line width=1.2pt, fill=white, minimum size=0.50cm, inner sep=0pt, font=\small] (mul) at (23.45,7.4) {$\otimes$};
\node[box, fill=fxrelu, draw=black!85, line width=1.3pt, minimum width=1.85cm, minimum height=1.05cm, font=\small\bfseries] (silu) at (25.45,7.4) {SiLU};

\draw[arr, line width=1.1pt] (c3) -- (c2);
\draw[arr, line width=1.1pt] (c2.north) -- (23,7.4) -- (23.2,7.4);
\draw[arr, line width=1.1pt] (silu.west) -- (mul.east);
\draw[arr, line width=1.1pt] (mul.north) -- (23.45,8.27) -- (23.7,8.27);
\draw[arr, line width=1.1pt] (c1a) -- (tmp);
\draw[arr, line width=1.1pt] (tmp.north) -- (24.15,11.45);
\end{tikzpicture}
"""

def fig06() -> str:
    return r"""
\begin{tikzpicture}[x=1cm, y=0.946cm]
\tikzset{
  cell/.style={draw=black!95, line width=1.1pt, inner sep=0pt},
  tok/.style={cell, fill=fxcolblue},
  mask/.style={cell, fill=black!28},
  kv/.style={cell, fill=fxred2},
  cmp/.style={cell, fill=fxgreen2},
  ttl/.style={font=\small, align=center},
  lbl/.style={font=\footnotesize},
  arr2/.style={-{Stealth[length=2.0mm,width=1.5mm]}, line width=1.0pt, draw=black!90},
  brc/.style={decorate, decoration={brace, amplitude=5pt}, black!75},
}

% ================= 图例 =================
\begin{scope}[shift={(1.59,6.45)}, every node/.style={font=\small}]
  \draw[cell, fill=white] (0,0) rectangle (0.44,0.44);
  \node[anchor=west] at (0.56,0.22) {Token};
  \draw[cell, fill=black!28] (2.30,0) rectangle (2.74,0.44);
  \node[anchor=west] at (2.86,0.22) {Mask};
  \draw[cell, fill=red!58!black] (4.40,0) rectangle (4.84,0.44);
  \node[anchor=west] at (4.96,0.22) {KV Cache};
  \draw[cell, fill=green!68!black] (7.10,0) rectangle (7.54,0.44);
  \node[anchor=west] at (7.66,0.22) {Compute};
\end{scope}

% ================= (a-1) Vanilla Attention =================
\begin{scope}[shift={(1.34,4.76)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \draw[cmp] (\c*1.05,-\r*1.05) rectangle ++(1.05,1.05);
    }
  }
  \node[lbl, anchor=east] at (-0.17,-0.44) {$Q_1$};
  \node[lbl, anchor=east] at (-0.17,-3.95) {$Q_N$};
  \node[lbl] at (-0.17,-2.2) {$\vdots$};
  \node[lbl, anchor=south] at (0.44,0.12) {$K_1$};
  \node[lbl, anchor=south] at (3.95,0.12) {$K_N$};
  \node[lbl] at (2.2,0.51) {$\cdots$};
  \node[ttl, anchor=north] at (2.2,-4.82) {Vanilla Attention};
\end{scope}

\node[font=\Large] at (6.77,2.93) {$\times$};

% ================= (a-2) Linear Attention =================
\begin{scope}[shift={(7.44,4.76)}]
  % V 列
  \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*1.05) rectangle ++(1.05,1.05); }
  \node[lbl, anchor=east] at (-0.17,-0.44) {$V_1$};
  \node[lbl, anchor=east] at (-0.17,-3.95) {$V_N$};
  \node[lbl, anchor=south] at (0.44,0.12) {$d$};
  \node[lbl] at (0.44,-2.2) {$\vdots$};
  \draw[brc] (1.46,0.05) -- (1.46,-2.15);
  \draw[brc] (1.46,-2.24) -- (1.46,-4.44);

  \node[font=\Large] at (2.81,2.5) {$\times$};

  % Q 列
  \begin{scope}[shift={(4.09,0)}]
    \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*1.05) rectangle ++(1.05,1.05); }
    \node[lbl, anchor=east] at (-0.2,-0.44) {$Q_1$};
    \node[lbl, anchor=east] at (-0.2,-3.95) {$Q_N$};
    \node[lbl, anchor=south] at (0.44,0.12) {$d$};
    \node[lbl] at (0.44,-2.2) {$\vdots$};
    \draw[brc] (-0.98,0.05) -- (-0.98,-2.15) node[midway, left=3pt, font=\scriptsize] {Block$_1$};
    \draw[brc] (-0.98,-2.24) -- (-0.98,-4.44) node[midway, left=3pt, font=\scriptsize] {Block$_N$};
  \end{scope}

  \node[font=\Large] at (6.53,2.5) {$\times$};

  % Σ 结果块
  \begin{scope}[shift={(7.26,-2.2)}]
    \draw[cmp] (0,0) rectangle (1.05,1.05);
    \node[font=\normalsize] at (0.44,0.44) {$\sum$};
    \node[lbl, anchor=south] at (0.44,0.98) {$d$};
    \node[lbl, anchor=east] at (-0.15,0.44) {$d$};
  \end{scope}

  \node[ttl, anchor=north] at (4.51,-4.82) {Linear Attention};
\end{scope}

% ================= (a-3) Causal Linear Attention =================
\begin{scope}[shift={(17.02,4.76)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \pgfmathparse{\r<\c ? 0 : 1}
      \ifnum\pgfmathresult=0
        \draw[mask] (\c*1.05,-\r*1.05) rectangle ++(1.05,1.05);
      \else
        \draw[cmp] (\c*1.05,-\r*1.05) rectangle ++(1.05,1.05);
      \fi
    }
  }
  % 第 3、4 行的前段标成 KV Cache
  \foreach \c in {0,1,2}{
    \draw[kv] (\c*1.05,-1.80) rectangle ++(1.05,1.05);
    \draw[kv] (\c*1.05,-2.52) rectangle ++(1.05,1.05);
  }
  \node[lbl, anchor=south] at (0.44,0.12) {$d$};
  \node[lbl, anchor=east] at (-0.2,-0.44) {$Q_1$};
  \node[lbl, anchor=east] at (-0.2,-3.95) {$Q_N$};
  \draw[brc] (-0.98,0.05) -- (-0.98,-2.15) node[midway, left=3pt, font=\scriptsize] {Block$_1$};
  \draw[brc] (-0.98,-2.24) -- (-0.98,-4.44) node[midway, left=3pt, font=\scriptsize] {Block$_N$};

  % 累积求和箭头
  \draw[arr2] (-0.02,-2.2) -- (2.81,-2.2);
  \node[font=\scriptsize, anchor=west] at (2.9,-2.2) {$\sum_{i=1}^{2}K_iV_i$};
  \draw[arr2] (-0.02,-3.07) -- (2.81,-3.07);
  \node[font=\scriptsize, anchor=west] at (2.9,-3.07) {$\sum_{i=1}^{3}K_iV_i$};
  \draw[arr2] (-0.02,-3.9) -- (3.72,-3.9);
  \node[font=\scriptsize, anchor=north] at (2.2,-4.07) {Cumulative Sum};

  \node[ttl, anchor=north] at (2.2,-4.82) {Causal Linear Attention};
\end{scope}

% ================= (b) Block Causal Mix-FFN =================
\begin{scope}[shift={(23.45,2.35)}]
  \node[font=\small] at (1.89,3.05) {$\vdots$};

  \foreach \i/\name/\fc/\tc in {
      0/{Token-2}/fxgrn/black,
      1/{Token-1}/fxgrn/black,
      2/{Zero Padding}/fxbluepad/white,
      3/{Cached Token-1}/fxkv/white,
      4/{Token$_0$}/fxgrn/black,
      5/{Token$_1$}/fxgrn/black}{
    \pgfmathsetmacro{\yy}{2.60-\i*0.86}
    \node[draw=black!80, line width=1.0pt, rounded corners=3pt, fill=\fc,
          minimum width=3.45cm, minimum height=0.94cm, font=\footnotesize, text=\tc]
      at (1.55,\yy) {\name};
  }
  \node[font=\small] at (1.89,-2.10) {$\vdots$};

  % 蓝色复用弧线
  \draw[arr2, draw=blue!80, line width=1.3pt]
    (3.84,1.6) to[bend left=42] (3.84,0.55);

  \draw[brc] (4.25,3.68) -- (4.25,1.65) node[midway, right=5pt, font=\footnotesize] {Block$_1$};
  \draw[brc] (4.25,1.24) -- (4.25,-2.26) node[midway, right=5pt, font=\footnotesize] {Block$_2$};
\end{scope}

\node[font=\small\bfseries] at (6.34,-1.55) {(a) Block Causal Linear Attention};
\node[font=\small\bfseries] at (25.74,-1.60) {(b) Block Causal Mix-FFN};
\end{tikzpicture}
"""


REPLICAS = [
    ("05-architecture", fig05, "架构 · 整体流程与模块放大",
     "三面板：(a) 分块自回归训练流水线 + 因果线性注意力小图；(b) 整体架构（AutoEncoder→Linear Attn→Cross Attn→Mix FFN）；(c) Linear DiT 模块内部（Linear Attention + Mix-FFN）",
     "architecture", ["CVPR", "ICCV", "NeurIPS"], ["生成"]),
    ("06-mechanism", fig06, "机制 · 张量结构与缓存复用",
     "把 Vanilla / Linear / Causal-Linear Attention 的矩阵运算画成格子对比，红=KV Cache、绿=Compute；(b) 分块 Mix-FFN 的缓存复用",
     "mechanism", ["ICLR", "NeurIPS", "MLSys"], ["系统"]),
]
