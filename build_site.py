#!/usr/bin/env python3
"""
build_site.py - Generate all website assets for Grannie's Family Trees website.

Outputs:
  docs/
    svg/                -> Crisp vector SVGs for all 5 trees
    search_index.json   -> Normalized search index for name lookups & snap-to-person
    tiles/              -> Letter-size tiled PDFs for 1:1 scale home printing
"""

import os
import re
import json
import math
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, 'grannie family trees')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SVG_DIR = os.path.join(DOCS_DIR, 'svg')
TILES_DIR = os.path.join(DOCS_DIR, 'tiles')

os.makedirs(SVG_DIR, exist_ok=True)
os.makedirs(TILES_DIR, exist_ok=True)

TREE_SPECS = [
    {
        'id': '000059',
        'file': '000059_94254091rdg39966w5890t_A.pdf',
        'name': 'Close Family of Marion Parker Inglis',
        'subtitle': 'Marion Parker Inglis (b. Feb 2, 1909, Glasgow)',
        'description': 'Full close family branch spanning 6+ generations with 98+ family members across Scotland & North America.',
        'width_in': 62.7,
        'height_in': 46.0,
    },
    {
        'id': '000061',
        'file': '000061_762453ldc65q126fw5lv98_A.pdf',
        'name': 'Close Family of Thomas Kinlay Johnston',
        'subtitle': 'Thomas Kinlay Johnston (b. Jun 27, 1913, Fife)',
        'description': 'Comprehensive panoramic tree spanning 8+ generations with 200+ family members.',
        'width_in': 151.2,
        'height_in': 37.6,
    },
    {
        'id': '000067',
        'file': '000067_222401i6396f79e5bznd7b_A.pdf',
        'name': 'Ancestors of Marion Parker Inglis',
        'subtitle': 'Direct Ancestors of Marion Parker Inglis',
        'description': 'Direct ancestral lineage tracing backward through Inglis, Gallie, and Crawford lines.',
        'width_in': 54.4,
        'height_in': 39.3,
    },
    {
        'id': '000069',
        'file': '000069_011201c6d3z98f777bt629_A.pdf',
        'name': 'Ancestors of John Inglis',
        'subtitle': 'John Inglis (b. May 26, 1872, Roxburgh)',
        'description': 'Ancestral chart of John Inglis tracing paternal and maternal Scottish origins.',
        'width_in': 43.6,
        'height_in': 35.8,
    },
    {
        'id': '000071',
        'file': '000071_77048093bwa928agcd8b62_A.pdf',
        'name': 'Ancestors of Thomas Kinlay Johnston',
        'subtitle': 'Thomas Kinlay Johnston (b. Jun 27, 1913, Fife)',
        'description': 'Ancestral chart for Thomas Kinlay Johnston tracing the Johnston, Kinlay, and Mackie families.',
        'width_in': 40.9,
        'height_in': 27.7,
    },
]

def clean_text(s: str) -> str:
    """Clean OCR / PDF split text and whitespace."""
    s = s.replace('\n', ' ')
    s = re.sub(r'Scotl\s*and', 'Scotland', s, flags=re.I)
    s = re.sub(r'Col\s*umbia', 'Columbia', s, flags=re.I)
    s = re.sub(r'Kingl\s*assie', 'Kinglassie', s, flags=re.I)
    s = re.sub(r'Lochgel\s*l\s*y', 'Lochgelly', s, flags=re.I)
    s = re.sub(r'Gl\s*asgow', 'Glasgow', s, flags=re.I)
    s = re.sub(r'Lanarksh\s*ire', 'Lanarkshire', s, flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def export_svg(doc, tree_id, out_dir):
    """Export page 0 of document to SVG."""
    page = doc[0]
    svg_data = page.get_svg_image()
    out_path = os.path.join(out_dir, f'{tree_id}.svg')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_data)
    size_mb = len(svg_data) / (1024 * 1024)
    print(f"  [SVG] Generated {out_path} ({size_mb:.2f} MB)")
    return out_path

