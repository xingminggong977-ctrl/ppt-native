# guochao · 国潮

墨底、金线、朱红印章，标题用毛笔字，内容压在一条大弧线切出来的深色面板里。
适合品牌提案、文化专题、需要气场的中文演示；不适合作表、放大量数据。

规格来源：`docs/guochao-theme-spec.md`（本主题逐条实现，没有自由发挥改设计）。

## 观感

| 元素 | 做法 |
| --- | --- |
| 底色 | 无图时是**径向渐变**：中心 `#2A241C` 亮、边缘 `#0E0C0A` 沉，像灯下的纸 |
| 主色 | 金 `#C9A227` 只做细线、小标签、印章边框；亮金 `#E8CE8F` 只做结尾大字与数字 |
| 朱红 | `#B1362A` **只出现在封面右上/右下那个 24×24 的印章方块上**，整页面积 < 0.1%（规格要求 ≤3%） |
| 标题 | 华文行楷（毛笔），只用在 40pt 以上：封面 63pt / 章节 55.5pt / 结尾 64pt |
| 次级标题 | 华文新魏 32pt，正文 微软雅黑 18–20pt，行距 1.6 |
| 图形 | 章节页三只同心金环；内容页一条从顶边划到底边的凹弧，把右半页切成深色面板 |

1px = 0.75pt 是这套仓库的单位约定，`theme.py` 的 `SIZE` 全部按 px 写。

## 文件

```
themes/guochao/theme.py     色板 / 字号阶梯 / 字体链 / HEAD FOOT CARD BAND
                            / PANEL COVER RINGS 几何 / background()
themes/guochao/README.md    本文件
examples/demo_guochao.py    6 页示例（封面 / 章节 / 内容×3 / 结尾）
```

`theme.py` 与 `themes/minimal-ink/theme.py` 的 key 一一对齐（`font` `colors`
`size` `head` `foot` `card` `band` `photo` `image_frame` `background()`），
另外多出三个只有本主题用得上的常量：`PANEL`（右侧面板几何）、`COVER`（封面与
结尾基线）、`RINGS`（同心圆环）。

页面里不写任何颜色或字号，全部读 `deck.theme.colors` / `deck.theme.size`。
`scripts/primitives.py` 里同样没有颜色、没有字体名——换肤只改主题。

## 字体依赖与回退

| 用途 | 首选 | 回退链（写在 SVG 里） |
| --- | --- | --- |
| 毛笔大标题 | 华文行楷 `STXINGKA.TTF` | `华文行楷, STXingkai, 楷体, KaiTi` |
| 次级标题 | 华文新魏 `STXINWEI.TTF` | `华文新魏, STXinwei, 黑体, SimHei` |
| 正文 | 微软雅黑 `msyh.ttc` | `Microsoft YaHei, SimHei, SimSun` |

链里第一个中文族名是给人在 PowerPoint 字体框里看的；紧跟的英文别名是必须的，
因为上游 converter 只把英文别名（`STXingkai`/`STXinwei`/`KaiTi`/`SimHei`…）
认成东亚字体，只写中文名时中文会悄悄落回正文字体。

```bash
# 机器上没有华文家族时：不报错，整篇退回楷体/黑体
python scripts/build.py --example demo_guochao \
  --out examples/build/demo_guochao_fb.pptx --font-fallback

# 反过来，如果导入时探测不到 STXINGKA.TTF，主题自己也会降级并在 stderr 提示
```

`--font-fallback` 打开后，主题的 major/minor 字体变成 `楷体 / KaiTi`，版式完全
不变，只是没有毛笔味（笔画从"写"变成"印"）。实测：同一份 6 页 deck，两版都
exit 0、都不溢出。

**注意**：`.pptx` 里每个 run 引用的是主题的 `+mj-*` / `+mn-*`，也就是说
**交付文件里只保留字体链解析后的第一个可用项**（现在写作 `华文行楷` + `STXingkai`），
后面的 `楷体/KaiTi` 兜底只在 SVG 源里生效。要确保在别人的机器上不跳字体，
要么用 `--font-fallback` 出片，要么让对方装华文家族。

## 背景图

```bash
# 用图：整页铺满，上面压 30% #0E0C0A 蒙版保证文字可读
python scripts/build.py --example demo_guochao \
  --out examples/build/demo_guochao_bg.pptx \
  --bg-image path/to/photo.jpg

# 不用图：走 THEME.background() 的渐变兜底
python scripts/build.py --example demo_guochao \
  --out examples/build/demo_guochao.pptx \
  --transition circle --transition-duration 2.0
```

