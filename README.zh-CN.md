# ppt-native

[English](README.md) | [简体中文](README.zh-CN.md)

一个把结构化文案变成**真正原生、可编辑 `.pptx`** 的小工具包 —— 每一个标题、段落、卡片、色带、细线都是 PowerPoint 里的真实形状，不是一张截图。

它面向的是中文长文型幻灯片（汇报、总结、学期小结）这种**排版会决定观感**的场合：字宽实测、中文断行、不会一个字一个 run、主题层与内容层彻底分离。

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────┐
│ example.py  │ → │ SVG 工程     │ → │ 原生 .pptx   │ → │ PNG 预览    │
│ + theme.py  │   │ 1280×720     │   │ DrawingML    │   │ LibreOffice │
└─────────────┘   └──────────────┘   └──────────────┘   └─────────────┘
```

## 它是什么

- 一套**版式原语库**（`scripts/primitives.py`），自身不含任何颜色和字号。
- 一份**主题契约**（`themes/*/theme.py`），掌管色板、字号阶梯、区块样式；换一个文件就换整套观感。
- 一个**deck 模型**（`scripts/deck.py`），负责materialise 页面、图片与 `deck.json` 清单。
- 一条**命令跑完全程**的流水线（`scripts/build.py`）：质量闸 → 上游 SVG→PPTX 转换器 → 文本框宽度修正 → PNG 渲染。

## 它不是什么

- 不是「一句话生成整份 PPT」的产品。你（或 AI）写一个几十行的 Python 模块描述页面，工具负责排版与转换。
- 不是图片转幻灯片。没有 OCR，不生成整页截图。
- 不是模板填空。没有一套必须遵守的固定版式，原语可以自由组合。

## 快速开始

环境要求：Windows + 微软雅黑、Python 3.10+、LibreOffice，以及一份本地 MIT 协议的 `ppt-master`（只用到其中的 `scripts/svg_to_pptx.py` 和 `scripts/svg_quality_checker.py`）。

```powershell
python scripts/build.py --example demo_minimal `
    --out examples/build/demo_minimal.pptx
```

如果 `python` 不在 `PATH` 里，换成你自己解释器的完整路径，例如 `C:\Python310\python.exe`。

一条命令产出三样东西：

```
examples/build/demo_minimal.pptx            # 成品
examples/build/demo_minimal_project/        # SVG 源文件 + deck.json
examples/build/demo_minimal_preview/        # page_01.png ... page_08.png
```

常用参数：

```powershell
# 换主题
python scripts/build.py --example demo_minimal --theme themes/minimal-ink

# 整幅背景照片（16:9 图片会居中裁切）
python scripts/build.py --example demo_minimal --bg-image .\photo.jpg

# 圆形转场，2 秒（原样透传给 svg_to_pptx.py）
python scripts/build.py --example demo_minimal `
    --transition circle --transition-duration 2.0

# 调版式时跳过耗时的 LibreOffice 渲染
python scripts/build.py --example demo_minimal --skip-render
```

`build.py` 默认在 `~/.dsh/skills/ppt-master` 找 `ppt-master`，也可以用 `--skill-dir <路径>` 或环境变量 `PPT_MASTER_SKILL` 指过去。

## 写一页

```python
# examples/my_deck.py
from primitives import HEAD, FOOT, PAR, R

def build(deck):
    c, s = deck.theme.colors, deck.theme.size
    body = [
        HEAD(2, "OVERVIEW", "本季度我们做了什么", deck.theme.head),
        PAR(60, 230, 700, "第一段正文，可以用〔高亮〕标出重点。",
            size=s["body"], fill=c["ink"]),
        R(60, 300, 1160, 1, c["edge"]),
        FOOT(2, deck.theme.foot),
    ]
    deck.add_page("content", "\n".join(body), name="overview")
```

然后：

```powershell
python scripts/build.py --example my_deck --out build/my_deck.pptx
```

`build(deck)` 是唯一必须的入口，页面顺序即调用顺序。

## 主题

`themes/minimal-ink/theme.py` 是参考主题，它掌管：

| 键 | 含义 |
| --- | --- |
| `THEME.font` | 字体族名 + 用于测宽的常规/粗体字体文件 |
| `THEME.colors` | 色板（墨绿、纸白、金调） |
| `THEME.size` | 字号阶梯，从 `micro` 16 到 `display` 64 |
| `THEME.head` / `foot` | 页面框架的几何与配色 |
| `THEME.card` / `band` | `NOTECARD` / `BAND` 使用的区块样式 |
| `THEME.background()` | 渐变兜底，或整幅图片 + 压暗层 |

复制这个目录，改掉 `NAME`，调几个值，用 `--theme themes/你的主题` 传进去即可。**任何原语都不用改。**

## 自带主题

| 主题 | 观感 | 适合 |
| --- | --- | --- |
| `minimal-ink` | 暖白纸面、墨绿、金细线 | 汇报、学期小结，适合打印着看 |
| `guochao` | 近黑面板、三道同心金环、弧边内容面板、华文行楷的封面与章节页 | 品牌提案、文化类，适合在暗房间里投影 |

`guochao` 的标题字族是 `华文行楷`（STXINGKA）。没装就加 `--font-fallback`：
版式不会位移，只是笔画从「写」变成「印」。

## 背景图

`--bg-image photo.jpg` 会交给主题处理。图片在转换**之前**就用 PIL 按画布比例居中裁切（转换器对 `preserveAspectRatio` 支持有限），拷进 `images/`，铺在每一页最底层，再叠一层主题色压暗保证文字可读。

不传图片时主题自己画渐变。弧边面板是真实填充的 `<path>` 转成 `<a:custGeom>`，所以不依赖裁切，有没有照片背景观感一致。

## 转场

`--transition` 原样传给 `svg_to_pptx.py`（`circle`、`push`、`fade`、`wipe`、`cut` 等），`--transition-duration` 单位是秒。生成的 XML 把 `<p:transition>` 放在 `<p:clrMapOvr>` 之后、`<p:timing>` 之前，时长按毫秒写。

**LibreOffice 不渲染转场**，所以预览 PNG 里看不到。转场必须在 PowerPoint 里放映验收。

## 和其他 AI PPT 工具的区别

| | ppt-native | HTML→PPTX 类工具 | 截图转 PPT |
| --- | --- | --- | --- |
| 产出 | 原生形状 | 原生形状 | 一整张图 |
| 排版控制 | 逐 run 实测字宽 | 浏览器近似 | 无 |
| 文字可编辑 | 每一段都能改 | 大体可以 | 不行 |
| 换主题 | 改一个 Python 文件 | 重写 CSS | 不适用 |
| 中文长文案 | 内置 CJK 断行 | 取决于浏览器 | 无 |
| 转场 | PowerPoint 原生 | 通常没有 | 没有 |

## 仓库结构

```
ppt-native/
├── SKILL.md               # 给 AI 操作者看的说明
├── README.md
├── README.zh-CN.md        # 本文件
├── LICENSE                # MIT
├── requirements.txt
├── scripts/
│   ├── primitives.py      # 与主题无关的 SVG 原语
│   ├── deck.py            # Deck 模型 + 主题加载 + 素材导出
│   ├── build.py           # 一条命令跑完全程
│   ├── post_fix.py        # 把文本框加宽到实测宽度
│   └── render.py          # soffice → PDF → PNG
├── themes/minimal-ink/
│   ├── theme.py
│   └── README.md
├── examples/
│   └── demo_minimal.py    # 8 页虚构内容
└── docs/
    ├── PIPELINE.md
    └── PITFALLS.md
```

## 已知限制

- 流水线依赖本地一份 `ppt-master`（MIT）。它没有 vendored 进来；`build.py` 依次在 `--skill-dir`、`PPT_MASTER_SKILL`、`vendor/ppt-master`、`~/.dsh/skills/ppt-master` 里找。
- 字体文件默认指向 `C:\Windows\Fonts` 下的微软雅黑。换系统要改 `THEME.font`；文件缺失时测宽会退化成估算。
- 文字是按行排的（每个视觉行一个 SVG `<text>`）。行内混色用 `TR`/`MIX` 支持，但**没有**原生项目符号、表格、图表、SmartArt。
- 不会自动分页：一页放得下什么由作者决定。
- LibreOffice 的字体回退与 PowerPoint 可能略有差异，交付前务必在 PowerPoint 里打开一次。
- PNG 预览只反映静态版式（没有转场、没有动画）。

## 许可

MIT，见 `LICENSE`。

流水线在运行时会调用 MIT 协议的 `ppt-master` 转换器；本项目不修改、也不再分发它。

**一个可选的 AGPL 依赖。** `scripts/render.py` 生成预览图时，优先用
poppler-utils 里的 `pdftoppm`。如果机器上没有 poppler、但仍然想要 PNG 预览，
`requirements-render.txt` 会装上 PyMuPDF —— 它是 **AGPL-3.0**（或商业授权）。

之所以特意把它剔出默认依赖：默认那行 `pip install -r requirements.txt` 装出来的
是一棵 MIT 干净的依赖树；两者都缺时，构建会跳过预览渲染，不影响出片。

