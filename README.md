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
| glyphs whose counters close (fewer than the designer's), 412 glyphs | 18.4 % | 22.1 % |
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

`propbold` (0.2.0) applies the same rule outside Glyphs, on Windows, macOS and Linux: `.glyphs` in → same file with a new master appended, `.ufo` → new UFO, `.otf`/`.ttf` → new TrueType font. `propbold-compare` measures a plugin-made master against the CLI's output.

    pip install "git+https://github.com/fanzhixiang777/ProportionalBold.git#subdirectory=propbold-cli"
    propbold NotoSansCJKtc-Regular.otf --ratio 1.45

Windows 11 install of the TTF output was verified with 0.1.2; re-verification of 0.2.0 is pending ([propbold-cli/WINDOWS_CHECK.md](propbold-cli/WINDOWS_CHECK.md)). Details: [propbold-cli/README.md](propbold-cli/README.md).

## Service

If you would rather not run it yourself: send a Regular master and I return the Bold or Black draft master prepared with this tool, checked glyph by glyph against the numbers above. NT$20,000 per weight set. A 50-glyph sample comes first, free, so you can judge it by eye before paying. Write to proportionalbold@gmail.com.

不想自己跑也可以：把 Regular 母版寄來，我用這套工具做出 Bold 或 Black 的草稿母版，並依上面的數據逐字檢查後交回。每一套字重 NT$20,000。先免費做 50 個字的樣本，你親眼看過再決定要不要付費。來信 proportionalbold@gmail.com。

ご自身で実行されない場合はこちらへ。Regular マスターをお送りいただければ、このツールで Bold または Black の下書きマスターを作成し、上記の数値に照らして一字ずつ確認してお返しします。ウェイト一式につき NT$20,000 です。まず 50 字のサンプルを無料でお作りしますので、目でご確認のうえご判断ください。連絡先は proportionalbold@gmail.com。

## License

MIT. Test data: Noto Sans CJK (SIL Open Font License).
