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
\begin{tikzpicture}[node distance=4mm]
% ============ (a) Block-wise autoregressive training pipeline ============
\node[lab, anchor=south west] at (-1.2, 3.75) {\textbf{(a)} Block-wise autoregressive training pipeline};

% 四帧图像条（用渐变色块示意）
\foreach \i/\x/\op in {0/0/0.35, 1/1.75/0.55, 2/3.5/0.78, 3/5.25/1.0}{
  \begin{scope}[shift={(\x,1.75)}]
    \foreach \k in {0,...,4}{
      \fill[blue!40!black, opacity=\op] (\k*0.16,0) rectangle ++(0.14,1.15);
    }
    \draw[black!40, line width=.4pt] (0,0) rectangle (0.78,1.15);
  \end{scope}
  \node[lab, below=1pt] at (\x+0.39,1.72) {$Block^{\i}_{\theta^{0.\i}}$};
}
% 上方弧线箭头
\foreach \i/\j in {0/1, 0/2, 0/3, 1/2, 1/3, 2/3}{
  \draw[arr, draw=teal!85!black, line width=.5pt]
    (\i*1.75+0.39, 3.02) to[bend left=17] (\j*1.75+0.39, 3.02);
}
\node[lab, anchor=west] at (0.1, 3.42) {recurrent sampling};

% 右侧：因果线性注意力小格
\begin{scope}[shift={(6.35,1.80)}]
  \node[lab, anchor=south] at (0.55,1.18) {Causal Linear Attention};
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r<\c ? 0 : (\r==\c ? 1 : 2)}
      \ifnum\pgfmathresult=0
        \fill[black!12] (\c*0.24,-\r*0.24) rectangle ++(0.23,0.23);
      \else
        \fill[green!70!black] (\c*0.24,-\r*0.24) rectangle ++(0.23,0.23);
      \fi
    }
  }
  \draw[black!50, line width=.4pt] (0,0.23) rectangle (0.96,-0.72);
  \node[lab, anchor=west] at (1.02,-0.24) {$\sum_{i=1}^{k}\!K_iV_i$};
\end{scope}

% ============ (b) 整体架构 ============
\begin{scope}[shift={(0,-1.55)}]
\node[lab, anchor=south west] at (-1.2, 2.15) {\textbf{(b)} Architecture overview of our SANA-Video};

% 图像输入
\foreach \k in {0,...,3}{
  \fill[blue!40!black, opacity=0.75] (-1.0+\k*0.10, 0.35+\k*0.10) rectangle ++(0.55,0.85);
}
\node[lab, anchor=north] at (-0.7, 0.28) {$[1\!+\!T, H, W, 3]$};

\node[blu2, right=6mm of {(0.05,0.75)}, minimum width=17mm, minimum height=13mm] (ae) {Auto\\Encoder};
\node[blu, right=5mm of ae, minimum width=13mm, minimum height=20mm] (lin) {Linear\\Attn};
\node[blu, right=3mm of lin, minimum width=12mm, minimum height=20mm] (cro) {Cross\\Attn};
\node[blu, right=3mm of cro, minimum width=12mm, minimum height=20mm] (ffn) {Mix\\FFN};
\node[circle, draw=black!55, fill=white, inner sep=1.2pt, font=\scriptsize] (plus) at ($(ffn.east)+(7mm,0)$) {$+$};

\draw[arr] (0.05,0.77) -- (ae);
\draw[arr] (ae) -- (lin);
\draw[arr] (lin) -- (cro);
\draw[arr] (cro) -- (ffn);
\draw[arr] (ffn) -- (plus);
\draw[arr] (plus) -- ++(7mm,0);

% N x 循环框
\draw[draw=black!55, dashed, rounded corners=2pt]
  ($(lin.north west)+(-1.5mm,1.5mm)$) rectangle ($(ffn.south east)+(1.5mm,-1.5mm)$);
\node[lab, anchor=north west, text=red!75!black, font=\scriptsize\bfseries]
  at ($(lin.north west)+(-1.5mm,1.2mm)$) {$\mathbf{N\times}$};

% 文本分支
\node[pnk, below=7mm of ae, minimum width=24mm, align=left, font=\tiny]
  (cap) {A cyberpunk cat with a\\sian that says "SANA"};