def extract_search_data(doc):
    """Extract persons with normalized coordinates from document."""
    page = doc[0]
    pw, ph = page.rect.width, page.rect.height
    text_dict = page.get_text('dict')

    name_spans = []
    detail_spans = []

    for block in text_dict['blocks']:
        if block['type'] == 0:
            for line in block['lines']:
                for span in line['spans']:
                    txt = span['text'].strip()
                    if not txt:
                        continue
                    if span['size'] > 20:
                        continue  # Skip title
                    # 9pt bold names
                    if abs(span['size'] - 9.0) < 0.6 and 'Bold' in span['font']:
                        name_spans.append({
                            'text': txt,
                            'bbox': span['bbox'],
                            'x': (span['bbox'][0] + span['bbox'][2]) / 2,
                            'y': span['bbox'][1],
                            'raw': span['bbox']
                        })
                    # 8.2pt details (birth, death, marriage)
                    elif abs(span['size'] - 8.2) < 0.6:
                        detail_spans.append({
                            'text': txt,
                            'bbox': span['bbox'],
                            'x': span['bbox'][0],
                            'y': span['bbox'][1]
                        })

    # Sort top-to-bottom, left-to-right
    name_spans.sort(key=lambda s: (s['y'], s['x']))
    merged_persons = []
    used = set()

    for i, n1 in enumerate(name_spans):
        if i in used:
            continue
        curr_text = [n1['text']]
        min_x = n1['raw'][0]
        max_x = n1['raw'][2]
        min_y = n1['raw'][1]
        max_y = n1['raw'][3]
        used.add(i)

        for j, n2 in enumerate(name_spans):
            if j in used:
                continue
            # Merge close spans belonging to same person's name (e.g. multi-line or split spans)
            x_close = abs(n1['x'] - n2['x']) < 60 or abs(n1['raw'][0] - n2['raw'][0]) < 35
            y_close = abs(n1['y'] - n2['y']) < 24
            if x_close and y_close:
                curr_text.append(n2['text'])
                min_x = min(min_x, n2['raw'][0])
                max_x = max(max_x, n2['raw'][2])
                min_y = min(min_y, n2['raw'][1])
                max_y = max(max_y, n2['raw'][3])
                used.add(j)

        full_name = clean_text(' '.join(curr_text))
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2

        # Collect detail lines beneath this person's name box
        person_details = []
        for ds in detail_spans:
            dx = ds['bbox'][0]
            dy = ds['bbox'][1]
            if abs(dx - min_x) < 80 and 0 <= (dy - max_y) < 140:
                person_details.append(ds['text'])

        detail_clean = clean_text(' '.join(person_details))

        merged_persons.append({
            'name': full_name,
            'details': detail_clean,
            'x': round(cx / pw, 5),
            'y': round(cy / ph, 5),
            'raw_x': round(cx, 1),
            'raw_y': round(cy, 1),
        })

    return merged_persons

