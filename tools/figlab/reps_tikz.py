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
\begin{tikzpicture}[x=1cm, y=0.92cm,
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
\draw[dashed, line width=1.1pt, black!80] (14.55,-0.2) -- (14.55,11.6);
\draw[dashed, line width=1.1pt, black!80] (0.0,6.95) -- (14.40,6.95);

% ================= (a) 训练流水线 =================
% 四帧
\foreach \i/\x/\op in {0/0.05/0.45, 1/2.85/0.66, 2/5.65/0.84, 3/8.45/0.98}{
  \begin{scope}[shift={(\x,9.25)}]
    \clip[rounded corners=3pt] (0,0) rectangle (2.05,2.05);
    \node[anchor=south west, inner sep=0pt] at (0,0)
      {\includegraphics[width=2.05cm,height=2.05cm]{frame\i.png}};
  \end{scope}
  \draw[black!50, line width=.5pt, rounded corners=3pt] (\x,9.25) rectangle (\x+2.05,11.30);
  \node[font=\scriptsize, text=red!60!white, opacity=0.9] at (\x+0.78, 10.55) {SANA};
  \node[font=\scriptsize, below=2pt] at (\x+1.02, 9.18)
    {$Block^{\i}_{\theta^{0.\i}}$};
}
% 上方弧线
\foreach \i/\j in {0/1, 0/2, 0/3, 1/2, 1/3, 2/3}{
  \draw[arr, draw=teal!70!black, line width=.7pt]
    (\i*2.8+1.02, 11.35) to[bend left=16] (\j*2.8+1.02, 11.35);
}
% 右侧因果线性注意力小格
\begin{scope}[shift={(11.55,9.85)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r>\c ? 0 : 2}
      \ifnum\pgfmathresult=0
        \fill[black!16] (\c*0.36,-\r*0.36) rectangle ++(0.34,0.34);
      \else
        \fill[green!72!black] (\c*0.36,-\r*0.36) rectangle ++(0.34,0.34);
      \fi
    }
  }
  \draw[black!55, line width=.4pt] (0,0.36) rectangle (1.44,-1.10);
  \node[lab2] at (-0.14,0.48) {$d$};
  \node[lab2] at (0.66,0.48) {$d$};
  \node[lab2, anchor=west] at (1.46,-0.20) {$\sum_{i=1}^{k}K_iV_i$};
  \node[font=\tiny, anchor=west] at (1.46,-1.30) {Cumulative Sum};
\end{scope}
\node[lab2, anchor=south] at (12.27,11.22) {Causal Linear Attention};
\node[ttl] at (7.5,7.55) {(a). Block-wise autoregressive training pipeline};

% ================= (b) 整体架构 =================
% 输入（叠层图像）
\begin{scope}[shift={(0.30,3.00)}]
  \foreach \k in {0,...,3}{
    \begin{scope}[shift={(\k*0.09,\k*0.09)}]
      \clip (0,0) rectangle (1.10,1.22);
      \node[anchor=south west, inner sep=0pt] at (0,0)
        {\includegraphics[width=1.10cm,height=1.22cm]{input.png}};
    \end{scope}
    \draw[black!45, line width=.4pt] (\k*0.09,\k*0.09) rectangle ++(1.10,1.22);
  }
\end{scope}
\node[font=\scriptsize] at (1.00,2.70) {$[1\!+\!T, H, W, 3]$};

% AutoEncoder（平行四边形）
\begin{scope}[shift={(3.60,2.95)}]
  \fill[black!7] (0.32,0) -- (2.85,0) -- (2.52,1.62) -- (0,1.62) -- cycle;
  \draw[black!25, line width=.5pt] (0.32,0) -- (2.85,0) -- (2.52,1.62) -- (0,1.62) -- cycle;
  \node[font=\scriptsize] (ae) at (1.45,0.81) {AutoEncoder};
\end{scope}
\draw[arr] (1.42,3.76) -- (ae.west);

% N x 大框（按原图像素比例：27.9%–49.1% 宽度）
\fill[fxblue, opacity=.55, rounded corners=7pt] (7.35,2.45) rectangle (13.05,5.60);
\node[font=\scriptsize\bfseries, text=red!70!black, anchor=south west] at (7.44,2.50) {$\mathbf{N\times}$};

% 三列：Linear Attn / Cross Attn / Mix FFN
\node[font=\scriptsize, rotate=90, align=center] at (8.30,4.05) {Linear Attn};
\node[font=\scriptsize, rotate=90, align=center] at (10.15,4.05) {Cross Attn};
\node[font=\scriptsize, rotate=90, align=center] at (12.05,4.05) {Mix FFN};
\fill[fxpnk, opacity=.72, rounded corners=3pt] (9.55,2.58) rectangle (10.75,5.47);
\fill[fxgrn, opacity=.55, rounded corners=3pt] (11.55,2.58) rectangle (12.55,5.47);