\node[pnk, right=4mm of cap, minimum width=15mm] (rew) {Rewriter};
\node[pnk, right=4mm of rew, minimum width=17mm] (llm) {Small LLM};
\node[pnk, right=4mm of llm, minimum width=15mm] (temb) {Time Emb};
\draw[arr] (cap) -- (rew);
\draw[arr] (rew) -- (llm);
\draw[arr] (llm) -- (temb);
\draw[arr] (llm.north) -- ++(0,0.42) -| (cro.south);
\end{scope}

% ============ (c) Linear DiT module ============
\begin{scope}[shift={(13.4,-1.35)}]
\node[lab, anchor=south] at (1.55,3.10) {\textbf{(c)} Linear DiT module};

% --- Linear Attention 子块
\begin{scope}[shift={(0,0)}]
  \fill[blue!12, rounded corners=6pt] (-0.75,-0.30) rectangle (2.75,3.30);
  \node[font=\scriptsize\bfseries] at (1.0,3.06) {Linear Attention};

  \node[box, fill=white, minimum width=13mm] (scale) at (1.0,2.55) {Scale};
  \node[box, fill=white, minimum width=15mm] (mm) at (1.0,1.95) {MatMul};
  \node[box, fill=white, minimum width=15mm] (mm2) at (1.35,1.35) {MatMul};
  \node[box, fill=fxorg, minimum width=11mm] (rope1) at (0.10,0.72) {3D RoPE};
  \node[box, fill=fxorg, minimum width=11mm] (rope2) at (2.30,0.72) {3D RoPE};
  \node[box, fill=white, minimum width=11mm] (relu1) at (0.10,0.16) {ReLU};
  \node[box, fill=white, minimum width=11mm] (relu2) at (2.30,0.16) {ReLU};
  \node[box, fill=white, minimum width=11mm] (lin1) at (-0.55,-0.58) {Linear};
  \node[box, fill=white, minimum width=11mm] (lin2) at (1.35,-0.58) {Linear};
  \node[box, fill=white, minimum width=11mm] (lin3) at (2.95,-0.58) {Linear};
  \node[lab] at (-0.55,-1.02) {$Q$}; \node[lab] at (1.35,-1.02) {$K$}; \node[lab] at (2.95,-1.02) {$V$};

  \draw[arr] (mm) -- (scale);
  \draw[arr] (mm2) -- (mm);
  \draw[arr] (rope1) -- (mm2);
  \draw[arr] (rope2) -- (mm2);
  \draw[arr] (relu1) -- (rope1); \draw[arr] (relu2) -- (rope2);
  \draw[arr] (lin1) -- (relu1); \draw[arr] (lin2) -- (relu2); \draw[arr] (lin3) -- (mm2);
  \node[lab, anchor=west] at (0.42,1.60) {$n\times d$};
  \node[lab, anchor=west] at (1.18,0.86) {$d\times n$};
  \node[lab, anchor=east] at (1.55,0.68) {$n\times d$};
  \node[lab, anchor=north] at (1.1,-1.36) {Cost: $\mathcal{O}(n)$};
\end{scope}

% --- Mix-FFN 子块
\begin{scope}[shift={(4.35,0)}]
  \fill[blue!12, rounded corners=6pt] (-0.60,-0.30) rectangle (2.30,3.30);
  \node[font=\scriptsize\bfseries] at (0.85,3.06) {Mix-FFN};

  \node[box, fill=fxorg, minimum width=24mm, minimum height=9mm, font=\tiny\bfseries]
    (tmpl) at (0.85,2.50) {Temporal\\$3\times1\times1$ ConvLayer};
  \node[box, fill=white, minimum width=24mm] (c1) at (0.85,1.78) {$1\times1$ ConvLayer};
  \node[box, fill=white, minimum width=24mm] (c2) at (0.85,0.42) {$1\times3\times3$ ConvLayer};
  \node[box, fill=white, minimum width=24mm] (c3) at (0.85,-0.30) {$1\times1$ ConvLayer};
  \node[circle, draw=black!55, fill=white, inner sep=1.5pt, font=\scriptsize] (mul) at (0.85,1.10) {$\otimes$};
  \node[box, fill=fxpnk, minimum width=11mm] (silu) at (2.15,1.10) {SiLU};

  \draw[arr] (tmpl) -- (c1);
  \draw[arr] (c1) -- (mul);
  \draw[arr] (c3) -- (c2);
  \draw[arr] (c2) -- (mul);
  \draw[arr] (mul) -- (silu);
  \draw[arr] (mul) -- (tmpl.east);
