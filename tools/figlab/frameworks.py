#!/usr/bin/env python3
r"""框架图（framework / pipeline / architecture）TikZ 模板集。

每个模板输出：(id, 标题, 说明, 领域标签, 会议标签, TeX 源码片段)
"""
from __future__ import annotations

STYLES = r"""
\tikzset{
  blk/.style={draw=black!45, rounded corners=2.5pt, line width=.5pt,
              minimum height=9mm, minimum width=17mm, align=center,
              font=\small, inner sep=2.5pt},
  bin/.style={blk, fill=cinput!45, draw=cinputb},
  bback/.style={blk, fill=cback!45, draw=cbackb},
  bmod/.style={blk, fill=cmod!55, draw=cmodb, line width=.7pt},
  bours/.style={blk, fill=cours!55, draw=coursb, line width=.8pt},
  bloss/.style={blk, fill=closs!55, draw=clossb},
  bgr/.style={blk, fill=cgr!60, draw=cgrb, dashed},
  ar/.style={-{Stealth[length=2.2mm,width=1.6mm]}, line width=.6pt, draw=black!70},
  ard/.style={ar, dashed},
  lab/.style={font=\scriptsize, text=black!65, inner sep=1.5pt},
}
"""

# ---------------------------------------------------------------- 模板

def single_stream() -> str:
    return r"""
\begin{tikzpicture}[node distance=7mm and 8mm]
  \node[bin]  (in)  {Input $\mathbf{x}$};
  \node[bback, right=of in]  (bb) {Backbone\\\scriptsize (ResNet-50)};
  \node[bmod, right=of bb]   (m1) {Module A};
  \node[bmod, right=of m1]   (m2) {Module B};
  \node[bloss, right=of m2]  (hd) {Classifier};
  \node[lab, below=1.5mm of in] (l1) {image};
  \node[lab, below=1.5mm of hd] (l2) {$\hat{y}$};

  \draw[ar] (in) -- (bb);
  \draw[ar] (bb) -- (m1) node[lab, midway, above=1mm] {$\mathbf{f}$};
  \draw[ar] (m1) -- (m2);
  \draw[ar] (m2) -- (hd);

  % 跳跃连接
  \draw[ard] (bb.south) -- ++(0,-5mm) -| (m2.south)
    node[lab, pos=.25, below] {residual};

  % 图例（右侧纵排）
  \begin{scope}[shift={($(hd.east)+(6mm,4mm)$)}, every node/.style={anchor=west, font=\scriptsize}]
    \node[fill=cback, draw=cbackb, minimum width=3.5mm, minimum height=3.5mm, inner sep=0pt] (l1) at (0,0) {};
    \node[right=1mm of l1] {骨干};
    \node[fill=cmod, draw=cmodb, minimum width=3.5mm, minimum height=3.5mm, inner sep=0pt] (l2) at (0,-5mm) {};
    \node[right=1mm of l2] {本文模块};
    \node[fill=closs, draw=clossb, minimum width=3.5mm, minimum height=3.5mm, inner sep=0pt] (l3) at (0,-10mm) {};
    \node[right=1mm of l3] {预测头};
  \end{scope}
\end{tikzpicture}
"""

def two_branch() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm and 7mm]
  \node[bin] (img) {Image};
  \node[bin, below=9mm of img] (txt) {Text};

  \node[bback, right=of img] (vb) {Visual\\Encoder};
  \node[bback, right=of txt] (tb) {Text\\Encoder};

  \node[bmod, right=of vb] (vf) {Visual\\Proj.};
  \node[bmod, right=of tb] (tf) {Text\\Proj.};

  \node[bours, right=9mm of $(vf.east)!0.5!(tf.east)$] (fuse) {Cross-Modal\\Fusion};
  \node[bloss, right=of fuse] (out) {Output};

  \draw[ar] (img) -- (vb);
  \draw[ar] (txt) -- (tb);
  \draw[ar] (vb) -- (vf);
  \draw[ar] (tb) -- (tf);
  \draw[ar] (vf) -- (fuse);
  \draw[ar] (tf) -- (fuse);
  \draw[ar] (fuse) -- (out);
  \draw[ard] (vf.east) to[bend left=18] node[lab, above] {align} (tf.east);
