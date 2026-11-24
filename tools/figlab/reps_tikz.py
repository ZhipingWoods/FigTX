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
\begin{tikzpicture}[x=1cm, y=1cm,
  box/.style={draw=black!65, line width=.5pt, rounded corners=2.5pt, align=center,
              font=\scriptsize, inner sep=2.2pt, minimum height=6.2mm},
  org/.style={box, fill=fxorg, draw=black!65, font=\scriptsize\bfseries},
  pnk2/.style={box, fill=fxpnk, draw=black!40},
  lin/.style={box, fill=white},
  arr/.style={-{Stealth[length=1.6mm,width=1.2mm]}, line width=.55pt, draw=black!85},
  lab2/.style={font=\tiny, text=black!80, inner sep=1pt},
  ttl/.style={font=\small\bfseries, align=center},
]

% ================= 分隔线 =================
\draw[dashed, line width=1.1pt, black!80] (14.35,-0.2) -- (14.35,11.6);
\draw[dashed, line width=1.1pt, black!80] (0.0,6.95) -- (14.2,6.95);

% ================= (a) 训练流水线 =================
% 四帧
\foreach \i/\x/\op in {0/0.15/0.42, 1/2.35/0.62, 2/4.55/0.80, 3/6.75/0.96}{
  \begin{scope}[shift={(\x,9.25)}]
    \fill[cyan!55!black, opacity=\op] (0,0) rectangle (1.55,1.55);
    \foreach \k in {0,...,7}{
      \fill[white, opacity=.10] (\k*0.22,0) rectangle ++(0.15,1.55);
    }
    \draw[black!35, line width=.4pt] (0,0) rectangle (1.55,1.55);
  \end{scope}
  \node[font=\scriptsize, below=1.5pt] at (\x+0.78, 9.22)
    {$Block^{\i}_{\theta^{0.\i}}$};
}
% 上方弧线
\foreach \i/\j in {0/1, 0/2, 0/3, 1/2, 1/3, 2/3}{
  \draw[arr, draw=teal!70!black, line width=.7pt]
    (\i*2.2+0.93, 10.90) to[bend left=18] (\j*2.2+0.93, 10.90);
}
% 右侧因果线性注意力小格
\begin{scope}[shift={(9.65,9.30)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r>\c ? 0 : 2}
      \ifnum\pgfmathresult=0
        \fill[black!16] (\c*0.42,-\r*0.42) rectangle ++(0.40,0.40);
      \else
        \fill[green!72!black] (\c*0.42,-\r*0.42) rectangle ++(0.40,0.40);
      \fi
    }
  }
  \draw[black!55, line width=.4pt] (0,0.42) rectangle (1.70,-1.28);
  \node[lab2] at (-0.16,0.55) {$d$};
  \node[lab2] at (0.78,0.55) {$d$};
  \node[lab2, anchor=west] at (1.78,-0.22) {$\sum_{i=1}^{k}K_iV_i$};
  \node[font=\tiny, anchor=west] at (1.78,-1.10) {Cumulative Sum};
\end{scope}
\node[lab2, anchor=west] at (11.62,10.35) {Causal Linear Attention};
\node[ttl] at (7.5,7.55) {(a). Block-wise autoregressive training pipeline};

% ================= (b) 整体架构 =================
% 输入
\begin{scope}[shift={(0.35,3.05)}]
  \foreach \k in {0,...,3}{
    \fill[cyan!50!black, opacity=0.75] (\k*0.10, \k*0.10) rectangle ++(0.95,1.05);
  }
  \draw[black!35] (0,0) rectangle (1.25,1.30);
\end{scope}
\node[font=\scriptsize] at (0.95,2.72) {$[1\!+\!T, H, W, 3]$};

% AutoEncoder（平行四边形）
\node[draw=black!25, fill=black!6, inner sep=3pt, minimum width=2.5cm, minimum height=1.5cm,
      font=\scriptsize, trapezium, trapezium left angle=74, trapezium right angle=106,
      trapezium stretches=true] (ae) at (3.05,3.75) {AutoEncoder};
\draw[arr] (1.30,3.75) -- (ae.west);

% N x 大框
\fill[fxblue, opacity=.55, rounded corners=6pt] (4.55,2.55) rectangle (11.35,5.55);
\node[font=\scriptsize\bfseries, text=red!70!black, anchor=south west] at (4.62,2.58) {$\mathbf{N\times}$};

