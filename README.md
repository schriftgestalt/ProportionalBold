# Proportional Bold → New Master

A Glyphs 3 and Glyphs 4 plugin. You give it one number — the target stem ratio — and it adds a **new master** to your font in which every glyph is emboldened in proportion to its own stem width. What you get is a **draft** for a Bold or Black master, not a finished weight.

![Regular, single Offset Curve, Proportional Bold, designer's Bold — eight dense glyphs](docs/before-after.png)

Rows: the Regular master; Filter > Offset Curve with one value for the whole font; this plugin at ratio 1.45 (its actual output); the designer-drawn Bold of Noto Sans CJK TC for reference.

## Why

`Filter > Offset Curve` adds the same amount to every glyph. A CJK Regular master already carries a stroke hierarchy — in Noto Sans CJK TC the stem of 一 is 82 units, the stem of 灣 is 46 — so one constant makes dense glyphs relatively much bolder and closes their counters. This plugin measures each glyph's stem on scan lines and offsets it by `(ratio − 1) / 2 × its own stem`, using Glyphs' own Offset Curve engine. The rule is old (Sharp 1998, Canon 1993 patents, both expired); the plugin only puts it into the font editor.

## What it is worth, measured

Real plugin output, Noto Sans CJK TC Regular → ratio 1.45, compared with the designer-drawn Bold ([run 35503951963](mac/results/35503951963/)):

| | this plugin | one Offset Curve value |
|---|---|---|
| IoU against the designer's Bold, 412 glyphs | 0.831 | 0.829 |
| glyphs with a counter closed that the designer kept open, 412 glyphs | 18.4 % | 22.1 % |
| same, 318 CJK ideographs | 23.9 % | 28.6 % |

So: the same overall fit as a single offset, and roughly one in six fewer dense glyphs with a closed counter. Nothing stronger than that. The designer still redraws junctions, re-spaces strokes and fixes every dense glyph by hand; this saves the first pass.

## Install

- Plugin Manager: once the plugin is listed, install it from *Window > Plugin Manager*.
- Manual: copy `ProportionalBold.glyphsPlugin` to `~/Library/Application Support/Glyphs 3/Plugins/` (or `Glyphs 4/Plugins/`) and restart Glyphs.
- It needs the Python module from *Window > Plugin Manager > Modules*: Glyphs 3 uses its Python 3.11 module, Glyphs 4 its Python 3.14 module (both verified below). No other module.

## Use

Select the master you want to embolden, then *Filter > Proportional Bold → New Master…*, enter the ratio (Bold ≈ 1.45, Black ≈ 1.75, measured on Noto Sans CJK), *Create Master*. A master named `<current> PropBold <ratio>` is appended; components are decomposed in it; each new layer stores `userData["proportionalBold"]` with the measured stem and offset. Glyphs with no measurable stem (dots, tiny marks) get the font's median stem and are listed in the report. Creating a master is not undoable — delete it in Font Info if you change your mind.

## Verified on

Glyphs 3.5 (build 3532) and Glyphs 4.1 (build 4107), on GitHub Actions macOS runners, headless and in the GUI: plugin loads, menu item present, 413 of 415 test glyphs emboldened, 1 fallback, 0 failures, output identical between the two versions and equal to the command-line tool to IoU 0.994. Logs and numbers: [mac/results/](mac/results/).

## Known limits

- Glyphs with fewer than six ink runs on the scan lines (dots, tiny marks) get the median stem, not their own.
- Sharp diagonal tips (撇, 捺) come out shorter than the command-line tool's, which uses a different offset engine; area agrees to 1 %.
- Dense glyphs still need hand work; junctions are not treated.
- About 13–17 minutes for 65,535 glyphs on a 3-core runner.

## Command line

`propbold` (0.2.0) applies the same rule outside Glyphs, on Windows, macOS and Linux: `.glyphs` in → same file with a new master appended, `.ufo` → new UFO, `.otf`/`.ttf` → new TrueType font. `propbold-compare` measures a plugin-made master against the CLI's output, and `--report` writes the hand-work list (counters lost, fallback stems) without any reference weight.

    pip install "git+https://github.com/fanzhixiang777/ProportionalBold.git#subdirectory=propbold-cli"
    propbold NotoSansCJKtc-Regular.otf --ratio 1.45

TTF output verified on Windows 11 (2026-09-20, propbold 0.2.0: 65,535 glyphs in 541 s, ots clean, installs, listed and rendered in Word — [mac/results/windows-0.2.0.md](mac/results/windows-0.2.0.md)). Details: [propbold-cli/README.md](propbold-cli/README.md).

## Service

If you would rather not run it yourself: send a Regular master and I return the Bold or Black draft master made with this tool, plus a report listing every glyph that lost a counter or used the fallback stem, so you know where to start by hand. NT$20,000 (about US$620) per weight set. A free sample of 50 glyphs of your choice comes first, so you can judge it by eye before paying. Your files are used only for this job and deleted after delivery. Write to proportionalbold@gmail.com.

不想自己跑也可以：把 Regular 母版寄來，我用這套工具做出 Bold 或 Black 的草稿母版交回，並附一份清單，列出 counter 被封死或改用替代筆寬的每一個字，讓你知道從哪裡開始手修。每一套字重 NT$20,000（約 US$620）。先免費做你挑的 50 個字當樣本，親眼看過再決定要不要付費。你的檔案只用於這件工作，交件後刪除。來信 proportionalbold@gmail.com。

ご自身で実行されない場合は、Regular マスターをお送りいただければ、このツールで作成した Bold または Black の下書きマスターと、カウンターが閉じたグリフや代替ステム幅を使ったグリフをすべて列挙したレポートをお返しします — どこから手作業を始めるべきかが分かります。ウェイト一式につき NT$20,000（約 US$620）です。まず、お選びいただいた 50 字のサンプルを無料でお作りしますので、目でご確認のうえお支払いをご判断ください。お預かりしたファイルはこの作業にのみ使用し、納品後に削除します。連絡先は proportionalbold@gmail.com です。

The report is `propbold-compare --report`; an example from the verification run: [docs/report-example.txt](docs/report-example.txt).

## License

MIT. Test data: Noto Sans CJK (SIL Open Font License).