\draw[arr] (ae.east) -- (7.44,3.76);
\draw[arr] (8.85,3.76) -- (9.45,3.76);
\draw[arr] (10.85,3.76) -- (11.45,3.76);
\draw[arr] (12.65,3.76) -- (13.18,3.76);
\node[circle, draw=black!65, fill=white, inner sep=1.4pt, font=\scriptsize] (plus) at (13.42,3.76) {$+$};
\draw[arr] (plus) -- ++(0.62,0);

% 图标：雪花（左）/ 火焰（右）
\node[font=\small, text=cyan!60!black] at (7.75,5.22) {$\ast$};
\node[font=\scriptsize, text=cyan!60!black] at (7.75,4.94) {$\ast$};
\node[font=\small, text=orange!90!black] at (12.75,5.22) {$\blacktriangle$};

% 文本分支
\node[draw=black!45, rounded corners=2pt, fill=white, minimum width=3.3cm,
      minimum height=0.80cm, font=\tiny, align=left, inner sep=2pt] (capbox)
  at (1.75,1.05) {\textit{A cyberpunk cat with a}\\\textit{sian that says "SANA"}};
\node[pnk2, minimum width=1.75cm] (rw) at (4.70,1.05) {Rewriter};
\node[pnk2, minimum width=1.95cm] (llm) at (7.05,1.05) {Small LLM};
\node[pnk2, minimum width=1.60cm] (te) at (9.40,1.05) {Time Emb};
\draw[arr] (capbox.east) -- (rw.west);
\draw[arr] (rw.east) -- (llm.west);
\draw[arr] (llm.east) -- (te.west);
\draw[arr] (llm.north) |- (10.15,2.45);
\node[ttl] at (7.35,0.05) {(b). Architecture overview of our SANA-Video.};

% ================= (c) Linear DiT module =================
% ---- 面板标题（在框上方）
\node[font=\large\bfseries] at (18.0,10.95) {Linear Attention};
\node[font=\large\bfseries] at (23.6,10.95) {Mix-FFN};

% ---- Linear Attention 面板
\fill[fxblue, opacity=.55, rounded corners=8pt] (14.85,0.55) rectangle (21.15,10.55);

\node[lin, minimum width=1.55cm] (sc) at (18.0,9.55) {Scale};
\node[lin, minimum width=2.0cm] (mm1) at (18.0,8.55) {MatMul};
\node[lin, minimum width=2.0cm] (mm0) at (18.75,7.20) {MatMul};

\node[org, minimum width=1.55cm] (ropeL) at (16.30,5.95) {3D RoPE};
\node[org, minimum width=1.55cm] (ropeR) at (20.15,5.95) {3D RoPE};
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
\draw[arr] (ropeL.north) |- (17.72,6.85);
\draw[arr] (ropeR.north) -- (20.15,6.85) -- (19.80,6.85);
\draw[arr] (lnV.north) -- (19.85,6.55) -- (20.90,6.55) -- (20.90,7.35) -- (20.05,7.35);
\draw[arr] (mm0.north) -- (18.75,8.05);
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
\begin{tikzpicture}[x=1cm, y=0.685cm]
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
\begin{scope}[shift={(1.15,7.35)}, every node/.style={font=\scriptsize}]
  \draw[cell, fill=white, minimum size=0.42cm] (0,0) rectangle (0.42,0.42);
  \node[anchor=west] at (0.52,0.21) {Token};
  \draw[cell, fill=black!26] (2.30,0) rectangle (2.72,0.42);
  \node[anchor=west] at (2.82,0.21) {Mask};
  \draw[cell, fill=red!58!black] (4.35,0) rectangle (4.77,0.42);
  \node[anchor=west] at (4.87,0.21) {KV Cache};
  \draw[cell, fill=green!68!black] (6.70,0) rectangle (7.12,0.42);
  \node[anchor=west] at (7.22,0.21) {Compute};
\end{scope}
\node[font=\small] at (4.35,6.45) {(a) Block Causal Linear Attention};

% ================= (a-1) Vanilla Attention =================
\begin{scope}[shift={(1.55,4.05)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \draw[cmp] (\c*0.62,-\r*0.62) rectangle ++(0.72,0.72);
    }
  }
  \node[ttl, anchor=north] at (2.00,-3.55) {Vanilla Attention};
  \node[ttl, anchor=east] at (-0.14,-0.36) {$Q_1$};
  \node[ttl, anchor=east] at (-0.14,-2.95) {$Q_N$};
  \node[ttl, anchor=south] at (0.26,0.10) {$K_1$};
  \node[ttl, anchor=south] at (2.34,0.10) {$K_N$};
  \node[ttl] at (1.20,0.34) {$\cdots$};