\end{scope}
\end{scope}
\end{tikzpicture}
"""


def fig06() -> str:
    return r"""
\begin{tikzpicture}[node distance=3mm]
\tikzset{
  cell/.style={draw=black!45, line width=.35pt, minimum size=4.2mm, inner sep=0pt},
  tok/.style={cell, fill=white},
  mask/.style={cell, fill=black!25},
  kv/.style={cell, fill=red!55!black},
  cmp/.style={cell, fill=green!65!black},
  ttl/.style={font=\scriptsize, align=center},
  arr/.style={-{Stealth[length=1.8mm,width=1.2mm]}, line width=.7pt, draw=black!80},
}

% ===== 图例 =====
\begin{scope}[shift={(0,3.35)}]
  \node[cell, fill=white, minimum size=3.6mm] (l1) at (0,0) {};
  \node[anchor=west, font=\scriptsize] at (0.28,0) {Token};
  \node[cell, fill=black!25, minimum size=3.6mm] (l2) at (1.75,0) {};
  \node[anchor=west, font=\scriptsize] at (2.03,0) {Mask};
  \node[cell, fill=red!55!black, minimum size=3.6mm] (l3) at (3.45,0) {};
  \node[anchor=west, font=\scriptsize] at (3.73,0) {KV Cache};
  \node[cell, fill=green!65!black, minimum size=3.6mm] (l4) at (5.45,0) {};
  \node[anchor=west, font=\scriptsize] at (5.73,0) {Compute};
\end{scope}

% ===== (a-1) Vanilla Attention =====
\begin{scope}[shift={(0,1.55)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \node[cmp] at (\c*0.44, -\r*0.36) {};
    }
  }
  \draw[black!45, line width=.4pt] (-0.22,0.18) rectangle (1.54,-1.26);
  \node[ttl, below=2mm] at (0.66,-1.42) {Vanilla Attention};
  % Q/K 标注
  \node[font=\tiny] at (-0.55,-0.02) {$Q_1$};
  \node[font=\tiny] at (-0.55,-1.10) {$Q_N$};
  \node[font=\tiny] at (-0.10,0.34) {$K_1$};
  \node[font=\tiny] at (1.40,0.34) {$K_N$};
  \node[font=\tiny] at (0.12,0.34) {$\cdots$};
  \node[font=\tiny] at (0.60,0.34) {$\cdots$};
\end{scope}

% 乘号
\node[font=\Large] at (2.05,0.55) {$\times$};

% ===== (a-2) Linear Attention =====
\begin{scope}[shift={(2.55,1.55)}]
  % V 列
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,0}{
      \node[tok] at (\c*0.44, -\r*0.36) {};
    }
  }
  \draw[black!45, line width=.4pt] (-0.22,0.18) rectangle (0.22,-1.26);
  \node[font=\tiny] at (0,-0.02) {$V_1$};
  \node[font=\tiny] at (0,-1.10) {$V_N$};
  \node[font=\tiny] at (0.44,0.34) {$d$};
  \node[font=\tiny] at (-0.52,-1.10) {$N$};

  \node[font=\Large] at (0.95,0.55) {$\times$};

  % Q 列
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,0}{
      \node[tok] at (1.45+\c*0.44, -\r*0.36) {};
    }
  }
  \draw[black!45, line width=.4pt] (1.23,0.18) rectangle (1.67,-1.26);
  \node[font=\tiny] at (1.45,-0.02) {$Q_1$};
  \node[font=\tiny] at (1.45,-1.10) {$Q_N$};
  \node[font=\tiny] at (1.90,0.34) {$d$};

  \node[font=\Large] at (2.40,0.55) {$\times$};

  % 结果小格
  \node[cmp, minimum size=8mm] (res) at (2.95,-0.55) {};
  \node[font=\tiny] at (2.95,-0.52) {$\sum$};
  \node[font=\tiny] at (2.95,0.02) {$d$};
  \node[font=\tiny, anchor=east] at (2.52,-0.55) {$d$};

  \node[ttl, below=2mm] at (1.45,-1.42) {Linear Attention};

  % Block 括号
  \draw[decorate, decoration={brace, amplitude=4pt}, black!60]
    (1.15,0.22) -- (1.15,-0.52) node[midway, left=4pt, font=\tiny] {Block$_1$};
  \draw[decorate, decoration={brace, amplitude=4pt}, black!60]
    (1.15,-0.62) -- (1.15,-1.30) node[midway, left=4pt, font=\tiny] {Block$_N$};
