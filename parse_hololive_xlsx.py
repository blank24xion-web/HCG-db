#!/usr/bin/env python3
"""
Hololive OCG Card Database Parser
==================================
Extracts card data + images from downloaded XLSX files and builds
the card database (cards.json + images/) used by the web app.

REQUIREMENTS
------------
Python 3.8+  (usually pre-installed on Mac; download from python.org on Windows)
Pillow       (install once with:  pip install Pillow)

HOW TO USE
----------
1. Open a terminal / command prompt and navigate to your repo folder:

   Windows:
       cd C:/Users/YourName/Documents/hololive-ocg

   Mac:
       cd ~/Documents/hololive-ocg

2. Run the parser pointing at your XLSX files:

   Single file:
       python parse_hololive_xlsx.py hBP01_Part1.xlsx

   Multiple parts (merged + deduplicated automatically):
       python parse_hololive_xlsx.py hBP01_Part1.xlsx hBP01_Part2.xlsx hBP01_Part3.xlsx

   Multiple sets at once:
       python parse_hololive_xlsx.py hBP01_Part1.xlsx hBP01_Part2.xlsx hBP02_Part1.xlsx

   All files in a subfolder (Mac/Linux):
       python parse_hololive_xlsx.py source_sheets/*.xlsx

3. The script outputs:
       cards.json    all card text data, image paths, visual fingerprints
       images/       compressed card images (~50-100KB each as JPEGs)

4. Open GitHub Desktop, commit all changed files, and push.
   Your live site updates within ~2 minutes.

ADDING NEW SETS LATER
---------------------
Always pass ALL your XLSX files together each time you run.
Duplicates are removed automatically so mixing old and new is safe.

Best practice: keep every downloaded XLSX in a subfolder called source_sheets/
inside your repo so you can always rebuild the full database from scratch.

   Windows (use ^ to wrap long commands):
       python parse_hololive_xlsx.py source_sheets/hBP01_Part1.xlsx ^
                                     source_sheets/hBP01_Part2.xlsx ^
                                     source_sheets/hBP02_Part1.xlsx

   Mac/Linux (use backslash to wrap):
       python parse_hololive_xlsx.py source_sheets/hBP01_Part1.xlsx \
                                     source_sheets/hBP01_Part2.xlsx \
                                     source_sheets/hBP02_Part1.xlsx

OPTIONS
-------
  -o FILE        output JSON file  (default: cards.json)
  -d DIR         output images dir (default: images)
  --no-compress  skip compression, keep original PNG quality
"""

import zipfile, json, sys, os, argparse, math
import xml.etree.ElementTree as ET

NS     = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
XDR    = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A_NS   = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R_NS   = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'


