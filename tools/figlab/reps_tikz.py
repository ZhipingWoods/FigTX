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
\begin{tikzpicture}[x=1cm, y=0.885cm,
  box/.style={draw=black!90, line width=1.1pt, rounded corners=4pt, align=center,
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
\foreach \i/\x in {0/0.10, 1/2.60, 2/5.10}{
  \begin{scope}[shift={(\x,9.55)}]
    \foreach \k in {3,2,1,0}{
      \begin{scope}[shift={(\k*0.12,\k*0.12)}]
        \clip[rounded corners=3pt] (0,0) rectangle (1.60,1.60);
        \node[anchor=south west, inner sep=0pt] at (0,0)
          {\includegraphics[width=1.60cm,height=1.60cm]{frame\i.png}};
      \end{scope}
      \draw[black!50, line width=.7pt, rounded corners=3pt]
        (\k*0.12,\k*0.12) rectangle ++(1.60,1.60);
    }
  \end{scope}
}
% 第四组：灰色叠层
\begin{scope}[shift={(7.60,9.55)}]
  \foreach \k in {3,2,1,0}{
    \fill[black!30, rounded corners=3pt] (\k*0.12,\k*0.12) rectangle ++(1.60,1.60);
    \draw[black!50, line width=.7pt, rounded corners=3pt] (\k*0.12,\k*0.12) rectangle ++(1.60,1.60);
  }
\end{scope}

% 块标签
\node[font=\footnotesize] at (1.05,9.25) {$Block^0_{t=0}$};
\node[font=\footnotesize] at (3.55,9.25) {$Block^1_{t=0.2}$};
\node[font=\footnotesize] at (6.05,9.25) {$Block^2_{t=0.7}$};
\node[font=\footnotesize] at (8.55,9.25) {$Block^3_{t=1}$};

% 上方跨块弧线
\foreach \i/\j/\bend in {0/1/28, 0/2/24, 0/3/20, 1/2/28, 1/3/24, 2/3/28}{
  \draw[arr, draw=teal!70!black, line width=1.0pt]
    (\i*2.50+1.90, 11.26) to[bend left=\bend] (\j*2.50+1.90, 11.26);
}

% 因果线性注意力小图（放在左半区右侧，x 10.3–13.6）
\begin{scope}[shift={(10.55,9.75)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r>\c ? 0 : 2}
      \ifnum\pgfmathresult=0
        \fill[black!18] (\c*0.46,-\r*0.46) rectangle ++(0.44,0.44);
      \else
        \fill[green!72!black] (\c*0.46,-\r*0.46) rectangle ++(0.44,0.44);
      \fi
    }
  }
  \draw[black!65, line width=.7pt] (0,0.46) rectangle (1.86,-1.40);
  \node[font=\scriptsize] at (-0.18,0.58) {$d$};
  \node[font=\scriptsize] at (0.86,0.58) {$d$};
  \node[font=\scriptsize, anchor=west] at (1.96,0.10) {$\sum_{i=1}^{k}K_iV_i$};
  \node[font=\tiny, anchor=north west] at (1.96,-0.30) {Cumulative Sum};
\end{scope}
\node[font=\scriptsize, anchor=south] at (11.50,11.72) {Causal Linear Attention};

\node[font=\large\bfseries] at (6.30,8.30) {(a). Block-wise autoregressive training pipeline};

% ================= (b) 整体架构 =================
% 输入：叠层帧
\begin{scope}[shift={(0.25,2.25)}]
  \foreach \k in {3,2,1,0}{
    \begin{scope}[shift={(\k*0.12,\k*0.12)}]
      \clip[rounded corners=2pt] (0,0) rectangle (1.55,1.55);
      \node[anchor=south west, inner sep=0pt] at (0,0)
        {\includegraphics[width=1.55cm,height=1.55cm]{input.png}};
      \draw[black!50, line width=.6pt, rounded corners=2pt] (0,0) rectangle (1.55,1.55);
    \end{scope}
  }
\end{scope}
\node[font=\footnotesize] at (1.10,1.92) {$[1\!+\!T, H, W, 3]$};

% AutoEncoder：左窄右宽梯形
\begin{scope}[shift={(4.55,2.10)}]
  \fill[fxblue2] (0.00,0.55) -- (0.55,0.00) -- (2.85,0.00) -- (2.30,0.55) -- (2.30,1.55) -- (2.85,2.10) -- (0.55,2.10) -- (0.00,1.55) -- cycle;
  \draw[black!55, line width=.9pt] (0.00,0.55) -- (0.55,0.00) -- (2.85,0.00) -- (2.30,0.55) -- (2.30,1.55) -- (2.85,2.10) -- (0.55,2.10) -- (0.00,1.55) -- cycle;
  \node[font=\footnotesize] at (1.45,1.05) {AutoEncoder};
\end{scope}
\draw[arr, line width=1.0pt] (1.75,2.90) -- (4.55,2.90);

% N x 大框（含内部 ⊕）
\fill[fxblue, opacity=.60, rounded corners=10pt] (7.60,1.95) rectangle (14.30,4.05);
\node[font=\footnotesize\bfseries, text=red!70!black, anchor=north west] at (7.70,4.00) {$\mathbf{N\times}$};

% 三列背景带
\fill[fxpnk, opacity=.70, rounded corners=4pt] (10.05,2.05) rectangle (11.35,3.95);
\fill[fxgrn, opacity=.55, rounded corners=4pt] (12.05,2.05) rectangle (13.05,3.95);

\node[font=\footnotesize, rotate=90] at (8.85,3.00) {Linear Attn};
\node[font=\footnotesize, rotate=90] at (10.70,3.00) {Cross Attn};
\node[font=\footnotesize, rotate=90] at (12.55,3.00) {Mix FFN};
\node[circle, draw=black!85, fill=white, inner sep=1.8pt, font=\footnotesize] (plus) at (13.75,3.00) {$+$};

\draw[arr, line width=1.0pt] (7.42,2.90) -- (8.30,2.90);
\draw[arr, line width=1.0pt] (9.25,2.90) -- (9.95,2.90);
\draw[arr, line width=1.0pt] (11.45,2.90) -- (11.95,2.90);
\draw[arr, line width=1.0pt] (13.15,2.90) -- (plus);
\draw[arr, line width=1.0pt] (plus) -- (14.85,2.90);

% 彩色图标：雪花（左）/ 火焰（右）
\begin{scope}[shift={(7.85,4.55)}]
  \foreach \a in {0,60,120,180,240,300}{
    \draw[cyan!65!black, line width=1.1pt] (0,0) -- (\a:0.26);
  }
  \fill[cyan!65!black] (0,0) circle (0.045);
\end{scope}
\begin{scope}[shift={(13.95,4.55)}]
  \fill[orange!90!black] (0,-0.22) .. controls (-0.20,0.05) and (-0.10,0.18) .. (0,0.28)
                        .. controls (0.10,0.18) and (0.20,0.05) .. (0,-0.22) -- cycle;
  \fill[red!80!black] (0,-0.16) .. controls (-0.10,0.00) and (-0.05,0.08) .. (0,0.13)
                      .. controls (0.05,0.08) and (0.10,0.00) .. (0,-0.16) -- cycle;
\end{scope}

% 文本分支
\node[draw=black!75, line width=.9pt, rounded corners=5pt, fill=white, minimum width=3.4cm,
      minimum height=1.00cm, font=\scriptsize, align=left, inner sep=3pt] (capbox)
  at (1.95,0.62) {\textbf{\textit{A cyberpunk cat with a}}\\[1pt]\textbf{\textit{sian that says "SANA"}}};
\node[pnk2, line width=.9pt, minimum width=1.85cm, minimum height=0.90cm, font=\footnotesize] (rw) at (5.05,0.62) {Rewriter};
\node[pnk2, line width=.9pt, minimum width=2.15cm, minimum height=0.90cm, font=\footnotesize] (llm) at (7.60,0.62) {Small LLM};
\node[pnk2, line width=.9pt, minimum width=1.75cm, minimum height=0.90cm, font=\footnotesize] (te) at (10.10,0.62) {Time Emb};
\draw[arr, line width=1.0pt] (capbox.east) -- (rw.west);
\draw[arr, line width=1.0pt] (rw.east) -- (llm.west);
\draw[arr, line width=1.0pt] (llm.east) -- (te.west);
\draw[arr, line width=1.0pt] (llm.north) |- (10.70,1.95);
\draw[arr, line width=1.0pt] (te.north) -- (10.10,1.95);

\node[font=\large\bfseries] at (7.3,-0.55) {(b). Architecture overview of our SANA-Video.};

% 上/下分隔线
\draw[dashed, line width=1.2pt, black!80] (0.0,6.95) -- (14.45,6.95);

% ================= (c) Linear DiT module =================
% ---- 面板标题（在框上方）
\node[font=\large\bfseries] at (18.0,10.95) {Linear Attention};
\node[font=\large\bfseries] at (23.6,10.95) {Mix-FFN};

% ---- Linear Attention 面板（按原图比例放大：方块更大、圆角、粗边）
\fill[fxblue, opacity=.62, rounded corners=10pt] (14.85,0.30) rectangle (21.45,10.62);

\node[box, fill=white, minimum width=2.25cm, minimum height=1.10cm, font=\footnotesize] (sc) at (18.15,9.55) {Scale};
\node[box, fill=white, minimum width=2.80cm, minimum height=1.10cm, font=\footnotesize] (mm1) at (18.15,8.28) {MatMul};
\node[box, fill=white, minimum width=2.80cm, minimum height=1.10cm, font=\footnotesize] (mm0) at (19.00,6.80) {MatMul};

\node[box, fill=fxorg, draw=black!65, minimum width=2.15cm, minimum height=1.05cm, font=\footnotesize\bfseries] (ropeL) at (16.28,5.30) {3D RoPE};
\node[box, fill=fxorg, draw=black!65, minimum width=2.15cm, minimum height=1.05cm, font=\footnotesize\bfseries] (ropeR) at (20.08,5.30) {3D RoPE};
\node[box, fill=fxpnk, draw=black!55, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (rl) at (16.28,3.92) {ReLU};
\node[box, fill=fxpnk, draw=black!55, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (rr) at (20.08,3.92) {ReLU};
\node[box, fill=white, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (lnQ) at (16.28,2.55) {Linear};
\node[box, fill=white, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (lnK) at (18.18,2.55) {Linear};
\node[box, fill=white, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (lnV) at (20.08,2.55) {Linear};

\node[font=\footnotesize] at (16.28,1.80) {$Q$};
\node[font=\footnotesize] at (18.18,1.80) {$K$};
\node[font=\footnotesize] at (20.08,1.80) {$V$};

\draw[arr, line width=.8pt] (lnQ) -- (rl);
\draw[arr, line width=.8pt] (rl) -- (ropeL);
\draw[arr, line width=.8pt] (lnK) -- (rr);
\draw[arr, line width=.8pt] (rr) -- (ropeR);
\draw[arr, line width=.8pt] (ropeL.north) |- (17.60,6.80);
\draw[arr, line width=.8pt] (ropeR.north) -- (20.08,6.05) -- (20.40,6.05);
\draw[arr, line width=.8pt] (lnV.north) -- (20.08,1.70) -- (21.28,1.70) -- (21.28,6.30) -- (20.62,6.30);
\draw[arr, line width=.8pt] (mm0.north) -- (19.00,7.74);
\draw[arr, line width=.8pt] (mm1) -- (sc);
\draw[arr, line width=.8pt] (sc.north) -- (18.15,10.20);

\node[lab2, font=\scriptsize] at (17.05,9.02) {$n\times d$};
\node[lab2, font=\scriptsize] at (19.40,7.42) {$n\times d$};
\node[lab2, font=\scriptsize] at (17.28,6.28) {$d\times n$};
\node[lab2, font=\scriptsize] at (20.78,6.50) {$n\times d$};

\node[font=\footnotesize, anchor=east] at (21.30,1.05) {Cost: $\mathcal{O}(n)$};

% ---- Mix-FFN 面板
\fill[fxblue, opacity=.62, rounded corners=10pt] (21.80,0.30) rectangle (26.25,10.62);

\node[box, fill=fxorg, draw=black!65, minimum width=3.70cm, minimum height=1.30cm,
      font=\footnotesize\bfseries, align=center] (tmp) at (23.98,9.18)
  {Temporal\\$3\times1\times1$ ConvLayer};
\node[box, fill=fxgrn, draw=black!55, minimum width=3.70cm, minimum height=1.05cm, font=\footnotesize] (c1a) at (23.98,7.66) {$1\times1$ ConvLayer};
\node[box, fill=fxgrn, draw=black!55, minimum width=3.70cm, minimum height=1.05cm, font=\footnotesize] (c2) at (23.98,4.90) {$1\times3\times3$ ConvLayer};
\node[box, fill=fxgrn, draw=black!55, minimum width=3.70cm, minimum height=1.05cm, font=\footnotesize] (c3) at (23.98,2.55) {$1\times1$ ConvLayer};
\node[circle, draw=black!65, fill=white, inner sep=2.2pt, font=\footnotesize] (mul) at (23.35,6.22) {$\otimes$};
\node[box, fill=fxpnk, draw=black!55, minimum width=1.75cm, minimum height=0.95cm, font=\footnotesize] (silu) at (25.25,6.22) {SiLU};

\draw[arr, line width=.8pt] (c3) -- (c2);
\draw[arr, line width=.8pt] (c2.north) -- (22.55,6.22) -- (23.08,6.22);
\draw[arr, line width=.8pt] (silu.west) -- (mul.east);
\draw[arr, line width=.8pt] (mul.north) -- (23.35,7.16) -- (23.60,7.16);
\draw[arr, line width=.8pt] (c1a) -- (tmp);
\draw[arr, line width=.8pt] (tmp.north) -- (23.98,10.05);
\node[ttl] at (23.65,-0.05) {(c). Linear DiT module};
\end{tikzpicture}
"""

def fig06() -> str:
    return r"""
\begin{tikzpicture}[x=1cm, y=0.685cm]
\tikzset{
  cell/.style={draw=black!70, line width=.7pt, inner sep=0pt},
  tok/.style={cell, fill=white},
  mask/.style={cell, fill=black!26},
  kv/.style={cell, fill=red!58!black},
  cmp/.style={cell, fill=green!68!black},
  ttl/.style={font=\footnotesize, align=center},
  arr2/.style={-{Stealth[length=2.0mm,width=1.5mm]}, line width=1.0pt, draw=black!90},
  brc/.style={decorate, decoration={brace, amplitude=5pt}, black!75},
}

% ================= 图例 =================
\begin{scope}[shift={(1.15,7.35)}, every node/.style={font=\footnotesize}]
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
\begin{scope}[shift={(16.55,3.15)}]
  \node[ttl] at (1.35,3.95) {$\vdots$};

  \foreach \i/\name/\fc/\tc in {
      0/{Token-2}/fxgrn/black,
      1/{Token-1}/fxgrn/black,
      2/{Zero Padding}/fxbluepad/white,
      3/{Cached Token-1}/fxkv/white,
      4/{Token$_0$}/fxgrn/black,
      5/{Token$_1$}/fxgrn/black}{
    \pgfmathsetmacro{\yy}{2.35-\i*0.62}
    \node[draw=black!75, line width=.8pt, rounded corners=3pt, fill=\fc,
          minimum width=2.55cm, minimum height=0.64cm, font=\scriptsize, text=\tc]
      at (1.35,\yy) {\name};
  }
  \node[ttl] at (1.35,-1.70) {$\vdots$};

  % 蓝色复用弧线
  \draw[arr2, draw=blue!75, line width=1.1pt]
    (2.75,1.11) to[bend left=42] (2.75,0.49);

  \draw[brc] (3.02,2.66) -- (3.02,1.42) node[midway, right=4pt, font=\scriptsize] {Block$_1$};
  \draw[brc] (3.02,1.18) -- (3.02,-1.28) node[midway, right=4pt, font=\scriptsize] {Block$_2$};
\end{scope}
\node[font=\small] at (17.90,-1.05) {(b) Block Causal Mix-FFN};
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