\end{scope}

% ===== (a-3) Causal Linear Attention =====
\begin{scope}[shift={(7.55,1.55)}]
  \foreach \r in {0,...,3}{
    \foreach \c in {0,...,3}{
      \pgfmathparse{\r<\c ? 0 : (\r==\c ? 1 : 2)}
      \ifnum\pgfmathresult=0
        \node[mask] at (\c*0.44, -\r*0.36) {};
      \else\ifnum\pgfmathresult=1
        \node[cmp] at (\c*0.44, -\r*0.36) {};
      \else
        \node[kv] at (\c*0.44, -\r*0.36) {};
      \fi\fi
    }
  }
  \draw[black!45, line width=.4pt] (-0.22,0.18) rectangle (1.54,-1.26);
  \node[ttl, below=2mm] at (0.66,-1.42) {Causal Linear Attention};
  \node[font=\tiny] at (-0.55,-0.02) {$Q_1$};
  \node[font=\tiny] at (-0.55,-1.10) {$Q_N$};
  \node[font=\tiny] at (0.10,0.34) {$d$};
  \node[font=\tiny] at (-0.42,0.10) {$d$};

  % 累积求和箭头
  \draw[arr, draw=black!70] (-0.05,-0.36) -- (1.05,-0.36);
  \node[font=\tiny, anchor=west] at (1.10,-0.36) {$\sum_{i=1}^{2}K_iV_i$};
  \draw[arr, draw=black!70] (-0.05,-0.72) -- (1.35,-0.72);
  \node[font=\tiny, anchor=west] at (1.42,-0.72) {$\sum_{i=1}^{3}K_iV_i$};
  \draw[arr, draw=white, line width=1.6pt] (-0.05,-1.08) -- (1.45,-1.08);
  \draw[arr, draw=black!70] (-0.05,-1.08) -- (1.45,-1.08);
  \node[font=\tiny, anchor=west] at (1.52,-1.08) {Cumulative Sum};

  % 左括号
  \draw[decorate, decoration={brace, amplitude=4pt, mirror}, black!60]
    (-0.30,0.22) -- (-0.30,-0.52) node[midway, left=5pt, font=\tiny] {Block$_1$};
  \draw[decorate, decoration={brace, amplitude=4pt, mirror}, black!60]
    (-0.30,-0.62) -- (-0.30,-1.30) node[midway, left=5pt, font=\tiny] {Block$_N$};
\end{scope}

% ===== (b) Block Causal Mix-FFN =====
\begin{scope}[shift={(11.6,1.75)}]
  % (逐个显式绘制，见下)
  % 具体标签
  \node[font=\tiny, fill=fxgrn, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm] at (0.9,1.35) {Token-2};
  \node[font=\tiny, fill=fxgrn, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm] at (0.9,0.80) {Token-1};
  \node[font=\tiny, fill=blue!70, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm, text=white] at (0.9,0.25) {Zero Padding};
  \node[font=\tiny, fill=red!55!black, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm, text=white] at (0.9,-0.30) {Cached Token-1};
  \node[font=\tiny, fill=fxgrn, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm] at (0.9,-0.85) {Token$_0$};
  \node[font=\tiny, fill=fxgrn, draw=black!50, rounded corners=2pt, minimum width=24mm,
        minimum height=6mm] at (0.9,-1.40) {Token$_1$};

  % 缓存复用弧线
  \draw[arr, draw=blue!70, line width=1.0pt] (2.20,0.25) to[bend left=40] (2.20,-0.30);
  % 上下省略号
  \node[font=\scriptsize] at (0.9,1.85) {$\vdots$};
  \node[font=\scriptsize] at (0.9,-1.90) {$\vdots$};

  \draw[decorate, decoration={brace, amplitude=4pt, mirror}, black!60]
    (2.55,1.62) -- (2.55,0.58) node[midway, right=5pt, font=\tiny] {Block$_1$};
  \draw[decorate, decoration={brace, amplitude=4pt, mirror}, black!60]
    (2.55,0.02) -- (2.55,-1.62) node[midway, right=5pt, font=\tiny] {Block$_2$};

  \node[ttl, below=16mm] at (0.9,-2.05) {(b) Block Causal Mix-FFN};
\end{scope}

% 顶部总标题
\node[font=\scriptsize, anchor=north] at (3.3,3.05) {(a) Block Causal Linear Attention};
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