\node[font=\scriptsize, rotate=90, align=center] (la) at (5.30,4.05) {Linear Attn};
\node[font=\scriptsize, rotate=90, align=center] (ca) at (7.35,4.05) {Cross Attn};
\node[font=\scriptsize, rotate=90, align=center] (ff) at (9.55,4.05) {Mix FFN};
\fill[fxpnk, opacity=.75, rounded corners=2pt] (6.75,2.75) rectangle (7.95,5.35);
\fill[fxgrn, opacity=.55, rounded corners=2pt] (8.95,2.75) rectangle (10.15,5.35);

\draw[arr] (ae.east) -- (4.62,3.75);
\draw[arr] (5.85,3.75) -- (6.40,3.75);
\draw[arr] (8.05,3.75) -- (8.60,3.75);
\draw[arr] (10.30,3.75) -- (11.42,3.75);
\node[circle, draw=black!65, fill=white, inner sep=1.3pt, font=\scriptsize] (plus) at (11.62,3.75) {$+$};
\draw[arr] (plus) -- ++(0.55,0);

% 图标位（雪花 / 火焰）
\node[font=\scriptsize, text=cyan!70!black] at (4.95,5.30) {$\ast$};
\node[font=\scriptsize, text=red!75!black] at (11.05,5.30) {$\blacktriangle$};

% 文本分支
\node[draw=black!45, rounded corners=2pt, fill=white, minimum width=3.1cm,
      minimum height=0.78cm, font=\tiny, align=left, inner sep=2pt] (capbox)
  at (1.85,1.20) {\textit{A cyberpunk cat with a}\\\textit{sian that says "SANA"}};
\node[pnk2, minimum width=1.55cm] (rw) at (4.35,1.20) {Rewriter};
\node[pnk2, minimum width=1.75cm] (llm) at (6.45,1.20) {Small LLM};
\node[pnk2, minimum width=1.35cm] (te) at (8.55,1.20) {Time Emb};
\draw[arr] (capbox.east) -- (rw.west);
\draw[arr] (rw.east) -- (llm.west);
\draw[arr] (llm.east) -- (te.west);
\draw[arr] (llm.north) |- (7.35,2.55);
\node[ttl] at (7.0,0.28) {(b). Architecture overview of our SANA-Video.};

% ================= (c) Linear DiT module =================
% ---- 面板标题（在框上方）
\node[ttl] at (18.0,10.95) {Linear Attention};
\node[ttl] at (23.6,10.95) {Mix-FFN};

% ---- Linear Attention 面板
\fill[fxblue, opacity=.55, rounded corners=8pt] (14.85,0.55) rectangle (21.15,10.55);

\node[lin, minimum width=1.55cm] (sc) at (18.0,9.55) {Scale};
\node[lin, minimum width=2.0cm] (mm1) at (18.0,8.55) {MatMul};
\node[lin, minimum width=2.0cm] (mm0) at (19.20,7.35) {MatMul};

\node[org, minimum width=1.55cm] (ropeL) at (16.35,6.05) {3D RoPE};
\node[org, minimum width=1.55cm] (ropeR) at (19.55,6.05) {3D RoPE};
\node[lin, minimum width=1.55cm] (rl) at (16.35,5.10) {ReLU};
\node[lin, minimum width=1.55cm] (rr) at (19.55,5.10) {ReLU};
\node[lin, minimum width=1.55cm] (lnQ) at (16.35,3.95) {Linear};
\node[lin, minimum width=1.55cm] (lnK) at (18.10,3.95) {Linear};
\node[lin, minimum width=1.55cm] (lnV) at (19.85,3.95) {Linear};

\node[font=\scriptsize] at (16.35,3.25) {$Q$};
\node[font=\scriptsize] at (18.10,3.25) {$K$};
\node[font=\scriptsize] at (19.85,3.25) {$V$};

\draw[arr] (lnQ) -- (rl);
\draw[arr] (rl) -- (ropeL);
\draw[arr] (lnK) -- (rr);
\draw[arr] (rr) -- (ropeR);
\draw[arr] (ropeL.north) |- (17.85,7.45);
\draw[arr] (ropeR.north) -- (19.55,7.35) -- (20.20,7.35);
\draw[arr] (lnV.north) -- (19.85,6.95) -- (20.28,6.95);
\draw[arr] (mm0.north) -- (18.85,8.05) -- (18.55,8.05);
\draw[arr] (mm1) -- (sc);
\draw[arr] (sc.north) -- (18.0,10.05);

\node[lab2] at (17.05,8.90) {$n\times d$};
\node[lab2] at (18.75,7.95) {$n\times d$};
\node[lab2] at (17.55,7.05) {$d\times n$};
\node[lab2] at (20.15,6.95) {$n\times d$};

\node[lab2, anchor=east] at (20.95,2.10) {Cost: $\mathcal{O}(n)$};