\end{tikzpicture}
"""

def encoder_decoder() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm]
  \node[bin]  (x)   {Input};
  \node[bback, right=of x]  (e1) {Enc-1};
  \node[bback, right=of e1] (e2) {Enc-2};
  \node[bback, right=of e2] (e3) {Enc-3};
  \node[bmod,  below=10mm of e3] (b) {Bottleneck\\\scriptsize (ours)};
  \node[bback, left=of b]  (d3) {Dec-3};
  \node[bback, left=of d3] (d2) {Dec-2};
  \node[bback, left=of d2] (d1) {Dec-1};
  \node[bloss, below=8mm of x] (y) {Mask $\hat{m}$};

  \draw[ar] (x) -- (e1); \draw[ar] (e1) -- (e2); \draw[ar] (e2) -- (e3);
  \draw[ar] (e3) -- (b);
  \draw[ar] (b) -- (d3); \draw[ar] (d3) -- (d2); \draw[ar] (d2) -- (d1);
  \draw[ar] (d1) |- (y);

  % 对称 skip
  \draw[ard] (e1.north) -- ++(0,4mm) -| (d1.north);
  \draw[ard] (e2.north) -- ++(0,7mm) -| (d2.north);
  \draw[ard] (e3.north) -- ++(0,10mm) -| (d3.north);
  \node[lab] at ($(e2.north)+(0,7mm)+(2mm,0)$) {skip};
\end{tikzpicture}
"""

def module_zoom() -> str:
    return r"""
\begin{tikzpicture}[node distance=5mm]
  % 上层：整体流程（简化）
  \node[bin] (in) {Input};
  \node[bback, right=of in] (bb) {Backbone};
  \node[bours, right=of bb, minimum width=22mm, minimum height=12mm] (blk) {\textbf{Our Block}};
  \node[bloss, right=of blk] (out) {Output};
  \draw[ar] (in)--(bb); \draw[ar] (bb)--(blk); \draw[ar] (blk)--(out);

  % 放大区域：内部先排好，再用 fit 包框
  \node[bmod, below=24mm of bb] (s) {Split};
  \node[bmod, right=5mm of s] (a) {Attn};
  \node[bmod, right=5mm of a] (g) {Gate};
  \node[bmod, right=5mm of g] (c) {Concat};
  \draw[ar] (s)--(a); \draw[ar] (a)--(g); \draw[ar] (g)--(c);
  \draw[ard] (s.south) -- ++(0,-5mm) -| (c.south);
  \node[lab, below=6mm of a] (short) {shortcut};

  \node[draw=coursb, dashed, rounded corners=2pt, inner sep=3.5mm,
        fit=(s)(c)(short)] (zoom) {};
  \node[lab, anchor=south west, text=coursb] at (zoom.north west)
        {Zoom-in of \textbf{Our Block}};

  % 连接线：从 Our Block 两侧垂直下引到放大框顶边
  \draw[draw=coursb, dashed, line width=.5pt] (blk.south west) -- (blk.south west |- zoom.north);
  \draw[draw=coursb, dashed, line width=.5pt] (blk.south east) -- (blk.south east |- zoom.north);
\end{tikzpicture}
"""

def multi_stage() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm and 6mm]
  \node[bin] (x) {Input};
  \node[bback, right=of x] (s1) {Stage-1};
  \node[bmod, right=of s1] (s2) {Stage-2};
  \node[bmod, right=of s2] (s3) {Stage-3};
  \node[bloss, right=of s3] (y) {Prediction};

  \draw[ar] (x)--(s1); \draw[ar] (s1)--(s2); \draw[ar] (s2)--(s3); \draw[ar] (s3)--(y);

  % 级联反馈
  \draw[ard] (s3.south) -- ++(0,-5mm) -| node[lab, below, pos=.25]{refine} (s2.south);
  \draw[ard] (s2.south) -- ++(0,-9mm) -| node[lab, below, pos=.25]{refine} (s1.south);

  % 损失
  \node[lab, below=12mm of s2] (sup) {$\mathcal{L}=\mathcal{L}_{1}+\lambda\mathcal{L}_{2}$};