def generate_printable_tiles(doc, tree_info, out_pdf_path):
    """Generate Letter landscape tiled PDF at 1:1 original scale with headers & grid info."""
    src_page = doc[0]

    LETTER_W = 792   # 11 inches in points (landscape)
    LETTER_H = 612   # 8.5 inches in points
    MARGIN = 36      # 0.5 inch margin
    HEADER_H = 24    # 24 pt header bar
    OVERLAP = 36     # 0.5 inch overlap between tiles

    usable_w = LETTER_W - 2 * MARGIN
    usable_h = LETTER_H - 2 * MARGIN - HEADER_H
    step_w = usable_w - OVERLAP
    step_h = usable_h - OVERLAP

    src_w = src_page.rect.width
    src_h = src_page.rect.height

    n_cols = math.ceil(src_w / step_w)
    n_rows = math.ceil(src_h / step_h)
    total_pages = n_cols * n_rows

    out = fitz.open()

    for row in range(n_rows):
        for col in range(n_cols):
            clip_x0 = col * step_w
            clip_y0 = row * step_h
            clip_x1 = min(clip_x0 + usable_w, src_w)
            clip_y1 = min(clip_y0 + usable_h, src_h)
            clip_rect = fitz.Rect(clip_x0, clip_y0, clip_x1, clip_y1)

            out_page = out.new_page(width=LETTER_W, height=LETTER_H)

            # Header background bar
            header_rect = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + HEADER_H)
            out_page.draw_rect(header_rect, color=(0.82, 0.82, 0.82), fill=(0.96, 0.96, 0.96))
            
            # Header text
            title_text = f"{tree_info['name']}   |   Tile: Column {col+1} of {n_cols}, Row {row+1} of {n_rows}  (Page {row*n_cols + col + 1}/{total_pages})"
            out_page.insert_text(fitz.Point(MARGIN + 8, MARGIN + HEADER_H - 7), title_text, fontsize=8.5, color=(0.2, 0.2, 0.2))

            # Tile drawing area
            dest_w = clip_x1 - clip_x0
            dest_h = clip_y1 - clip_y0
            dest_rect = fitz.Rect(
                MARGIN, MARGIN + HEADER_H,
                MARGIN + dest_w,
                MARGIN + HEADER_H + dest_h
            )

            # Copy vector content from original PDF
            out_page.show_pdf_page(dest_rect, doc, 0, clip=clip_rect)

            # Border around tile
            out_page.draw_rect(dest_rect, color=(0.75, 0.75, 0.75), width=0.5)

    out.save(out_pdf_path)
    size_mb = os.path.getsize(out_pdf_path) / (1024 * 1024)
    print(f"  [TILES] Generated {out_pdf_path} ({total_pages} pages, {n_cols}×{n_rows} grid, {size_mb:.2f} MB)")
    return total_pages

def main():
    print("=== Building Grannie's Family Tree Website Assets ===")
    
    search_index = {}
    tree_metadata = []

    for spec in TREE_SPECS:
        tree_id = spec['id']
        pdf_path = os.path.join(PDF_DIR, spec['file'])
        print(f"\nProcessing {tree_id}: {spec['name']}...")
        
        doc = fitz.open(pdf_path)
        page = doc[0]
        pw, ph = page.rect.width, page.rect.height

        # 1. Export SVG
        export_svg(doc, tree_id, SVG_DIR)

        # 2. Extract Persons & Coordinates
        persons = extract_search_data(doc)
        search_index[tree_id] = persons
        print(f"  [INDEX] Indexed {len(persons)} persons")

        # 3. Generate Printable Tiled PDF
        tiles_out_path = os.path.join(TILES_DIR, f"{tree_id}_printable_tiles.pdf")
        page_count = generate_printable_tiles(doc, spec, tiles_out_path)

        tree_metadata.append({
            'id': tree_id,
            'name': spec['name'],
            'subtitle': spec['subtitle'],
            'description': spec['description'],
            'width_in': spec['width_in'],
            'height_in': spec['height_in'],
            'svg_width_pt': pw,
            'svg_height_pt': ph,
            'person_count': len(persons),
            'tile_pages': page_count,
            'tile_pdf': f"tiles/{tree_id}_printable_tiles.pdf",
            'svg_file': f"svg/{tree_id}.svg"
        })

    # Save search index
    search_index_path = os.path.join(DOCS_DIR, 'search_index.json')
    with open(search_index_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, separators=(',', ':'))
    print(f"\n[OK] Saved search index to {search_index_path}")

    # Save trees metadata
    meta_path = os.path.join(DOCS_DIR, 'trees_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(tree_metadata, f, indent=2)
    print(f"[OK] Saved trees metadata to {meta_path}")
    print("\n=== Build Completed Successfully! ===")

if __name__ == '__main__':
    main()