def compute_phash(img, hash_size=8):
    dct_size = hash_size * 4
    small    = img.convert('L').resize((dct_size, dct_size))
    pixels   = list(small.getdata())

    def dct_1d(row):
        n = len(row)
        return [
            sum(row[i] * math.cos(math.pi * k * (2*i+1) / (2*n)) for i in range(n))
            * (math.sqrt(1/n) if k == 0 else math.sqrt(2/n))
            for k in range(n)
        ]

    matrix   = [pixels[i*dct_size:(i+1)*dct_size] for i in range(dct_size)]
    dct_rows = [dct_1d(row) for row in matrix]
    dct_cols = [dct_1d([dct_rows[r][c] for r in range(dct_size)]) for c in range(dct_size)]
    dct_low  = [dct_cols[c][r] for r in range(hash_size) for c in range(hash_size)]
    median   = sorted(dct_low)[len(dct_low) // 2]
    bits     = [1 if v > median else 0 for v in dct_low]
    return ''.join(
        format(sum(bits[i+j] << (3-j) for j in range(4) if i+j < len(bits)), 'x')
        for i in range(0, len(bits), 4)
    )


def parse_xlsx(path):
    cards = []
    with zipfile.ZipFile(path, 'r') as z:
        files = z.namelist()

        shared_strings = []
        if 'xl/sharedStrings.xml' in files:
            ss_root = ET.fromstring(z.read('xl/sharedStrings.xml').decode())
            for si in ss_root.findall(f'{{{NS}}}si'):
                text = ''.join(t.text or '' for t in si.iter(f'{{{NS}}}t'))
                shared_strings.append(text)

        sheet_xml = next(
            (f for f in files if f.startswith('xl/worksheets/sheet') and f.endswith('.xml')), None)
        if not sheet_xml:
            print(f"  WARNING: No sheet found in {path}")
            return cards

        sheet_root = ET.fromstring(z.read(sheet_xml).decode())
        rows_data  = {}
        for row in sheet_root.findall(f'.//{{{NS}}}row'):
            rn = int(row.get('r'))
            rd = {}
            for cell in row.findall(f'{{{NS}}}c'):
                col = ''.join(c for c in cell.get('r') if c.isalpha())
                v   = cell.find(f'{{{NS}}}v')
                if v is not None and v.text:
                    rd[col] = shared_strings[int(v.text)] if cell.get('t','') == 's' else v.text
            rows_data[rn] = rd

        row_to_main = {}
        row_to_alt  = {}
        drw = next((f for f in files if 'drawings/drawing' in f and f.endswith('.xml') and '_rels' not in f), None)
        if drw:
            rels_path = drw.replace('xl/drawings/', 'xl/drawings/_rels/').replace('.xml', '.xml.rels')
            if rels_path in files:
                rid_map = {r.get('Id'): r.get('Target').replace('../media/', '')
                           for r in ET.fromstring(z.read(rels_path).decode())
                               .findall(f'{{{PKG_NS}}}Relationship')}
                for anc in ET.fromstring(z.read(drw).decode()).findall(f'{{{XDR}}}oneCellAnchor'):
                    fe  = anc.find(f'{{{XDR}}}from')
                    col = int(fe.find(f'{{{XDR}}}col').text)
                    srow= int(fe.find(f'{{{XDR}}}row').text) + 1
                    pic = anc.find(f'{{{XDR}}}pic')
                    if pic is not None:
                        blip = pic.find(f'.//{{{A_NS}}}blip')
                        if blip is not None:
                            mp = f'xl/media/{rid_map.get(blip.get(f"{{{R_NS}}}embed",""), "")}'
                            if mp in files:
                                if col == 2: row_to_main[srow] = z.read(mp)
                                elif col == 9: row_to_alt[srow] = z.read(mp)

        for rn in sorted(rows_data.keys()):
            if rn == 1: continue
            r = rows_data[rn]
            if not r.get('A'): continue
            cards.append({
                'setcode': r.get('A',''), 'name':    r.get('B',''),
                'type':    r.get('D',''), 'rarity':  r.get('E',''),
                'color':   r.get('F',''), 'life_hp': r.get('G',''),
                'tags':    r.get('H',''), 'text':    r.get('I',''),
                '_img':    row_to_main.get(rn), '_alt': row_to_alt.get(rn),
            })
    return cards


def save_img(img_bytes, out_path, compress):
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    ph  = compute_phash(img)
    if compress:
        w, h = img.size
        if w > 380: img = img.resize((380, int(h*380/w)), Image.LANCZOS)
        img.save(out_path, 'JPEG', quality=82, optimize=True)
    else:
        img.save(out_path)
    return ph


def main():
    ap = argparse.ArgumentParser(description='Parse Hololive OCG XLSX -> card database',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('files', nargs='+')
    ap.add_argument('-o', '--output',  default='cards.json')
    ap.add_argument('-d', '--img-dir', default='images')
    ap.add_argument('--no-compress',   action='store_true')
    args = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow not installed. Run:  pip install Pillow"); sys.exit(1)

    os.makedirs(args.img_dir, exist_ok=True)
    compress = not args.no_compress
    ext      = '.jpg' if compress else '.png'

    all_cards = []
    for f in args.files:
        if not os.path.exists(f):
            print(f"ERROR: Not found: {f}"); continue
        print(f"Parsing {f}...")
        cards = parse_xlsx(f)
        print(f"  -> {len(cards)} cards")
        all_cards.extend(cards)

    if not all_cards:
        print("No cards found."); sys.exit(1)

    seen, deduped = set(), []
    for c in all_cards:
        if c['setcode'] not in seen:
            seen.add(c['setcode']); deduped.append(c)
    if len(all_cards) != len(deduped):
        print(f"Skipped {len(all_cards)-len(deduped)} duplicates")

    print("\nProcessing images...")
    final, img_count = [], 0

    for card in deduped:
        main_b = card.pop('_img',  None)
        alt_b  = card.pop('_alt',  None)
        card.update({'image': None, 'alt_image': None, 'phash': None, 'alt_phash': None})

        if main_b:
            p = os.path.join(args.img_dir, f"{card['setcode']}{ext}")
            try:
                card['phash'] = save_img(main_b, p, compress)
                card['image'] = p.replace('\\', '/'); img_count += 1
            except Exception as e:
                print(f"  WARNING {card['setcode']}: {e}")

        if alt_b:
            p = os.path.join(args.img_dir, f"{card['setcode']}_alt{ext}")
            try:
                card['alt_phash'] = save_img(alt_b, p, compress)
                card['alt_image'] = p.replace('\\', '/'); img_count += 1
            except Exception as e:
                print(f"  WARNING {card['setcode']} alt: {e}")

        final.append(card)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"\n✓  {len(final)} cards  ->  {args.output}")
    print(f"   {img_count} images  ->  {args.img_dir}/")
    print(f"\nNext: open GitHub Desktop, commit all changes, and push.")

if __name__ == '__main__':
    main()
