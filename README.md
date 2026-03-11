# hololive OCG Card Database

A self-hosted card database and translation reference for the hololive OCG (Japanese version). Search cards by name, type, color, tag, rarity, or set. Includes a live camera scanner to identify cards.

---

## Live Site

Once deployed: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

---

## File Structure

```
your-repo/
├── index.html              ← The web app (all UI, search, scanner)
├── cards.json              ← Card database (text data only, no images)
├── images/
│   ├── hBP01-001.jpg       ← Standard card art
│   ├── hBP01-001_alt.jpg   ← Alternate art (if exists)
│   └── ...
├── parse_hololive_xlsx.py  ← Parser script (run locally to update database)
└── README.md
```

---

## One-Time Setup

### 1. Install requirements (first time only)

You need Python 3 and Pillow:

```bash
pip install Pillow
```

### 2. Install GitHub Desktop

Download from https://desktop.github.com and sign in with your GitHub account.

### 3. Clone your repository

- Open GitHub Desktop
- File → Clone Repository
- Choose your repo and pick a local folder (e.g. `Documents/hololive-ocg`)
- Click **Clone**

You now have a local copy of the repo on your computer that syncs to GitHub.

---

## How to Add a New Set (or Finish a Partial Set)

### Step 1: Download the XLSX from the community Google Sheet

- Open the community Google Sheet
- Navigate to the sheet for the set you want (e.g. hBP02)
- If the sheet is too large, split it into parts manually (select rows, copy to a new sheet, download each)
- File → Download → Microsoft Excel (.xlsx)
- Repeat for each part

### Step 2: Run the parser

Open a terminal (Command Prompt on Windows, Terminal on Mac) and navigate to your local repo folder:

```bash
cd path/to/your/repo
```

Run the parser with all your XLSX files:

```bash
# Single set
python parse_hololive_xlsx.py hBP02_Part1.xlsx -o cards.json

# Multiple parts — merges automatically, removes duplicates
python parse_hololive_xlsx.py hBP02_Part1.xlsx hBP02_Part2.xlsx hBP02_Part3.xlsx -o cards.json

# Adding a new set ON TOP of existing cards (pass old cards.json as well? No — just pass all XLSX files together)
# Best practice: keep all your XLSX files in a folder called "source_sheets/"
python parse_hololive_xlsx.py source_sheets/*.xlsx -o cards.json
```

The script will:
- Extract all card text, types, colors, tags, rarities
- Extract all card images (standard + alt art)
- Compress images automatically (~90% size reduction)
- Save everything to `cards.json` and the `images/` folder
- Skip duplicate setcodes automatically

### Step 3: Push to GitHub

- Open **GitHub Desktop**
- You'll see all the changed/new files listed on the left
- Write a short summary in the bottom left (e.g. "Add hBP02")
- Click **Commit to main**
- Click **Push origin** (top right)

GitHub Pages will update automatically within 1–2 minutes.

---

## How the App Works

- **Filters** are built dynamically — any new card type, tag, color, or set in the database automatically gets a filter button. No code changes needed.
- **Search** checks card name (JP + EN), setcode, card text, tags, and type simultaneously.
- **Scanner** opens a live camera feed. Tap 📷 to capture a frame. It runs OCR and tries to match either the setcode (most reliable — e.g. `hBP01-042`) or the English card name. On a match it opens the card detail directly.

### Scanner tips
- Setcodes (e.g. `hBP01-042`) are the most reliable thing to point at — they're unambiguous
- Good lighting makes a big difference
- Hold the card steady when you tap capture
- Works in Safari on iPhone — no app install needed

---

## Troubleshooting

**Images not showing after deploy**
- Make sure the `images/` folder was committed and pushed (GitHub Desktop should show them as new files)
- GitHub Pages can take a few minutes to process a large batch of new files

**Parser says "No sheet found"**
- The XLSX might have a different internal structure. Try re-downloading it from Google Sheets

**Cards missing from a part**
- Check that the Google Sheet rows weren't hidden — hidden rows won't export

**File too large to upload via GitHub web interface**
- Always use GitHub Desktop for pushes — it has no file size limit (individual files just need to be under 100MB, which card images never will be)

---

## Credits

Card translations by the hololive OCG community.
App built with plain HTML/JS + Tesseract.js for OCR.