\end{tikzpicture}
"""

def graph_reasoning() -> str:
    return r"""
\begin{tikzpicture}[node distance=9mm]
  % 异构图：三种节点
  \node[circle, draw=cinputb, fill=cinput!60, minimum size=8mm, font=\scriptsize] (e1) at (0,0) {$e_1$};
  \node[circle, draw=cbackb, fill=cback!60, minimum size=8mm, font=\scriptsize] (e2) at (2.2,0.9) {$e_2$};
  \node[circle, draw=cinputb, fill=cinput!60, minimum size=8mm, font=\scriptsize] (e3) at (2.4,-0.8) {$e_3$};
  \node[rectangle, draw=cmodb, fill=cmod!60, minimum size=7mm, font=\scriptsize, rotate=0] (r1) at (1.1,1.5) {$r_1$};
  \node[rectangle, draw=cmodb, fill=cmod!60, minimum size=7mm, font=\scriptsize] (r2) at (1.2,-1.6) {$r_2$};

  \draw[ar] (e1)--(e2); \draw[ar] (e1)--(e3); \draw[ar] (e2)--(e3);
  \draw[ar] (e1)--(r1); \draw[ar] (e2)--(r1);
  \draw[ar] (e1)--(r2); \draw[ar] (e3)--(r2);

  % 推理链
  \node[bours, right=14mm of e2] (g) {GNN $\times L$};
  \node[bloss, right=of g] (p) {Score};
  \draw[ard] (e2) to[bend left=10] (g);
  \draw[ard] (r1) to[bend left=6] (g);
  \draw[ar] (g)--(p);
\end{tikzpicture}
"""


def templates() -> list[dict]:
    """返回所有框架图模板。"""
    T = [
        ("single-stream", single_stream(),
         "单流 Pipeline 骨架", "输入→骨干→串联模块→预测头，带跳跃连接与角色图例；改模块名即可套用",
         ["通用"], ["CVPR", "ICCV", "ECCV", "NeurIPS", "ICLR"]),
        ("two-branch", two_branch(),
         "双分支（双流）架构", "图文/音视双编码器 + 投影 + 跨模态融合，常用于多模态对齐",
         ["多模态"], ["CVPR", "ICCV", "ACL", "ACM MM", "NeurIPS"]),
        ("encoder-decoder", encoder_decoder(),
         "编码-解码 + 对称跳跃", "U 形结构，三处 skip 连接，分割/去噪类论文的标配",
         ["分割"], ["CVPR", "ICCV", "ECCV", "MICCAI"]),
        ("module-zoom", module_zoom(),
         "主干 + 模块放大（Zoom-in）", "上层画整体流程，下方虚线框放大单个模块的内部结构，评审最爱看",
         ["通用"], ["CVPR", "ICLR", "NeurIPS", "ICML"]),
        ("multi-stage", multi_stage(),
         "多阶段级联 + 逐级精修", "Stage 串联并在下方画反馈箭头，配多任务损失",
         ["检测"], ["CVPR", "ICCV", "ECCV"]),
        ("graph-reasoning", graph_reasoning(),
         "图结构 + 消息传递", "异构节点/边 + GNN 推理，知识图谱与关系建模类论文常用",
         ["LLM"], ["ACL", "NeurIPS", "ICLR", "EMNLP"]),
        ("attention-module", attention_module(),
         "自注意力模块（Q/K/V）", "把 softmax(QKᵀ/√d) 与 AV 显式画出来，Transformer 类论文的通用画法",
         ["LLM"], ["NeurIPS", "ICLR", "ICML", "ACL"]),
        ("moe-routing", moe_routing(),
         "MoE 路由 + 多专家", "Router 输出权重分发到多个 Expert 再加权求和，附负载均衡损失标注",
         ["LLM"], ["NeurIPS", "ICML", "ICLR", "MLSys"]),
        ("quant-pipeline", quant_pipeline(),
         "量化流程（含 STE）", "统计→缩放因子→量化→反量化，虚线标出直通估计的反向路径",
         ["量化"], ["ICLR", "ICML", "NeurIPS", "DAC", "TCAD"]),
        ("prune-pipeline", prune_pipeline(),
         "剪枝流程（含迭代回路）", "重要性打分→生成掩码→稀疏模型→微调，虚线回路表示迭代剪枝",
         ["剪枝"], ["ICLR", "NeurIPS", "ICML", "MLSys"]),
        ("distill-pipeline", distill_pipeline(),
         "知识蒸馏（教师-学生）", "并行两支 + KL 软标签 + CE 硬标签，最后按 α 加权",
         ["蒸馏"], ["CVPR", "ICLR", "NeurIPS", "ICML"]),
        ("hardware-systolic", hardware_block(),
         "硬件数据流（脉动阵列）", "PE 阵列 + DRAM/缓冲，适合体系结构会议画加速器总体结构",
         ["系统"], ["MICRO", "HPCA", "ISCA", "ASPLOS", "DAC"]),
    ]
    return [{"slug": s, "tex": t, "title": ti, "desc": d, "domain": dom, "venues": v}
            for s, t, ti, d, dom, v in T]


# ---------------------------------------------------------------- 追加模板

def attention_module() -> str:
    return r"""