% ---- Mix-FFN 面板
\fill[fxblue, opacity=.55, rounded corners=8pt] (21.55,0.55) rectangle (25.75,10.55);

\node[org, minimum width=2.55cm, minimum height=0.95cm, align=center] (tmp) at (23.65,9.00)
  {Temporal\\$3\times1\times1$ ConvLayer};
\node[lin, minimum width=2.55cm] (c1a) at (23.65,7.75) {$1\times1$ ConvLayer};
\node[lin, minimum width=2.55cm] (c2) at (23.65,5.55) {$1\times3\times3$ ConvLayer};
\node[lin, minimum width=2.55cm] (c3) at (23.65,3.35) {$1\times1$ ConvLayer};
\node[circle, draw=black!65, fill=white, inner sep=1.6pt, font=\scriptsize] (mul) at (23.05,6.60) {$\otimes$};
\node[pnk2, minimum width=1.05cm] (silu) at (24.75,6.60) {SiLU};

\draw[arr] (c3) -- (c2);
\draw[arr] (c2.north) -- (22.55,6.60) -- (22.88,6.60);
\draw[arr] (silu.west) -- (mul.east);
\draw[arr] (mul.north) -- (23.05,7.35) -- (23.35,7.35);
\draw[arr] (c1a) -- (tmp);
\draw[arr] (tmp.north) -- (23.65,9.90);
\node[ttl] at (23.65,-0.05) {(c). Linear DiT module};
\end{tikzpicture}
"""

def fig06() -> str:
    return r"""
\begin{tikzpicture}[x=1cm, y=0.66cm]
\tikzset{
  cell/.style={draw=black!55, line width=.35pt, inner sep=0pt},
  tok/.style={cell, fill=white},
  mask/.style={cell, fill=black!26},
  kv/.style={cell, fill=red!58!black},
  cmp/.style={cell, fill=green!68!black},
  ttl/.style={font=\scriptsize, align=center},
  arr2/.style={-{Stealth[length=1.7mm,width=1.2mm]}, line width=.75pt, draw=black!85},
  brc/.style={decorate, decoration={brace, amplitude=4pt}, black!65},
}

% ================= 图例 =================
\begin{scope}[shift={(1.15,8.55)}, every node/.style={font=\scriptsize}]
  \draw[cell, fill=white, minimum size=0.42cm] (0,0) rectangle (0.42,0.42);
  \node[anchor=west] at (0.52,0.21) {Token};
  \draw[cell, fill=black!26] (2.30,0) rectangle (2.72,0.42);
  \node[anchor=west] at (2.82,0.21) {Mask};
  \draw[cell, fill=red!58!black] (4.35,0) rectangle (4.77,0.42);
  \node[anchor=west] at (4.87,0.21) {KV Cache};
  \draw[cell, fill=green!68!black] (6.70,0) rectangle (7.12,0.42);
  \node[anchor=west] at (7.22,0.21) {Compute};
\end{scope}
\node[font=\small] at (4.35,7.80) {(a) Block Causal Linear Attention};

% ================= (a-1) Vanilla Attention =================
\begin{scope}[shift={(1.55,4.05)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \draw[cmp] (\c*0.52,-\r*0.52) rectangle ++(0.52,0.52);
    }
  }
  \node[ttl, anchor=north] at (1.30,-2.75) {Vanilla Attention};
  \node[ttl, anchor=east] at (-0.14,-0.26) {$Q_1$};
  \node[ttl, anchor=east] at (-0.14,-2.34) {$Q_N$};
  \node[ttl, anchor=south] at (0.26,0.10) {$K_1$};
  \node[ttl, anchor=south] at (2.34,0.10) {$K_N$};
  \node[ttl] at (1.04,0.32) {$\cdots$};
\end{scope}

\node[font=\normalsize] at (4.55,2.80) {$\times$};

