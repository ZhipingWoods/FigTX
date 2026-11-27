# 设计契约字段（从参考图测量，全部写具体数值）

来源：FigTX `tools/figgen/contract.py`（契约思路来自 topconf-paper-figure-gallery：形容词会把决策丢给生成者，风格漂移就是这么来的；只有精确数值能钉住风格）。

```json
{
  "canvas": {"aspect": "16:9 | 4:3 | other", "orientation": "landscape | portrait | square"},
  "pattern": "pipeline | teaser | motivation | comparison | system-overview | result-grid | other",
  "palette": {"background": "#hex", "primary": "#hex", "accent": "#hex", "neutral": "#hex", "others": ["#hex"]},
  "typography": {"title_px": 0, "panel_header_px": 0, "label_px": 0, "note_px": 0, "family": "sans | serif | mixed"},
  "strokes": {"box_px": 0, "arrow_px": 0, "connector_px": 0, "panel_border_heavier_than_module": true},
  "density": {"panels": 0, "containers": 0, "modules_per_panel": 0, "solid_borders": 0, "dashed_borders": 0,
              "connectors": 0, "fill_percent": 0},
  "layout": {"reading_direction": "left-to-right | top-to-bottom | other", "panel_division": "画布如何切分"},
  "topology": {"anchor": "视线起点", "flow": "信息怎么流动", "spacing": "间距与分组节奏"},
  "style_fingerprint": {"panel_shape": "rounded | sharp | mixed", "module_shape": "", "arrow_style": "",
                        "icon_style": "", "text_treatment": ""},
  "panels": [{"name": "只写角色，不写参考图的名字", "role": "", "x_pct": 0, "y_pct": 0, "w_pct": 0, "h_pct": 0}],
  "elements": ["实际看到的重复元素类型"],
  "reusable_rules": ["3-6 条可度量、祈使句的规则"]
}
```

- `*_pct` 是相对画布的 0–100 整数。数量要数准。
- `panels[].name` 只写结构角色（如 "input stage"、"zoom-in inset"），**不要**抄参考图的面板标题——契约只承载视觉语法。
- 字段在参考图里确实不存在就省略，不要编。