\begin{tikzpicture}[node distance=5mm]
  \node[bin] (x) {$\mathbf{X}\in\mathbb{R}^{N\times d}$};
  \node[bmod, right=of x] (q) {$Q$};
  \node[bmod, above=6mm of q] (k) {$K$};
  \node[bmod, below=6mm of q] (v) {$V$};
  \node[bours, right=9mm of q] (att) {$A=\mathrm{softmax}\!\left(\dfrac{QK^{\top}}{\sqrt{d_k}}\right)$};
  \node[bloss, right=of att] (o) {$\mathbf{Y}=A V$};

  \draw[ar] (x) -- (q);
  \draw[ar] (x.east) to[bend left=22] (k.west);
  \draw[ar] (x.east) to[bend right=22] (v.west);
  \draw[ar] (q) -- (att); \draw[ar] (k) -- (att); \draw[ar] (v) -- (att);
  \draw[ar] (att) -- (o);
  \node[lab, below=1mm of o] {$d_k=d/h$};
\end{tikzpicture}
"""

def moe_routing() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm]
  \node[bin] (x) {Token $\mathbf{x}$};
  \node[bmod, right=of x] (g) {Router\\\scriptsize $g(\mathbf{x})$};

  \node[bback, above right=3mm and 10mm of g] (e1) {Expert 1};
  \node[bback, right=10mm of g] (e2) {Expert 2};
  \node[bback, below right=3mm and 10mm of g] (e3) {Expert $k$};

  \node[bours, right=12mm of e2] (c) {Weighted\\Sum};
  \node[bloss, right=of c] (o) {Output};

  \draw[ar] (x)--(g);
  \draw[ar] (g.east) to[bend left=14] node[lab, above]{$p_1$} (e1.west);
  \draw[ar] (g)--(e2) node[lab, midway, above]{$p_2$};
  \draw[ar] (g.east) to[bend right=14] node[lab, below]{$p_k$} (e3.west);
  \draw[ar] (e1.east) to[bend left=10] (c);
  \draw[ar] (e2)--(c);
  \draw[ar] (e3.east) to[bend right=10] (c);
  \draw[ar] (c)--(o);
  \node[lab, below=1.5mm of g] {负载均衡损失};
\end{tikzpicture}
"""