% ================= (a-2) Linear Attention =================
\begin{scope}[shift={(5.20,4.05)}]
  % V 列（N×d）
  \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*0.52) rectangle ++(0.52,0.52); }
  \node[ttl, anchor=east] at (-0.14,-0.26) {$V_1$};
  \node[ttl, anchor=east] at (-0.14,-2.34) {$V_N$};
  \node[ttl, anchor=south] at (0.26,0.10) {$d$};
  \node[ttl, anchor=west] at (-0.62,-1.30) {$N$};

  \node[font=\normalsize] at (0.92,-0.62) {$\times$};

  % Q 列（N×d）
  \begin{scope}[shift={(1.42,0)}]
    \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*0.52) rectangle ++(0.52,0.52); }
    \node[ttl, anchor=east] at (-0.14,-0.26) {$Q_1$};
    \node[ttl, anchor=east] at (-0.14,-2.34) {$Q_N$};
    \node[ttl, anchor=south] at (0.26,0.10) {$d$};
    \draw[brc] (-0.42,0.04) -- (-0.42,-1.28) node[midway, left=3.5pt, font=\tiny] {Block$_1$};
    \draw[brc] (-0.42,-1.36) -- (-0.42,-2.60) node[midway, left=3.5pt, font=\tiny] {Block$_N$};
  \end{scope}

  \node[font=\normalsize] at (2.80,-0.62) {$\times$};

  % 结果小方块
  \begin{scope}[shift={(3.02,0)}]
    \draw[cmp] (0,-1.16) rectangle (0.88,-0.28);
    \node[font=\small] at (0.44,-0.72) {$\sum$};
    \node[ttl, anchor=south] at (0.44,-0.20) {$d$};
    \node[ttl, anchor=east] at (-0.14,-0.72) {$d$};
  \end{scope}

  \node[ttl, anchor=north] at (1.10,-2.82) {Linear Attention};
\end{scope}

% ================= (a-3) Causal Linear Attention =================
\begin{scope}[shift={(11.60,4.05)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \pgfmathparse{\r<\c ? 0 : 1}
      \ifnum\pgfmathresult=0
        \draw[mask] (\c*0.52,-\r*0.52) rectangle ++(0.52,0.52);
      \else
        \draw[cmp] (\c*0.52,-\r*0.52) rectangle ++(0.52,0.52);
      \fi
    }
  }
  % 第 3、4 行的左段标成 KV Cache（红），模仿累积复用的部分
  \foreach \c in {0,1,2}{
    \draw[kv] (\c*0.52,-1.56) rectangle ++(0.52,0.52);
    \draw[kv] (\c*0.52,-2.08) rectangle ++(0.52,0.52);
  }
  \node[ttl, anchor=south] at (1.30,0.10) {$d$};
  \node[ttl, anchor=east] at (-0.14,-0.26) {$Q_1$};
  \node[ttl, anchor=east] at (-0.14,-2.34) {$Q_N$};
  \draw[brc] (-0.42,0.04) -- (-0.42,-1.28) node[midway, left=3.5pt, font=\tiny] {Block$_1$};
  \draw[brc] (-0.42,-1.36) -- (-0.42,-2.60) node[midway, left=3.5pt, font=\tiny] {Block$_N$};

  % 累积求和箭头
  \draw[arr2] (-0.02,-1.30) -- (1.32,-1.30);
  \node[font=\tiny, anchor=west] at (1.38,-1.30) {$\sum_{i=1}^{2}K_iV_i$};
  \draw[arr2] (-0.02,-1.82) -- (1.32,-1.82);
  \node[font=\tiny, anchor=west] at (1.38,-1.82) {$\sum_{i=1}^{3}K_iV_i$};
  \draw[arr2, draw=black!85] (-0.02,-2.62) -- (1.60,-2.62);
  \node[font=\tiny, anchor=west] at (1.66,-2.62) {Cumulative Sum};

  \node[ttl, anchor=north] at (1.30,-2.82) {Causal Linear Attention};
\end{scope}

% ================= (b) Block Causal Mix-FFN =================
\begin{scope}[shift={(17.35,4.30)}]
  \node[ttl] at (1.35,3.95) {$\vdots$};

  \foreach \i/\name/\fc/\tc in {
      0/{Token-2}/fxgrn/black,
      1/{Token-1}/fxgrn/black,
      2/{Zero Padding}/fxbluepad/white,
      3/{Cached Token-1}/fxkv/white,
      4/{Token$_0$}/fxgrn/black,
      5/{Token$_1$}/fxgrn/black}{
    \pgfmathsetmacro{\yy}{2.35-\i*0.62}
    \node[draw=black!55, line width=.4pt, rounded corners=2pt, fill=\fc,
          minimum width=2.15cm, minimum height=0.54cm, font=\tiny, text=\tc]
      at (1.35,\yy) {\name};
  }
  \node[ttl] at (1.35,-1.70) {$\vdots$};

  % 蓝色复用弧线
  \draw[arr2, draw=blue!75, line width=1.1pt]
    (2.62,1.11) to[bend left=42] (2.62,0.49);

  \draw[brc] (2.92,2.66) -- (2.92,1.42) node[midway, right=4pt, font=\tiny] {Block$_1$};
  \draw[brc] (2.92,1.18) -- (2.92,-1.28) node[midway, right=4pt, font=\tiny] {Block$_2$};
\end{scope}
\node[font=\small] at (18.70,-0.55) {(b) Block Causal Mix-FFN};
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