换背景图只需换 `--bg-image` 指向的文件；`deck.add_image(..., crop=True)` 会按
16:9 居中裁切到 2560×1440 再嵌入，不会拉伸变形。

蒙版浓度在 `theme.py` 的 `BG_IMAGE_SCRIM`（默认 0.30，按规格）。**图片偏亮时要
自己把它调到 0.45–0.55**，否则 PAPER 色的字在亮部会发飘——这是本主题唯一需要
人工判断的地方。

### 兜底用哪一档、为什么

`BG_MODE = "radial"`，即规格里的**第①档径向渐变**（中心 `#2A241C` → 55% 处
`#1A1613` → 边缘 `#0E0C0A`）。

上游 converter 的 `drawingml/styles.py` 支持 `radialGradient`，但有两条约束：
渐变焦点必须落在以 (0.5,0.5) 为心、半径 0.5 的圆内，否则抛
`Radial gradient effective focus must lie within the canonical circle ...`；
`r` 属性会被忽略（渐变恒铺满形状）。本主题焦点就是正中心，两条都不犯，
实测导出为真 `<a:gradFill><a:path path="circle">`，所以**没有退到第②档**。
若将来某台机器的 converter 变了，把 `BG_MODE` 改成 `"linear"`（第②档线性）或
`"flat"`（第③档纯 `#0E0C0A`）即可，页面代码一行都不用动。

## 版式

- **A 封面**：主标题行楷 63pt + 一条 120×3 的金短线 + 新魏 24pt 副标题，
  右下角 24×24 朱红印章（留空，也可以塞一个字进去，`_seal()` 在示例里）。
- **B 章节页**：三只同心圆环（直径 400/300/200px，`fill="none"`，金描边 1.5pt，
  透明度 30%/50%/70%，是三个独立形状，可在 PowerPoint 里单独选中），
  居中章节名行楷 55.5pt、字距 10px，下方一条与标题等宽的金线。
- **C 内容页**：右侧 `x=600` 起、贴右边缘的深色面板，左缘是规格给的那条贝塞尔弧
  （`M 812 0 C 640 150 600 340 700 430 C 770 500 830 600 845 720 L 1280 720
  L 1280 0 Z`，导出成真 `<a:custGeom>`）。面板内文字列 `x=790`、宽 406：
  金标签 14pt → 新魏 32pt 标题 → 金线 → 雅黑 18pt 正文（行距 1.6）→ 右下页码 12pt。
  **正文到 y≈520 为止**：再往下弧线已经收窄到 x≈780，文字会掉出面板。
- **D 结尾**：同封面背景，居中「感谢聆听」行楷 64pt 亮金 + 一行 14pt MUTED 小字。

`ARC_PANEL(..., edge="right")` 是本主题新加的原语（`scripts/primitives.py`），
弧线锚点在模块级 `EDGE_ARC_ANCHORS` 里按面板包围盒的分数给出，别的主题传
`anchors={...}` 就能改弯曲形状；`edge="top"` 保持 `demo_minimal` 原来的上拱面板。

## 转场

```bash
python scripts/build.py --example demo_guochao \
  --out examples/build/demo_guochao.pptx \
  --transition circle --transition-duration 2.0
```

全篇 `<p:p:circle/>`、`p14:dur="2000"`（即 2.0 秒，不是默认 1.0 秒）。

**LibreOffice 预览看不到转场**——`--skip-render` 之外那条 PNG 预览链路是
pptx → PDF → PNG，转场在 PDF 里本来就不存在。要看圆形转场必须在
**PowerPoint 放映模式**下验收。

## 已知约束

- 朱红只有印章一处；如果后续页面要加红色，先算面积（规格硬要求 ≤3%/页）。
- 毛笔字体只允许 ≥40pt；`T(..., font=deck.theme.font_for("display"))` 不要用在正文。
- `post_fix.py` 用微软雅黑量字宽去放大文本框，行楷/新魏比雅黑窄，所以框会偏宽
  一点，只影响选中框，不影响视觉。
- `--font-fallback` 只换字体，不改字号，因此断行位置可能有 1–2 字差异（示例文字
  都按最宽情况留了余量，实测 6 页均不出界）。
- 上游 postflight 会报 `unsafe_exported_font_faces`（华文家族不在它的安全清单里），
  这是提示不是错误，导出与放映都正常。