def quant_pipeline() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm]
  \node[bin] (w) {FP32 权重};
  \node[bmod, right=of w] (s) {统计\\\scriptsize min/max};
  \node[bmod, right=of s] (sc) {缩放因子\\\scriptsize $s=\frac{\max|W|}{2^{b-1}-1}$};
  \node[bours, right=of sc] (q) {量化\\\scriptsize $\hat{W}=\mathrm{round}(W/s)$};
  \node[bloss, right=of q] (d) {反量化\\\scriptsize $\tilde{W}=s\hat{W}$};

  \draw[ar] (w)--(s); \draw[ar] (s)--(sc); \draw[ar] (sc)--(q); \draw[ar] (q)--(d);
  \draw[ard] (w.south) -- ++(0,-6mm) -| node[lab, below, pos=.75]{STE 直通估计} (d.south);
  \node[lab, above=1mm of q] {$b\in\{4,8\}$};
\end{tikzpicture}
"""

def prune_pipeline() -> str:
    return r"""
\begin{tikzpicture}[node distance=6mm]
  \node[bin] (m) {稠密模型};
  \node[bmod, right=of m] (imp) {重要性打分\\\scriptsize $|W_{ij}|$ / 梯度};
  \node[bmod, right=of imp] (mask) {生成掩码\\\scriptsize $\mathbf{m}\in\{0,1\}$};
  \node[bours, right=of mask] (sp) {稀疏模型};
  \node[bloss, right=of sp] (ft) {微调恢复};

  \draw[ar] (m)--(imp); \draw[ar] (imp)--(mask); \draw[ar] (mask)--(sp); \draw[ar] (sp)--(ft);
  \draw[ard] (ft.south) -- ++(0,-7mm) -| node[lab, below, pos=.25]{迭代剪枝} (imp.south);
  \node[lab, above=1.5mm of mask] {稀疏度 $s\%$};
\end{tikzpicture}
"""

def distill_pipeline() -> str:
    return r"""
\begin{tikzpicture}[node distance=8mm]
  \node[bin] (x) {输入 $\mathbf{x}$};
  \node[bback, above right=4mm and 12mm of x] (t) {教师模型\\\scriptsize (frozen)};
  \node[bmod, below right=4mm and 12mm of x] (s) {学生模型\\\scriptsize (ours)};

  \node[bloss, right=12mm of t] (lt) {软标签\\\scriptsize $T=4$};
  \node[bloss, right=12mm of s] (ls) {硬标签\\\scriptsize CE};
  \node[bours, right=10mm of $(lt)!0.5!(ls)$] (tot) {$\mathcal{L}=\alpha\mathcal{L}_{KD}+(1-\alpha)\mathcal{L}_{CE}$};

  \draw[ar] (x.east) to[bend left=16] (t.west);
  \draw[ar] (x.east) to[bend right=16] (s.west);
  \draw[ar] (t)--(lt); \draw[ar] (s)--(ls);
  \draw[ar] (lt)--(tot); \draw[ar] (ls)--(tot);
  \draw[ard] (t.south) -- node[lab, right]{KL} (s.north);
\end{tikzpicture}
"""

def hardware_block() -> str:
    return r"""
\begin{tikzpicture}[node distance=3mm]
  % 脉动阵列：4x4 PE
  \foreach \i in {0,...,3}{
    \foreach \j in {0,...,3}{
      \node[draw=cmodb, fill=cmod!45, minimum size=8mm, inner sep=0pt,
            font=\tiny] (pe\i\j) at (\j*9mm, -\i*9mm) {PE};
    }
  }
  \node[dashed, rounded corners=2pt, inner sep=2.5mm,
        fit=(pe00)(pe33), draw=coursb] (arr) {};
  \node[lab, above=1mm of arr] {$\mathbf{4\times4}$ 脉动阵列};

  \node[bin, left=9mm of pe00, yshift=-13mm] (dram) {DRAM};
  \node[bback, right=9mm of pe03, yshift=-13mm] (buf) {输出缓冲};

  \draw[ar, -{Stealth[length=1.8mm]}] ($(dram.east)+(0,4mm)$) -- ++(6mm,0) node[lab, above, pos=.3]{载入};
  \draw[ar] (buf.west) -- ++(-6mm,0);
  \node[lab, below=2mm of dram] {带宽瓶颈};
  \node[lab, below=2mm of buf] {写回};
\end{tikzpicture}
"""

