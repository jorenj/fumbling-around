#!/usr/bin/env python3
"""
build_site.py - Generate all website assets for Grannie's Family Trees website.

Layout & Printing specs:
  - 0.25" physical margins (18 pt) for maximum printable area per letter sheet.
  - 0.25" overlap (18 pt) matching the 0.25" margin for natural shingle layering.
  - Clean Bottom and Right edges (free of text/labels) for seamless shingle overlapping.
  - Pure crisp white background (ink-saving, zero background tint).
  - Page 1 Master Assembly Guide Sheet with complete visual grid map.
  - Prominent Tile Identifiers (e.g. [ TILE B-3 ]) in the top header bar.
  - Automatic elimination of empty whitespace tiles (saves 35-50% paper).
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

def make_background_white_and_remove_frame(doc):
    """
    1. Replace parchment background fill with pure white (1 1 1 rg) to save ink.
    2. Eliminate outer decorative poster frame border (/form1 Do) for clean borderless prints.
    """
    page = doc[0]
    for xref in page.get_contents():
        stream = doc.xref_stream(xref).decode('latin1')
        # Pure white background
        stream_mod = re.sub(r'\.949\s+\.949\s+\.937\s+rg', '1 1 1 rg', stream)
        # Eliminate outer frame border
        stream_mod = re.sub(r'/[Ff]orm\d+\s+Do', '          ', stream_mod)
        doc.update_stream(xref, stream_mod.encode('latin1'))

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

def get_col_letter(col_idx: int) -> str:
    """Convert column index (0-based) to letter (A, B, ... Z, AA, AB...)."""
    if col_idx < 26:
        return chr(65 + col_idx)
    return chr(65 + col_idx // 26 - 1) + chr(65 + col_idx % 26)

def generate_printable_tiles(doc, tree_info, out_pdf_path):
    """
    Generate Letter landscape tiled PDF at 1:1 original scale with pure white background.
    - 0.25" margins (18 pt) and 0.25" overlap (18 pt) for natural shingling.
    - Clean Bottom and Right edges with no text or labels.
    - Page 1: Master Assembly Guide & Visual Grid Map.
    - Pages 2+: Non-empty tiles with clear Tile Identifiers (e.g. [ TILE B-3 ]).
    """
    src_page = doc[0]

    LETTER_W = 792   # 11 inches in points (landscape)
    LETTER_H = 612   # 8.5 inches in points
    MARGIN = 18      # 0.25 inch margin (18 pt)
    HEADER_H = 22    # 22 pt header bar
    OVERLAP = 18     # 0.25 inch overlap (18 pt) matching margin for clean shingling

    usable_w = LETTER_W - 2 * MARGIN
    usable_h = LETTER_H - 2 * MARGIN - HEADER_H
    step_w = usable_w - OVERLAP
    step_h = usable_h - OVERLAP

    src_w = src_page.rect.width
    src_h = src_page.rect.height

    n_cols = math.ceil(src_w / step_w)
    n_rows = math.ceil(src_h / step_h)
    total_grid_tiles = n_cols * n_rows

    # Extract non-empty content elements to test tile emptiness
    text_blocks = [fitz.Rect(b[:4]) for b in src_page.get_text('blocks') if b[4].strip()]
    
    content_drawings = []
    for d in src_page.get_drawings():
        is_bg = any(item[0] == 're' and item[1].width > src_w * 0.8 and item[1].height > src_h * 0.8 for item in d['items'])
        if not is_bg:
            content_drawings.append(d)

    # 1. First pass: find all active non-empty tiles
    active_tiles = []
    active_map = {}  # (col, row) -> sheet_number (1-based)

    for row in range(n_rows):
        for col in range(n_cols):
            clip_x0 = col * step_w
            clip_y0 = row * step_h
            clip_x1 = min(clip_x0 + usable_w, src_w)
            clip_y1 = min(clip_y0 + usable_h, src_h)
            tile_rect = fitz.Rect(clip_x0, clip_y0, clip_x1, clip_y1)

            # Check if tile contains any text
            has_text = any(tile_rect.intersects(tb) for tb in text_blocks)

            # Check if tile contains drawings / connectors
            has_drawing = False
            for d in content_drawings:
                for item in d['items']:
                    if item[0] == 'l':
                        p1, p2 = item[1], item[2]
                        line_rect = fitz.Rect(min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y))
                        if tile_rect.intersects(line_rect):
                            has_drawing = True
                            break
                    elif item[0] == 're':
                        if tile_rect.intersects(item[1]):
                            has_drawing = True
                            break
                if has_drawing:
                    break

            if has_text or has_drawing:
                sheet_idx = len(active_tiles) + 1
                tile_id = f"{get_col_letter(col)}-{row+1}"
                active_tiles.append({
                    'col': col,
                    'row': row,
                    'tile_id': tile_id,
                    'sheet_num': sheet_idx,
                    'clip_rect': tile_rect,
                    'clip_x0': clip_x0,
                    'clip_y0': clip_y0,
                    'clip_x1': clip_x1,
                    'clip_y1': clip_y1,
                })
                active_map[(col, row)] = sheet_idx

    total_active_pages = len(active_tiles)
    skipped_count = total_grid_tiles - total_active_pages

    out = fitz.open()

    # =========================================================================
    # PAGE 1: MASTER ASSEMBLY GUIDE & VISUAL GRID MAP
    # =========================================================================
    guide_page = out.new_page(width=LETTER_W, height=LETTER_H)
    guide_page.draw_rect(guide_page.rect, color=(1, 1, 1), fill=(1, 1, 1))

    # Header Box
    header_box = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + 42)
    guide_page.draw_rect(header_box, color=(0.15, 0.35, 0.55), fill=(0.94, 0.97, 1.0), width=1.5)
    guide_page.insert_text(fitz.Point(MARGIN + 12, MARGIN + 18), 'MASTER ASSEMBLY GUIDE & GRID MAP', fontsize=13, fontname='hebo', color=(0.1, 0.25, 0.45))
    guide_page.insert_text(fitz.Point(MARGIN + 12, MARGIN + 33), f"{tree_info['name']}   |   Total Size: {tree_info['width_in']}\" × {tree_info['height_in']}\"   |   {total_active_pages} Sheets to Print ({skipped_count} Empty Omitted)", fontsize=8.5, color=(0.3, 0.4, 0.5))

    # Grid Dimensions
    grid_top = MARGIN + 56
    grid_left = MARGIN + 26
    grid_width = LETTER_W - 2 * MARGIN - 38
    grid_bottom = LETTER_H - MARGIN - 64
    grid_height = grid_bottom - grid_top

    cell_w = grid_width / n_cols
    cell_h = grid_height / n_rows

    # Top Column Headers (A, B, C...)
    for c in range(n_cols):
        col_letter = get_col_letter(c)
        cx = grid_left + c * cell_w + cell_w / 2 - (5 if len(col_letter) == 1 else 9)
        guide_page.insert_text(fitz.Point(cx, grid_top - 5), col_letter, fontsize=8.5, fontname='hebo', color=(0.2, 0.35, 0.5))

    # Left Row Headers (R1, R2, R3...)
    for r in range(n_rows):
        ry = grid_top + r * cell_h + cell_h / 2 + 4
        guide_page.insert_text(fitz.Point(grid_left - 22, ry), f"R{r+1}", fontsize=8, fontname='hebo', color=(0.2, 0.35, 0.5))

    # Draw Grid Cells
    for r in range(n_rows):
        for c in range(n_cols):
            rx = grid_left + c * cell_w
            ry = grid_top + r * cell_h
            cell_rect = fitz.Rect(rx + 1, ry + 1, rx + cell_w - 1, ry + cell_h - 1)
            tile_id = f"{get_col_letter(c)}-{r+1}"

            if (c, r) in active_map:
                s_num = active_map[(c, r)]
                guide_page.draw_rect(cell_rect, color=(0.25, 0.55, 0.8), fill=(0.92, 0.96, 1.0), width=1.2)
                
                font_id = 9 if n_cols <= 8 else 7.5
                font_sheet = 7.5 if n_cols <= 8 else 6.0
                
                guide_page.insert_text(fitz.Point(rx + 4, ry + (14 if cell_h > 40 else 12)), tile_id, fontsize=font_id, fontname='hebo', color=(0.1, 0.3, 0.55))
                if cell_h > 26:
                    guide_page.insert_text(fitz.Point(rx + 4, ry + (26 if cell_h > 40 else 22)), f"Sheet #{s_num}", fontsize=font_sheet, color=(0.15, 0.5, 0.25))
            else:
                guide_page.draw_rect(cell_rect, color=(0.84, 0.84, 0.84), fill=(0.96, 0.96, 0.96), width=0.5)
                font_id = 8 if n_cols <= 8 else 6.5
                guide_page.insert_text(fitz.Point(rx + 4, ry + (14 if cell_h > 40 else 12)), tile_id, fontsize=font_id, color=(0.65, 0.65, 0.65))
                if cell_h > 26:
                    guide_page.insert_text(fitz.Point(rx + 4, ry + (25 if cell_h > 40 else 21)), "—", fontsize=8, color=(0.7, 0.7, 0.7))

    # Bottom Instructions Box (Clear Shingle Overlap Directions)
    inst_box = fitz.Rect(MARGIN, LETTER_H - MARGIN - 54, LETTER_W - MARGIN, LETTER_H - MARGIN)
    guide_page.draw_rect(inst_box, color=(0.8, 0.8, 0.8), fill=(0.98, 0.98, 0.98))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 38), 'HOW TO ASSEMBLE (ZERO-CUTTING SHINGLE OVERLAP):', fontsize=8.5, fontname='hebo', color=(0.2, 0.2, 0.2))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 26), '1. Match the Tile Identifier in the top header (e.g. [ TILE B-3 ]) to its grid position above.', fontsize=7.5, color=(0.35, 0.35, 0.35))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 15), '2. Shingle from top-left: overlap each sheet 0.25" over the clean bottom/right edge of its neighbor and tape down.', fontsize=7.5, color=(0.35, 0.35, 0.35))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 4), '3. Gray cells marked "—" are empty space with no family members and were omitted to save paper.', fontsize=7.5, color=(0.35, 0.35, 0.35))

    # =========================================================================
    # PAGES 2+: INDIVIDUAL ACTIVE TILES (CLEAN BOTTOM & RIGHT FOR SHINGLING)
    # =========================================================================
    for idx, tile in enumerate(active_tiles):
        col = tile['col']
        row = tile['row']
        tile_id = tile['tile_id']
        clip_rect = tile['clip_rect']
        clip_x0 = tile['clip_x0']
        clip_y0 = tile['clip_y0']
        clip_x1 = tile['clip_x1']
        clip_y1 = tile['clip_y1']

        out_page = out.new_page(width=LETTER_W, height=LETTER_H)

        # Draw pure white background on entire letter sheet
        out_page.draw_rect(out_page.rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Compact Header Bar at top
        header_rect = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + HEADER_H)
        out_page.draw_rect(header_rect, color=(0.2, 0.35, 0.5), fill=(0.95, 0.97, 1.0))
        
        # High-contrast prominent Tile ID badge on left
        badge_rect = fitz.Rect(MARGIN + 3, MARGIN + 3, MARGIN + 80, MARGIN + HEADER_H - 3)
        out_page.draw_rect(badge_rect, color=(0.15, 0.35, 0.55), fill=(0.15, 0.35, 0.55))
        out_page.insert_text(fitz.Point(MARGIN + 8, MARGIN + HEADER_H - 7), f"TILE {tile_id}", fontsize=9, fontname='hebo', color=(1, 1, 1))

        # Sheet Number & Tree Title
        out_page.insert_text(fitz.Point(MARGIN + 90, MARGIN + HEADER_H - 7), f"Sheet {idx+1} of {total_active_pages}  (Page {idx+2} of {total_active_pages+1})   |   {tree_info['name']}", fontsize=8, color=(0.2, 0.2, 0.2))

        # Grid Coordinates on right
        coord_str = f"Col {get_col_letter(col)} of {n_cols} (Col {col+1}), Row {row+1} of {n_rows}"
        out_page.insert_text(fitz.Point(LETTER_W - MARGIN - 180, MARGIN + HEADER_H - 7), coord_str, fontsize=7.5, color=(0.35, 0.35, 0.35))

        # Tile drawing area
        dest_w = clip_x1 - clip_x0
        dest_h = clip_y1 - clip_y0
        dest_rect = fitz.Rect(
            MARGIN, MARGIN + HEADER_H,
            MARGIN + dest_w,
            MARGIN + HEADER_H + dest_h
        )

        # Copy vector content from modified white-background PDF
        out_page.show_pdf_page(dest_rect, doc, 0, clip=clip_rect)

        # Note: Bottom and Right margins remain 100% clean and free of labels or text
        # for clean shingle overlapping.

    out.save(out_pdf_path)
    size_mb = os.path.getsize(out_pdf_path) / (1024 * 1024)
    total_pdf_pages = total_active_pages + 1  # includes Page 1 Assembly Guide
    print(f"  [TILES] Generated {out_pdf_path} ({total_pdf_pages} total PDF pages: 1 Guide Map + {total_active_pages} tiles | {skipped_count} empty skipped | {size_mb:.2f} MB)")
    
    return {
        'guide_pages': 1,
        'active_pages': total_active_pages,
        'total_pdf_pages': total_pdf_pages,
        'grid_cols': n_cols,
        'grid_rows': n_rows,
        'total_grid_tiles': total_grid_tiles,
        'skipped_empty': skipped_count
    }

def main():
    print("=== Building Grannie's Family Tree Website Assets ===")
    
    search_index = {}
    tree_metadata = []

    for spec in TREE_SPECS:
        tree_id = spec['id']
        pdf_path = os.path.join(PDF_DIR, spec['file'])
        print(f"\nProcessing {tree_id}: {spec['name']}...")
        
        doc = fitz.open(pdf_path)
        
        # 1. Convert background to pure white and eliminate outer frame border
        make_background_white_and_remove_frame(doc)

        page = doc[0]
        pw, ph = page.rect.width, page.rect.height

        # 2. Export SVG with pure white background
        export_svg(doc, tree_id, SVG_DIR)

        # 3. Extract Persons & Coordinates
        persons = extract_search_data(doc)
        search_index[tree_id] = persons
        print(f"  [INDEX] Indexed {len(persons)} persons")

        # 4. Generate Printable Tiled PDF (0.25" Margins, Clean Bottom/Right for Shingling)
        tiles_out_path = os.path.join(TILES_DIR, f"{tree_id}_printable_tiles.pdf")
        tile_stats = generate_printable_tiles(doc, spec, tiles_out_path)

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
            'tile_pages': tile_stats['active_pages'],
            'total_pdf_pages': tile_stats['total_pdf_pages'],
            'grid_cols': tile_stats['grid_cols'],
            'grid_rows': tile_stats['grid_rows'],
            'total_grid_tiles': tile_stats['total_grid_tiles'],
            'skipped_empty': tile_stats['skipped_empty'],
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
