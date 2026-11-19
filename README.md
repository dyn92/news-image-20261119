# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/dyn92/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/dyn92/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

[make.fun](https://make.fun) · [Bounty: news-image-20261119](https://make.fun/bounty/news-image-20261119) · $250 in USDC

A small pure-Python program that draws one 1024x1024 newspaper poster for Thursday 19 November 2026: a dated navy header plus six panels, one per story — GTA VI launching into Vice City after a 13-year wait, Trump, Xi and Putin holding trilateral talks in Shenzhen at the APEC summit, US and Iranian strikes widening across the Gulf, the EU proposing a 45 billion euro loan for Ukraine, NASA's Voyager 1 reaching a light-day from Earth, and Cyclone Akvan bearing down on India's east coast. Each panel has a hand-drawn pictogram (Vice City skyline and palm, three leaders at a table under three flags, explosion over Gulf waves, EU star ring around a 45BN coin, deep-space probe, cyclone spiral with a leaning palm), a headline and one factual sub-label.

Everything is drawn from scratch with the standard library only (`math`, `os`, `struct`, `zlib`): its own RGB canvas, its own 5x7 bitmap font, and its own PNG encoder. No network, no third-party packages, and the output is byte-identical on every run.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, under 1 MiB).

Entered on make.fun — "Sum up 19 November's world news in one image", $250 in USDC.
