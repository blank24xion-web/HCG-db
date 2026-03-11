#!/usr/bin/env python3
"""
Hololive OCG Card Database Parser
Extracts card data + images from downloaded XLSX files.
Usage: python parse_hololive_xlsx.py <file1.xlsx> [file2.xlsx ...] -o cards.json
"""
import zipfile, json, base64, sys, os, argparse
import xml.etree.ElementTree as ET

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
XDR = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'

def parse_xlsx(path):
    cards = []
    with zipfile.ZipFile(path, 'r') as z:
        files = z.namelist()

        # Shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in files:
            ss_root = ET.fromstring(z.read('xl/sharedStrings.xml').decode())
            for si in ss_root.findall(f'{{{NS}}}si'):
                text = ''.join(t.text or '' for t in si.iter(f'{{{NS}}}t'))
                shared_strings.append(text)

        # Sheet data
        sheet_xml = None
        for f in files:
            if f.startswith('xl/worksheets/sheet') and f.endswith('.xml'):
                sheet_xml = f
                break
        if not sheet_xml:
            print(f"  WARNING: No sheet found in {path}")
            return cards

        sheet_root = ET.fromstring(z.read(sheet_xml).decode())
        rows_data = {}
        for row in sheet_root.findall(f'.//{{{NS}}}row'):
            row_num = int(row.get('r'))
            row_data = {}
            for cell in row.findall(f'{{{NS}}}c'):
                ref = cell.get('r')
                col = ''.join(c for c in ref if c.isalpha())
                cell_type = cell.get('t', '')
                v = cell.find(f'{{{NS}}}v')
                if v is not None and v.text:
                    row_data[col] = shared_strings[int(v.text)] if cell_type == 's' else v.text
            rows_data[row_num] = row_data

        # Image mapping
        row_to_main_img = {}
        row_to_alt_img = {}

        drawing_xml_path = None
        drawing_rels_path = None
        for f in files:
            if 'drawings/drawing' in f and f.endswith('.xml') and '_rels' not in f:
                drawing_xml_path = f
                base = f.replace('xl/drawings/', '').replace('.xml', '')
                drawing_rels_path = f'xl/drawings/_rels/{base}.xml.rels'
                break

        if drawing_xml_path and drawing_rels_path and drawing_rels_path in files:
            rels_root = ET.fromstring(z.read(drawing_rels_path).decode())
            rid_to_image = {
                r.get('Id'): r.get('Target').replace('../media/', '')
                for r in rels_root.findall(f'{{{PKG_NS}}}Relationship')
            }

            draw_root = ET.fromstring(z.read(drawing_xml_path).decode())
            for anchor in draw_root.findall(f'{{{XDR}}}oneCellAnchor'):
                from_elem = anchor.find(f'{{{XDR}}}from')
                col = int(from_elem.find(f'{{{XDR}}}col').text)
                draw_row = int(from_elem.find(f'{{{XDR}}}row').text)
                sheet_row = draw_row + 1
                pic = anchor.find(f'{{{XDR}}}pic')
                if pic is not None:
                    blip = pic.find(f'.//{{{A_NS}}}blip')
                    if blip is not None:
                        rid = blip.get(f'{{{R_NS}}}embed')
                        img_file = rid_to_image.get(rid, '')
                        media_path = f'xl/media/{img_file}'
                        if media_path in files:
                            img_data = base64.b64encode(z.read(media_path)).decode()
                            if col == 2:
                                row_to_main_img[sheet_row] = img_data
                            elif col == 9:
                                row_to_alt_img[sheet_row] = img_data

        # Build cards
        for row_num in sorted(rows_data.keys()):
            if row_num == 1:
                continue
            r = rows_data[row_num]
            if not r.get('A'):
                continue
            card = {
                'setcode': r.get('A', ''),
                'name': r.get('B', ''),
                'type': r.get('D', ''),
                'rarity': r.get('E', ''),
                'color': r.get('F', ''),
                'life_hp': r.get('G', ''),
                'tags': r.get('H', ''),
                'text': r.get('I', ''),
                'image': row_to_main_img.get(row_num),
                'alt_image': row_to_alt_img.get(row_num),
            }
            cards.append(card)

    return cards


def main():
    parser = argparse.ArgumentParser(description='Parse Hololive OCG XLSX files into card database JSON')
    parser.add_argument('files', nargs='+', help='XLSX files to parse')
    parser.add_argument('-o', '--output', default='cards.json', help='Output JSON file (default: cards.json)')
    args = parser.parse_args()

    all_cards = []
    for f in args.files:
        if not os.path.exists(f):
            print(f"ERROR: File not found: {f}")
            continue
        print(f"Parsing {f}...")
        cards = parse_xlsx(f)
        print(f"  -> {len(cards)} cards extracted")
        all_cards.extend(cards)

    # Deduplicate by setcode
    seen = set()
    deduped = []
    for c in all_cards:
        if c['setcode'] not in seen:
            seen.add(c['setcode'])
            deduped.append(c)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(deduped, f, ensure_ascii=False)

    print(f"\nDone! {len(deduped)} total cards saved to {args.output}")
    if len(all_cards) != len(deduped):
        print(f"  ({len(all_cards) - len(deduped)} duplicates removed)")


if __name__ == '__main__':
    main()
