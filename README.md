# PixelAura 🎨

> Premium AI-generated wallpapers for phones, desktops, and tablets.

## Live Site

🌐 **[View on GitHub Pages](https://YOUR-USERNAME.github.io/PixelAura)**

---

## How It Works

```
GitHub Actions runs daily at 6:00 AM IST
        ↓
python ai_engine/run.py
        ↓
10 new AI wallpapers generated via Pollinations
        ↓
wallpapers.json updated automatically
        ↓
Committed back to repo
        ↓
GitHub Pages re-deploys → site is updated
```

## Project Structure

```
PixelAura/
├── ai_engine/          ← Python automation engine
│   ├── run.py          ← Main entry point
│   ├── config.py       ← Settings (.env driven)
│   ├── prompt_generator.py
│   ├── job_queue.py
│   ├── image_manager.py
│   ├── website_updater.py
│   ├── providers/
│   │   └── pollinations_provider.py
│   ├── prompts/        ← Vocabulary files
│   └── history/        ← Job tracking (prompts.json)
│
└── website/            ← Static site (served by GitHub Pages)
    ├── index.html
    ├── css/style.css
    ├── js/app.js
    ├── data/wallpapers.json   ← Auto-generated
    └── assets/images/generated/   ← Auto-generated PNGs
```

## Run Locally

```bash
# Generate new wallpapers
cd ai_engine
python run.py

# Serve website
cd ../website
python -m http.server 8080
# → Open http://localhost:8080
```

## Built By

**Vijender Kumar** — [Instagram](https://www.instagram.com/itz_vijender1/) · [LinkedIn](https://www.linkedin.com/in/vijenderkumar15/) · [YouTube](https://www.youtube.com/@TinyTales-41)