\end{scope}

\node[font=\normalsize] at (4.55,2.80) {$\times$};

% ================= (a-2) Linear Attention =================
\begin{scope}[shift={(5.85,4.05)}]
  % V 列（N×d），格 0.72、行距 0.72，5 行 → 高 3.60
  \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*0.72) rectangle ++(0.72,0.72); }
  \node[ttl, anchor=east] at (-0.12,-0.36) {$V_1$};
  \node[ttl, anchor=east] at (-0.12,-3.24) {$V_N$};
  \node[ttl, anchor=south] at (0.36,0.10) {$d$};
  \node[ttl, anchor=west] at (0.86,-1.90) {$N$};

  \node[font=\normalsize] at (1.48,0.24) {$\times$};

  % Q 列（N×d）
  \begin{scope}[shift={(2.05,0)}]
    \foreach \r in {0,...,4}{ \draw[tok] (0,-\r*0.72) rectangle ++(0.72,0.72); }
    \node[ttl, anchor=east] at (-0.14,-0.36) {$Q_1$};
    \node[ttl, anchor=east] at (-0.14,-3.24) {$Q_N$};
    \node[ttl, anchor=south] at (0.36,0.10) {$d$};
    \draw[brc] (-0.44,0.04) -- (-0.44,-1.76) node[midway, left=5pt, font=\tiny] {Block$_1$};
    \draw[brc] (-0.44,-1.84) -- (-0.44,-3.64) node[midway, left=5pt, font=\tiny] {Block$_N$};
  \end{scope}

  \node[font=\normalsize] at (3.72,0.24) {$\times$};

  % 结果小方块（d×d）
  \begin{scope}[shift={(4.15,-1.50)}]
    \draw[cmp] (0,0) rectangle (0.72,0.72);
    \node[font=\scriptsize] at (0.36,0.36) {$\sum$};
    \node[ttl, anchor=south] at (0.36,0.80) {$d$};
    \node[ttl, anchor=east] at (-0.12,0.36) {$d$};
  \end{scope}

  \node[ttl, anchor=north] at (2.35,-3.95) {Linear Attention};
\end{scope}

% ================= (a-3) Causal Linear Attention =================
\begin{scope}[shift={(12.15,4.05)}]
  \foreach \r in {0,...,4}{
    \foreach \c in {0,...,4}{
      \pgfmathparse{\r<\c ? 0 : 1}
      \ifnum\pgfmathresult=0
        \draw[mask] (\c*0.62,-\r*0.62) rectangle ++(0.72,0.72);
      \else
        \draw[cmp] (\c*0.62,-\r*0.62) rectangle ++(0.72,0.72);
      \fi
    }
  }
  % 第 3、4 行的左段标成 KV Cache（红），模仿累积复用的部分
  \foreach \c in {0,1,2}{
    \draw[kv] (\c*0.62,-1.86) rectangle ++(0.72,0.72);
    \draw[kv] (\c*0.62,-2.48) rectangle ++(0.72,0.72);
  }
  \node[ttl, anchor=south] at (1.44,0.10) {$d$};
  \node[ttl, anchor=east] at (-0.14,-0.36) {$Q_1$};
  \node[ttl, anchor=east] at (-0.14,-2.95) {$Q_N$};
  \draw[brc] (-0.42,0.04) -- (-0.42,-1.28) node[midway, left=3.5pt, font=\tiny] {Block$_1$};
  \draw[brc] (-0.42,-1.36) -- (-0.42,-2.60) node[midway, left=3.5pt, font=\tiny] {Block$_N$};

  % 累积求和箭头
  \draw[arr2] (-0.02,-1.30) -- (1.32,-1.30);
  \node[font=\tiny, anchor=west] at (1.38,-1.30) {$\sum_{i=1}^{2}K_iV_i$};
  \draw[arr2] (-0.02,-1.82) -- (1.32,-1.82);
  \node[font=\tiny, anchor=west] at (1.38,-1.82) {$\sum_{i=1}^{3}K_iV_i$};
  \draw[arr2, draw=black!85] (-0.02,-2.62) -- (1.60,-2.62);
  \node[font=\tiny, anchor=west] at (1.66,-2.62) {Cumulative Sum};

  \node[ttl, anchor=north] at (1.85,-3.60) {Causal Linear Attention};
\end{scope}

% ================= (b) Block Causal Mix-FFN =================
\begin{scope}[shift={(16.30,3.20)}]
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
\node[font=\small] at (17.65,-0.95) {(b) Block Causal Mix-FFN};
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
