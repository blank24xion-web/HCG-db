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
- Navigate to the tab for the set you want (e.g. hBP02)
- If the sheet is too large to download in one go, split it manually by selecting rows, copying to a new sheet, and downloading each part separately
- File → Download → Microsoft Excel (.xlsx)
- Save each part into a `source_sheets/` folder inside your repo

### Step 2: Run the parser

Open a terminal and navigate to your repo folder:

**Windows (Command Prompt):**
```
cd C:/Users/YourName/Documents/hololive-ocg
```

**Mac (Terminal):**
```
cd ~/Documents/hololive-ocg
```

Then run the parser with your XLSX files:

```bash
# Single file
python parse_hololive_xlsx.py source_sheets/hBP02_Part1.xlsx

# Multiple parts of one set (merged + deduplicated automatically)
python parse_hololive_xlsx.py source_sheets/hBP02_Part1.xlsx source_sheets/hBP02_Part2.xlsx

# Multiple sets at once — always pass ALL your files together
python parse_hololive_xlsx.py source_sheets/hBP01_Part1.xlsx source_sheets/hBP01_Part2.xlsx source_sheets/hBP02_Part1.xlsx source_sheets/hBP02_Part2.xlsx
```

The script outputs:
- `cards.json` — all card text data, image paths, and visual fingerprints for the scanner
- `images/` — compressed card images (~50–100KB each)

### Step 3: Push to GitHub

- Open **GitHub Desktop**
- You'll see the updated `cards.json` and any new images listed as changes
- Write a short summary (e.g. "Add hBP02")
- Click **Commit to main** → **Push origin**

Your live site updates within ~2 minutes.

---

## How the App Works

- **Filters** are built dynamically — any new card type, tag, color, or set in the database automatically gets a filter button. No code changes needed.
- **Search** checks card name (JP + EN), setcode, card text, tags, and type simultaneously.
- **Scanner** opens a live camera feed. Tap 📷 to capture a frame. It matches the card art visually using a perceptual fingerprint — no text reading needed. On a confident match it opens the card detail directly.

### Scanner tips
- Aim at the **card art** so it fills most of the viewfinder — the scanner matches by visual appearance, not text
- Good, even lighting with no glare gives the best results
- Hold the card steady when you tap capture — motion blur will hurt accuracy
- Works in Safari on iPhone — no app install needed
- The scanner compares the camera frame against every card's stored visual fingerprint (perceptual hash) and finds the closest match

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
