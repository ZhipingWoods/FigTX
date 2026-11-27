# 场景 JSON 格式（figtx-forge v1）

```json
{
  "version": 1,
  "canvas": {"width": 1092, "height": 599, "background": "#FFFFFF"},
  "nodes": [ ... ]
}
```

坐标单位 = 原图像素，原点左上角。`canvas.width/height` 必须等于原图尺寸。节点按数组顺序绘制（后画的在上层）。每个节点必须有唯一 `id`。

| type | 必填字段 | 可选字段 |
|---|---|---|
| `rect` | x, y, w, h | rx（圆角）, fill, stroke, strokeWidth, dash, opacity |
| `ellipse` | cx, cy, rx, ry | fill, stroke, strokeWidth, dash, opacity |
| `line` | x1, y1, x2, y2 | stroke, strokeWidth, dash, arrowEnd, arrowStart, opacity |
| `polyline` | points `[[x,y],...]` | closed, fill, stroke, strokeWidth, dash, arrowEnd, arrowStart |
| `path` | d（SVG path 语法，支持 M L H V C S Q T Z，A 按直线近似） | 同 polyline |
| `text` | x, y, w, h, text | fontSize(px), fontWeight, fontStyle, fontFamily, fill, align(left/center/right), valign(top/middle/bottom) |
| `image` | x, y, w, h, href（场景目录下的相对路径，如 `crops/photo-1.png`） | — |

- 颜色：`#RGB`、`#RRGGBB` 或 `"none"`。rect/ellipse 默认白色填充；line/polyline/path 默认无填充。
- `dash`：如 `[6, 4]`，对应虚线。
- `text` 的 x/y/w/h 是文字框，不是基线。一行一个 text 节点；多行文字拆成多个节点。
- 上下标、希腊字母用 Unicode 字符直接写进 text。

检查与导出命令：`figtx validate scene.json`、`figtx render scene.json -o r.png`、`figtx lint scene.json`、`figtx redraw-check original.png scene.json -o out --texts texts.txt`、`figtx export scene.json -o out`。
