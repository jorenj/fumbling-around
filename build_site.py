#!/usr/bin/env python3
"""
build_site.py - Generate all website assets for Grannie's Family Trees website.

Features:
  - Compact Portrait Icons (60% scale): Downscales large portrait frames to neat, elegant icons.
  - Enhanced Readable Typography (115% scale): Increases text size by 15% for crisp, legible names and dates on paper.
  - Complete Person Card Capture: Encompasses portrait photos, decorative frames, names, and detail spans.
  - Seam-Clearing Layout Engine: Shifts person entries away from fixed Letter grid seams
    (X = 756, 1512... pt; Y = 554, 1108... pt) into available whitespace gutters without overlapping neighboring entries.
  - 100% Exact Vector Formatting: Preserves original typography and high-res photos using direct vector clip mapping.
  - Perfect Uniform Printable Grid: Every sheet is a standard Letter landscape page (11" x 8.5")
    at exact 1:1 true scale with uniform 10.5" x 7.69" printable areas (Col A, B, C... x Row 1, 2, 3...).
  - Continuous Connector Line Bleed: Any connecting lines crossing sheet boundaries extend across
    margins all the way to the physical page edges so no lines are lost during physical assembly/shingling.
  - Page 1: Master Assembly Guide Sheet with complete visual grid matrix map.
  - Page 2: Full Assembled View & Alignment Proof.
  - Pages 3+: Individual active printable sheets at exact 1:1 true scale with prominent [ TILE B-3 ] header badges.
  - 0.25" white printer hardware margins (18 pt).
  - 100% pure crisp white background (no ink waste on background tint).
"""

import os
import re
import json
import math
import datetime
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
        'subtitle': 'Marion Parker Inglis (b. 1909, Glasgow)',
        'description': '6 generations across Scotland and North America.',
        'width_in': 62.7,
        'height_in': 46.0,
    },
    {
        'id': '000061',
        'file': '000061_762453ldc65q126fw5lv98_A.pdf',
        'name': 'Close Family of Thomas Kinlay Johnston',
        'subtitle': 'Thomas Kinlay Johnston (b. 1913, Fife)',
        'description': 'Panoramic chart spanning 8 generations with 200+ family members.',
        'width_in': 151.2,
        'height_in': 37.6,
    },
    {
        'id': '000067',
        'file': '000067_222401i6396f79e5bznd7b_A.pdf',
        'name': 'Ancestors of Marion Parker Inglis',
        'subtitle': 'Ancestors of Marion Parker Inglis',
        'description': 'Inglis, Gallie, and Crawford family lines.',
        'width_in': 54.4,
        'height_in': 39.3,
    },
    {
        'id': '000069',
        'file': '000069_011201c6d3z98f777bt629_A.pdf',
        'name': 'Ancestors of John Inglis',
        'subtitle': 'John Inglis (b. 1872, Roxburgh)',
        'description': 'Scottish ancestral lineage of the Inglis family.',
        'width_in': 43.6,
        'height_in': 35.8,
    },
    {
        'id': '000071',
        'file': '000071_77048093bwa928agcd8b62_A.pdf',
        'name': 'Ancestors of Thomas Kinlay Johnston',
        'subtitle': 'Thomas Kinlay Johnston (b. 1913, Fife)',
        'description': 'Johnston, Kinlay, and Mackie family lines.',
        'width_in': 40.9,
        'height_in': 27.7,
    },
]

LETTER_W = 792.0   # 11 inches in points (landscape)
LETTER_H = 612.0   # 8.5 inches in points
MARGIN = 18.0      # 0.25 inch margin (18 pt)
HEADER_H = 22.0    # 22 pt header bar

PRINTABLE_W = LETTER_W - 2 * MARGIN  # 756 pt (10.50 in)
PRINTABLE_H = LETTER_H - 2 * MARGIN - HEADER_H  # 554 pt (7.69 in)
MARGIN_SAFE = 15.0  # Minimum clearance from any grid seam line

PHOTO_SCALE = 0.60  # Compact portrait icon (60% of original bulky size)
TEXT_SCALE = 1.15   # Slightly larger readable typography (+15%)

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

def get_col_letter(col_idx: int) -> str:
    """Convert column index (0-based) to letter (A, B, ... Z, AA, AB...)."""
    if col_idx < 26:
        return chr(65 + col_idx)
    return chr(65 + col_idx // 26 - 1) + chr(65 + col_idx % 26)

def make_background_white_and_remove_frame(doc):
    """
    1. Replace parchment background fill with pure white (1 1 1 rg) to save ink.
    2. Eliminate outer decorative poster frame border for clean borderless prints.
    """
    page = doc[0]
    for xref in page.get_contents():
        stream = doc.xref_stream(xref).decode('latin1')
        stream_mod = re.sub(r'\.949\s+\.949\s+\.937\s+rg', '1 1 1 rg', stream)
        doc.update_stream(xref, stream_mod.encode('latin1'))

def extract_entities(page):
    """
    Extract all discrete Person Entities, Titles, and Vector Connector Lines from a page.
    Structures each card with compact photo and larger text dimensions.
    """
    td = page.get_text('dict')
    spans = []
    titles = []

    for b in td['blocks']:
        if b['type'] == 0:
            for l in b['lines']:
                for s in l['spans']:
                    txt = s['text'].strip()
                    if txt:
                        if s['size'] > 20:
                            titles.append({
                                'text': txt,
                                'bbox': fitz.Rect(s['bbox']),
                                'font': s['font'],
                                'size': s['size'],
                                'color': s['color']
                            })
                        else:
                            spans.append({
                                'text': txt,
                                'bbox': fitz.Rect(s['bbox']),
                                'font': s['font'],
                                'size': s['size'],
                                'color': s['color']
                            })

    imgs = [fitz.Rect(im['bbox']) for im in page.get_image_info() if 10 < im['bbox'][2] - im['bbox'][0] < 300 and 10 < im['bbox'][3] - im['bbox'][1] < 300]

    persons = []
    used_spans = set()
    used_imgs = set()
    name_spans = [i for i, s in enumerate(spans) if 'Bold' in s['font'] and s['size'] >= 8.5]

    for n_idx in name_spans:
        if n_idx in used_spans:
            continue
        ns = spans[n_idx]
        p_text_rect = fitz.Rect(ns['bbox'])
        p_name_spans = [ns]
        used_spans.add(n_idx)

        # Multi-line name
        for other_idx in name_spans:
            if other_idx not in used_spans:
                os = spans[other_idx]
                if abs(ns['bbox'].x0 - os['bbox'].x0) < 50 and 0 < (os['bbox'].y0 - ns['bbox'].y0) < 25:
                    p_text_rect.include_rect(os['bbox'])
                    p_name_spans.append(os)
                    used_spans.add(other_idx)

        # Associated photo and decorative frame (located directly ABOVE the name text)
        p_imgs = []
        for im_idx, im_rect in enumerate(imgs):
            if 0 <= (p_text_rect.y0 - im_rect.y0) < 95 and abs((im_rect.x0 + im_rect.x1)/2 - (p_text_rect.x0 + p_text_rect.x1)/2) < 70:
                p_imgs.append(im_rect)
                used_imgs.add(im_idx)

        # Associated detail spans (birth, death, marriage - located BELOW name)
        p_details = []
        for s_idx, s in enumerate(spans):
            if s_idx not in used_spans and 'Bold' not in s['font']:
                if (p_text_rect.x0 - 20) <= s['bbox'].x0 <= (p_text_rect.x1 + 20) and 0 <= (s['bbox'].y0 - p_text_rect.y0) < 140:
                    p_text_rect.include_rect(s['bbox'])
                    p_details.append(s['text'])
                    used_spans.add(s_idx)

        photo_orig = None
        if p_imgs:
            photo_orig = fitz.Rect(p_imgs[0])
            for im in p_imgs[1:]:
                photo_orig.include_rect(im)

        # Card footprint with compact photo (0.60x) and larger text (1.15x)
        photo_w = (photo_orig.width * PHOTO_SCALE) if photo_orig else 0.0
        photo_h = (photo_orig.height * PHOTO_SCALE) if photo_orig else 0.0
        text_w = p_text_rect.width * TEXT_SCALE
        text_h = p_text_rect.height * TEXT_SCALE

        card_w = max(photo_w, text_w) + 6.0
        card_h = (photo_h + 4.0 + text_h) if photo_orig else text_h

        center_x = (p_text_rect.x0 + p_text_rect.x1) / 2
        card_y0 = (photo_orig.y0 + (photo_orig.height - photo_h)) if photo_orig else p_text_rect.y0

        card_rect = fitz.Rect(center_x - card_w/2, card_y0, center_x + card_w/2, card_y0 + card_h)

        full_name = clean_text(' '.join(it['text'] for it in p_name_spans))
        detail_clean = clean_text(' '.join(p_details))

        persons.append({
            'id': len(persons),
            'name': full_name,
            'details': detail_clean,
            'photo_orig': photo_orig,
            'text_orig': fitz.Rect(p_text_rect),
            'rect': fitz.Rect(card_rect),
            'orig_rect': fitz.Rect(card_rect),
            'photos_count': len(p_imgs),
            'shift_x': 0.0,
            'shift_y': 0.0
        })

    # Extract all connecting line drawings
    lines = []
    for d in page.get_drawings():
        is_bg = any(item[0] == 're' and item[1].width > page.rect.width * 0.8 for item in d['items'])
        if not is_bg:
            for item in d['items']:
                if item[0] == 'l':
                    lines.append({
                        'p1': item[1],
                        'p2': item[2],
                        'color': d['color'] or (0.714, 0.714, 0.714),
                        'width': d['width'] or 1.5
                    })

    return persons, titles, lines

def optimize_tree_layout(persons, titles, lines, sw, sh):
    """
    Shifts person cards away from fixed Letter grid seams while preserving relative hierarchy,
    order, and spacing without introducing overlaps.
    """
    n_cols = math.ceil(sw / PRINTABLE_W)
    n_rows = math.ceil(sh / PRINTABLE_H)
    grid_x = [c * PRINTABLE_W for c in range(1, n_cols)]
    grid_y = [r * PRINTABLE_H for r in range(1, n_rows)]

    # -------------------------------------------------------------------------
    # 1. Vertical Optimization (Generational Tier Shifting)
    # -------------------------------------------------------------------------
    gen_rows = []
    for p in sorted(persons, key=lambda x: x['rect'].y0):
        placed = False
        for gr in gen_rows:
            if abs(p['rect'].y0 - gr['mean_y']) < 35:
                gr['persons'].append(p)
                gr['mean_y'] = sum(x['rect'].y0 for x in gr['persons']) / len(gr['persons'])
                placed = True
                break
        if not placed:
            gen_rows.append({'mean_y': p['rect'].y0, 'persons': [p]})
    gen_rows.sort(key=lambda gr: gr['mean_y'])

    for gr in gen_rows:
        min_y = min(p['rect'].y0 for p in gr['persons'])
        max_y = max(p['rect'].y1 for p in gr['persons'])
        for gy in grid_y:
            if min_y < gy + MARGIN_SAFE and max_y > gy - MARGIN_SAFE:
                shift_up = (gy - MARGIN_SAFE) - max_y
                shift_down = (gy + MARGIN_SAFE) - min_y
                gr_idx = gen_rows.index(gr)
                prev_max_y = max(p['rect'].y1 for p in gen_rows[gr_idx - 1]['persons']) if gr_idx > 0 else 0
                next_min_y = min(p['rect'].y0 for p in gen_rows[gr_idx + 1]['persons']) if gr_idx < len(gen_rows) - 1 else sh
                space_up = min_y - prev_max_y
                space_down = next_min_y - max_y
                chosen = shift_up if (space_up > abs(shift_up) + 15 or abs(shift_up) < shift_down) else shift_down
                for p in gr['persons']:
                    p['shift_y'] += chosen
                    p['rect'].y0 += chosen
                    p['rect'].y1 += chosen

    # -------------------------------------------------------------------------
    # 2. Horizontal Optimization (Seam Clearing per Generational Row)
    # -------------------------------------------------------------------------
    for gr in gen_rows:
        gr['persons'].sort(key=lambda x: x['rect'].x0)
        groups = []
        for p in gr['persons']:
            if not groups:
                groups.append([p])
            else:
                prev_max = groups[-1][-1]['rect'].x1
                if p['rect'].x0 - prev_max < 20.0:
                    groups[-1].append(p)
                else:
                    groups.append([p])

        for _ in range(35):
            moved = False
            for g_idx, grp in enumerate(groups):
                gx0 = min(p['rect'].x0 for p in grp)
                gx1 = max(p['rect'].x1 for p in grp)

                for seam_x in grid_x:
                    if gx0 < seam_x + MARGIN_SAFE and gx1 > seam_x - MARGIN_SAFE:
                        moved = True
                        push_left = (seam_x - MARGIN_SAFE) - gx1
                        push_right = (seam_x + MARGIN_SAFE) - gx0

                        prev_g_x1 = max(p['rect'].x1 for p in groups[g_idx - 1]) if g_idx > 0 else 0
                        next_g_x0 = min(p['rect'].x0 for p in groups[g_idx + 1]) if g_idx < len(groups) - 1 else sw

                        left_space = gx0 - prev_g_x1
                        right_space = next_g_x0 - gx1

                        if left_space > abs(push_left) + 10:
                            chosen_push = push_left
                        elif right_space > push_right + 10:
                            chosen_push = push_right
                        else:
                            chosen_push = push_left if abs(push_left) < push_right else push_right

                        for p in grp:
                            p['shift_x'] += chosen_push
                            p['rect'].x0 += chosen_push
                            p['rect'].x1 += chosen_push

                        # Propagate push right
                        for i in range(g_idx, len(groups) - 1):
                            curr_max = max(p['rect'].x1 for p in groups[i])
                            nxt_min = min(p['rect'].x0 for p in groups[i+1])
                            if nxt_min < curr_max + 8.0:
                                diff = (curr_max + 8.0) - nxt_min
                                for p in groups[i+1]:
                                    p['shift_x'] += diff
                                    p['rect'].x0 += diff
                                    p['rect'].x1 += diff

                        # Propagate push left
                        for i in range(g_idx, 0, -1):
                            curr_min = min(p['rect'].x0 for p in groups[i])
                            prev_max = max(p['rect'].x1 for p in groups[i-1])
                            if prev_max > curr_min - 8.0:
                                diff = (curr_min - 8.0) - prev_max
                                for p in groups[i-1]:
                                    p['shift_x'] += diff
                                    p['rect'].x0 += diff
                                    p['rect'].x1 += diff
            if not moved:
                break

    # -------------------------------------------------------------------------
    # 3. Chart Title Seam Clearing
    # -------------------------------------------------------------------------
    for t in titles:
        t_rect = t['bbox']
        t['shift_x'] = 0.0
        t['shift_y'] = 0.0
        for gx in grid_x:
            if t_rect.x0 < gx + MARGIN_SAFE and t_rect.x1 > gx - MARGIN_SAFE:
                push_left = (gx - MARGIN_SAFE) - t_rect.x1
                push_right = (gx + MARGIN_SAFE) - t_rect.x0
                chosen = push_left if abs(push_left) < push_right else push_right
                t['shift_x'] += chosen
                t_rect.x0 += chosen
                t_rect.x1 += chosen

    # -------------------------------------------------------------------------
    # 4. Connector Line Displacement Mapping
    # -------------------------------------------------------------------------
    for l in lines:
        p1, p2 = l['p1'], l['p2']
        closest_p1 = min(persons, key=lambda p: (min(abs(p1.x - p['orig_rect'].x0), abs(p1.x - p['orig_rect'].x1))**2 + min(abs(p1.y - p['orig_rect'].y0), abs(p1.y - p['orig_rect'].y1))**2))
        closest_p2 = min(persons, key=lambda p: (min(abs(p2.x - p['orig_rect'].x0), abs(p2.x - p['orig_rect'].x1))**2 + min(abs(p2.y - p['orig_rect'].y0), abs(p2.y - p['orig_rect'].y1))**2))

        d1 = math.hypot(p1.x - (closest_p1['orig_rect'].x0 + closest_p1['orig_rect'].x1)/2, p1.y - (closest_p1['orig_rect'].y0 + closest_p1['orig_rect'].y1)/2)
        d2 = math.hypot(p2.x - (closest_p2['orig_rect'].x0 + closest_p2['orig_rect'].x1)/2, p2.y - (closest_p2['orig_rect'].y0 + closest_p2['orig_rect'].y1)/2)

        p1_shift_x = closest_p1['shift_x'] if d1 < 120 else 0.0
        p1_shift_y = closest_p1['shift_y'] if d1 < 120 else 0.0
        p2_shift_x = closest_p2['shift_x'] if d2 < 120 else 0.0
        p2_shift_y = closest_p2['shift_y'] if d2 < 120 else 0.0

        if abs(p1.x - p2.x) < 2.0:  # Vertical line
            avg_shift_x = (p1_shift_x + p2_shift_x) / 2 if (p1_shift_x and p2_shift_x) else (p1_shift_x or p2_shift_x)
            l['new_p1'] = fitz.Point(p1.x + avg_shift_x, p1.y + p1_shift_y)
            l['new_p2'] = fitz.Point(p2.x + avg_shift_x, p2.y + p2_shift_y)
        elif abs(p1.y - p2.y) < 2.0:  # Horizontal line
            avg_shift_y = (p1_shift_y + p2_shift_y) / 2 if (p1_shift_y and p2_shift_y) else (p1_shift_y or p2_shift_y)
            l['new_p1'] = fitz.Point(p1.x + p1_shift_x, p1.y + avg_shift_y)
            l['new_p2'] = fitz.Point(p2.x + p2_shift_x, p2.y + avg_shift_y)
        else:
            l['new_p1'] = fitz.Point(p1.x + p1_shift_x, p1.y + p1_shift_y)
            l['new_p2'] = fitz.Point(p2.x + p2_shift_x, p2.y + p2_shift_y)

def generate_printable_tiles(orig_doc, persons, titles, lines, tree_info, out_pdf_path):
    """
    Generate Letter landscape tiled PDF in a perfect, uniform, rectangular grid at 1:1 true scale.
    Renders person cards with compact portrait icons and larger, highly readable typography.
    Extends connecting lines across margins to the physical page edges.
    """
    src_page = orig_doc[0]
    src_w = src_page.rect.width
    src_h = src_page.rect.height

    n_cols = math.ceil(src_w / PRINTABLE_W)
    n_rows = math.ceil(src_h / PRINTABLE_H)

    all_grid_tiles = []
    active_tiles = []
    active_map = {}

    for r in range(n_rows):
        y0 = r * PRINTABLE_H
        y1 = (r + 1) * PRINTABLE_H

        for c in range(n_cols):
            x0 = c * PRINTABLE_W
            x1 = (c + 1) * PRINTABLE_W
            tile_rect = fitz.Rect(x0, y0, x1, y1)

            has_person = any(tile_rect.intersects(p['rect']) for p in persons)
            has_title = any(tile_rect.intersects(t['bbox']) for t in titles)
            has_line = False
            for l in lines:
                p1 = l.get('new_p1', l['p1'])
                p2 = l.get('new_p2', l['p2'])
                line_rect = fitz.Rect(min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y))
                if tile_rect.intersects(line_rect):
                    has_line = True
                    break

            tile_info = {
                'row': r,
                'col': c,
                'tile_id': f"{get_col_letter(c)}-{r+1}",
                'clip_rect': tile_rect,
                'x0': round(x0, 1),
                'y0': round(y0, 1),
                'x1': round(x1, 1),
                'y1': round(y1, 1),
                'has_content': has_person or has_title or has_line
            }
            all_grid_tiles.append(tile_info)

            if tile_info['has_content']:
                sheet_idx = len(active_tiles) + 1
                tile_info['sheet_num'] = sheet_idx
                active_tiles.append(tile_info)
                active_map[(c, r)] = sheet_idx

    total_grid_tiles = len(all_grid_tiles)
    total_active_pages = len(active_tiles)
    skipped_count = total_grid_tiles - total_active_pages

    out = fitz.open()

    # =========================================================================
    # PAGE 1: MASTER ASSEMBLY GUIDE & VISUAL GRID MATRIX MAP
    # =========================================================================
    guide_page = out.new_page(width=LETTER_W, height=LETTER_H)
    guide_page.draw_rect(guide_page.rect, color=(1, 1, 1), fill=(1, 1, 1))

    # Header Box
    header_box = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + 42)
    guide_page.draw_rect(header_box, color=(0.15, 0.35, 0.55), fill=(0.94, 0.97, 1.0), width=1.5)
    guide_page.insert_text(fitz.Point(MARGIN + 12, MARGIN + 18), 'ASSEMBLY GUIDE & GRID MAP', fontsize=13, fontname='hebo', color=(0.1, 0.25, 0.45))
    guide_page.insert_text(fitz.Point(MARGIN + 12, MARGIN + 33), f"{tree_info['name']}   |   Uniform Grid: {n_cols} Cols × {n_rows} Rows ({n_cols*n_rows} Cells)   |   {total_active_pages} Sheets (+ Guides)", fontsize=8.5, color=(0.3, 0.4, 0.5))

    # Grid Dimensions
    grid_top = MARGIN + 56
    grid_left = MARGIN + 26
    grid_width = LETTER_W - 2 * MARGIN - 38
    grid_bottom = LETTER_H - MARGIN - 64
    grid_height = grid_bottom - grid_top

    cell_w = grid_width / n_cols
    cell_h = grid_height / n_rows

    for c in range(n_cols):
        col_letter = get_col_letter(c)
        cx = grid_left + c * cell_w + cell_w / 2 - (5 if len(col_letter) == 1 else 9)
        guide_page.insert_text(fitz.Point(cx, grid_top - 5), col_letter, fontsize=8.5, fontname='hebo', color=(0.2, 0.35, 0.5))

    for r in range(n_rows):
        ry = grid_top + r * cell_h + cell_h / 2 + 4
        guide_page.insert_text(fitz.Point(grid_left - 22, ry), f"R{r+1}", fontsize=8, fontname='hebo', color=(0.2, 0.35, 0.5))

    for t in all_grid_tiles:
        r = t['row']
        c = t['col']
        rx = grid_left + c * cell_w
        ry = grid_top + r * cell_h
        cell_rect = fitz.Rect(rx + 1, ry + 1, rx + cell_w - 1, ry + cell_h - 1)
        tile_id = t['tile_id']

        if (c, r) in active_map:
            s_num = active_map[(c, r)]
            guide_page.draw_rect(cell_rect, color=(0.25, 0.55, 0.8), fill=(0.92, 0.96, 1.0), width=1.2)
            font_id = 9 if n_cols <= 8 else 6.5
            font_sheet = 7.5 if n_cols <= 8 else 5.0
            guide_page.insert_text(fitz.Point(rx + 3, ry + (14 if cell_h > 35 else 10)), tile_id, fontsize=font_id, fontname='hebo', color=(0.1, 0.3, 0.55))
            if cell_h > 20:
                guide_page.insert_text(fitz.Point(rx + 3, ry + (25 if cell_h > 35 else 19)), f"#{s_num}", fontsize=font_sheet, color=(0.15, 0.5, 0.25))
        else:
            guide_page.draw_rect(cell_rect, color=(0.84, 0.84, 0.84), fill=(0.96, 0.96, 0.96), width=0.5)
            font_id = 8 if n_cols <= 8 else 5.5
            guide_page.insert_text(fitz.Point(rx + 3, ry + (14 if cell_h > 35 else 10)), tile_id, fontsize=font_id, color=(0.65, 0.65, 0.65))
            if cell_h > 20:
                guide_page.insert_text(fitz.Point(rx + 3, ry + (24 if cell_h > 35 else 18)), "—", fontsize=7.5, color=(0.7, 0.7, 0.7))

    inst_box = fitz.Rect(MARGIN, LETTER_H - MARGIN - 54, LETTER_W - MARGIN, LETTER_H - MARGIN)
    guide_page.draw_rect(inst_box, color=(0.8, 0.8, 0.8), fill=(0.98, 0.98, 0.98))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 38), 'ASSEMBLY INSTRUCTIONS:', fontsize=8.5, fontname='hebo', color=(0.2, 0.2, 0.2))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 26), '1. Page 2 shows the complete assembled poster with all sheet outlines overlaid for visual alignment reference.', fontsize=7.5, color=(0.35, 0.35, 0.35))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 15), '2. Follow the grid above. Sheets are labeled with their column and row (e.g., Tile A-1, B-1, A-2, B-2).', fontsize=7.5, color=(0.35, 0.35, 0.35))
    guide_page.insert_text(fitz.Point(MARGIN + 10, LETTER_H - MARGIN - 4), '3. Gray cells marked "—" are empty space and were omitted to save paper.', fontsize=7.5, color=(0.35, 0.35, 0.35))

    # =========================================================================
    # PAGE 2: FULL ASSEMBLED VIEW & ALIGNMENT PROOF (SCALED POSTER PROOF)
    # =========================================================================
    proof_page = out.new_page(width=LETTER_W, height=LETTER_H)
    proof_page.draw_rect(proof_page.rect, color=(1, 1, 1), fill=(1, 1, 1))

    # Header Box
    p2_header = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + 36)
    proof_page.draw_rect(p2_header, color=(0.15, 0.35, 0.55), fill=(0.94, 0.97, 1.0), width=1.2)
    proof_page.insert_text(fitz.Point(MARGIN + 10, MARGIN + 16), 'FULL ASSEMBLED VIEW & ALIGNMENT PROOF', fontsize=11, fontname='hebo', color=(0.1, 0.25, 0.45))
    proof_page.insert_text(fitz.Point(MARGIN + 10, MARGIN + 28), f"Visual proof of the full assembled family tree. Blue outlines show individual printable sheets ({total_active_pages} active sheets).", fontsize=7.5, color=(0.3, 0.4, 0.5))

    # Full Vector Tree Render (scaled)
    proof_dest = fitz.Rect(MARGIN, MARGIN + 42, LETTER_W - MARGIN, LETTER_H - MARGIN)
    proof_scale = min(proof_dest.width / src_w, proof_dest.height / src_h)
    proof_w = src_w * proof_scale
    proof_h = src_h * proof_scale
    proof_fit = fitz.Rect(
        proof_dest.x0 + (proof_dest.width - proof_w) / 2,
        proof_dest.y0 + (proof_dest.height - proof_h) / 2,
        proof_dest.x0 + (proof_dest.width - proof_w) / 2 + proof_w,
        proof_dest.y0 + (proof_dest.height - proof_h) / 2 + proof_h
    )

    # Draw lines on proof
    for l in lines:
        p1 = l.get('new_p1', l['p1'])
        p2 = l.get('new_p2', l['p2'])
        proof_page.draw_line(
            fitz.Point(proof_fit.x0 + p1.x * proof_scale, proof_fit.y0 + p1.y * proof_scale),
            fitz.Point(proof_fit.x0 + p2.x * proof_scale, proof_fit.y0 + p2.y * proof_scale),
            color=l['color'], width=max(0.5, l['width'] * proof_scale)
        )

    # Draw titles on proof
    for t in titles:
        orig_box = fitz.Rect(t['bbox'].x0 - t['shift_x'], t['bbox'].y0 - t['shift_y'], t['bbox'].x1 - t['shift_x'], t['bbox'].y1 - t['shift_y'])
        nb = fitz.Rect(
            proof_fit.x0 + t['bbox'].x0 * proof_scale,
            proof_fit.y0 + t['bbox'].y0 * proof_scale,
            proof_fit.x0 + t['bbox'].x1 * proof_scale,
            proof_fit.y0 + t['bbox'].y1 * proof_scale
        )
        proof_page.show_pdf_page(nb, orig_doc, 0, clip=orig_box)

    # Draw person cards on proof (compact photo + larger text)
    for p in persons:
        cx = (p['rect'].x0 + p['rect'].x1) / 2
        p_y0 = p['rect'].y0

        if p['photo_orig']:
            pw = p['photo_orig'].width * PHOTO_SCALE * proof_scale
            ph = p['photo_orig'].height * PHOTO_SCALE * proof_scale
            nb_photo = fitz.Rect(
                proof_fit.x0 + cx * proof_scale - pw/2,
                proof_fit.y0 + p_y0 * proof_scale,
                proof_fit.x0 + cx * proof_scale + pw/2,
                proof_fit.y0 + p_y0 * proof_scale + ph
            )
            proof_page.show_pdf_page(nb_photo, orig_doc, 0, clip=p['photo_orig'])
            p_text_y = p_y0 + (p['photo_orig'].height * PHOTO_SCALE + 4.0)
        else:
            p_text_y = p_y0

        tw = p['text_orig'].width * TEXT_SCALE * proof_scale
        th = p['text_orig'].height * TEXT_SCALE * proof_scale
        nb_text = fitz.Rect(
            proof_fit.x0 + cx * proof_scale - tw/2,
            proof_fit.y0 + p_text_y * proof_scale,
            proof_fit.x0 + cx * proof_scale + tw/2,
            proof_fit.y0 + p_text_y * proof_scale + th
        )
        proof_page.show_pdf_page(nb_text, orig_doc, 0, clip=p['text_orig'])

    # Superimpose Active Sheet Rectangles & Badges
    for t in active_tiles:
        x0_s = proof_fit.x0 + t['x0'] * proof_scale
        y0_s = proof_fit.y0 + t['y0'] * proof_scale
        x1_s = proof_fit.x0 + t['x1'] * proof_scale
        y1_s = proof_fit.y0 + t['y1'] * proof_scale

        s_rect = fitz.Rect(x0_s, y0_s, x1_s, y1_s)
        proof_page.draw_rect(s_rect, color=(0.15, 0.45, 0.85), width=0.75)

        badge_w = min(42, s_rect.width * 0.7)
        badge_h = min(11, s_rect.height * 0.4)
        if badge_w > 18 and badge_h > 6:
            b_rect = fitz.Rect(x0_s + 1, y0_s + 1, x0_s + 1 + badge_w, y0_s + 1 + badge_h)
            proof_page.draw_rect(b_rect, color=(0.15, 0.35, 0.55), fill=(0.15, 0.35, 0.55))
            proof_page.insert_text(fitz.Point(x0_s + 2, y0_s + badge_h - 2), f"#{t['sheet_num']} {t['tile_id']}", fontsize=5, fontname='hebo', color=(1, 1, 1))

    # =========================================================================
    # PAGES 3+: INDIVIDUAL ACTIVE TILES (1:1 TRUE SCALE)
    # =========================================================================
    for idx, tile in enumerate(active_tiles):
        col = tile['col']
        row = tile['row']
        tile_id = tile['tile_id']
        x0, y0 = tile['x0'], tile['y0']
        x1, y1 = tile['x1'], tile['y1']
        clip_rect = tile['clip_rect']

        out_page = out.new_page(width=LETTER_W, height=LETTER_H)
        out_page.draw_rect(out_page.rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Compact Header Bar at top
        header_rect = fitz.Rect(MARGIN, MARGIN, LETTER_W - MARGIN, MARGIN + HEADER_H)
        out_page.draw_rect(header_rect, color=(0.2, 0.35, 0.5), fill=(0.95, 0.97, 1.0))

        # High-contrast prominent Tile ID badge on left
        badge_rect = fitz.Rect(MARGIN + 3, MARGIN + 3, MARGIN + 80, MARGIN + HEADER_H - 3)
        out_page.draw_rect(badge_rect, color=(0.15, 0.35, 0.55), fill=(0.15, 0.35, 0.55))
        out_page.insert_text(fitz.Point(MARGIN + 8, MARGIN + HEADER_H - 7), f"TILE {tile_id}", fontsize=9, fontname='hebo', color=(1, 1, 1))

        # Sheet Number & Tree Title
        out_page.insert_text(fitz.Point(MARGIN + 90, MARGIN + HEADER_H - 7), f"Sheet {idx+1} of {total_active_pages}   |   {tree_info['name']}", fontsize=8, color=(0.2, 0.2, 0.2))

        # Grid Coordinates on right
        coord_str = f"Col {get_col_letter(col)}, Row {row+1} (Grid {n_cols} × {n_rows})"
        out_page.insert_text(fitz.Point(LETTER_W - MARGIN - 170, MARGIN + HEADER_H - 7), coord_str, fontsize=7.5, color=(0.35, 0.35, 0.35))

        # 1. Draw Connector Lines in this tile (with margin extensions so no lines are lost)
        for l in lines:
            p1 = l.get('new_p1', l['p1'])
            p2 = l.get('new_p2', l['p2'])
            min_lx, max_lx = min(p1.x, p2.x), max(p1.x, p2.x)
            min_ly, max_ly = min(p1.y, p2.y), max(p1.y, p2.y)

            # Check if line intersects this tile
            if not (max_lx < x0 - 2 or min_lx > x1 + 2 or max_ly < y0 - 2 or min_ly > y1 + 2):
                page_x1 = MARGIN + (p1.x - x0)
                page_y1 = MARGIN + HEADER_H + (p1.y - y0)
                page_x2 = MARGIN + (p2.x - x0)
                page_y2 = MARGIN + HEADER_H + (p2.y - y0)

                # Horizontal line: extend to left/right paper edges if crossing seams
                if abs(p1.y - p2.y) < 2.0:
                    py = (page_y1 + page_y2) / 2
                    px_start = page_x1 if min_lx >= x0 else 0.0
                    px_end = page_x2 if max_lx <= x1 else LETTER_W
                    out_page.draw_line(fitz.Point(px_start, py), fitz.Point(px_end, py), color=l['color'], width=l['width'])

                # Vertical line: extend to top/bottom paper edges if crossing seams
                elif abs(p1.x - p2.x) < 2.0:
                    px = (page_x1 + page_x2) / 2
                    py_start = page_y1 if min_ly >= y0 else 0.0
                    py_end = page_y2 if max_ly <= y1 else LETTER_H
                    out_page.draw_line(fitz.Point(px, py_start), fitz.Point(px, py_end), color=l['color'], width=l['width'])
                else:
                    out_page.draw_line(fitz.Point(page_x1, page_y1), fitz.Point(page_x2, page_y2), color=l['color'], width=l['width'])

        # 2. Draw Titles in this tile
        for t in titles:
            if clip_rect.intersects(t['bbox']):
                tb = t['bbox']
                orig_box = fitz.Rect(tb.x0 - t['shift_x'], tb.y0 - t['shift_y'], tb.x1 - t['shift_x'], tb.y1 - t['shift_y'])
                dest_b = fitz.Rect(
                    MARGIN + (tb.x0 - x0),
                    MARGIN + HEADER_H + (tb.y0 - y0),
                    MARGIN + (tb.x1 - x0),
                    MARGIN + HEADER_H + (tb.y1 - y0)
                )
                out_page.show_pdf_page(dest_b, orig_doc, 0, clip=orig_box)

        # 3. Draw Person Cards in this tile (compact photo icon + 15% larger text)
        for p in persons:
            if clip_rect.intersects(p['rect']):
                sheet_cx = MARGIN + (p['rect'].x0 + p['rect'].x1) / 2 - x0
                sheet_y0 = MARGIN + HEADER_H + (p['rect'].y0 - y0)

                # Draw Compact Portrait Icon (60% scale)
                if p['photo_orig']:
                    photo_w = p['photo_orig'].width * PHOTO_SCALE
                    photo_h = p['photo_orig'].height * PHOTO_SCALE
                    dest_photo = fitz.Rect(sheet_cx - photo_w/2, sheet_y0, sheet_cx + photo_w/2, sheet_y0 + photo_h)
                    out_page.show_pdf_page(dest_photo, orig_doc, 0, clip=p['photo_orig'])
                    text_y0 = sheet_y0 + photo_h + 4.0
                else:
                    text_y0 = sheet_y0

                # Draw Enhanced Readable Typography (115% scale)
                text_w = p['text_orig'].width * TEXT_SCALE
                text_h = p['text_orig'].height * TEXT_SCALE
                dest_text = fitz.Rect(sheet_cx - text_w/2, text_y0, sheet_cx + text_w/2, text_y0 + text_h)
                out_page.show_pdf_page(dest_text, orig_doc, 0, clip=p['text_orig'])

    out.save(out_pdf_path)
    size_mb = os.path.getsize(out_pdf_path) / (1024 * 1024)
    total_pdf_pages = len(out)
    print(f"  [TILES] Generated {out_pdf_path} ({total_pdf_pages} total PDF pages: 1 Guide Map + 1 Assembled Proof + {total_active_pages} tiles | {skipped_count} empty skipped | {size_mb:.2f} MB)")

    return {
        'guide_pages': 2,
        'active_pages': total_active_pages,
        'total_pdf_pages': total_pdf_pages,
        'grid_cols': n_cols,
        'grid_rows': n_rows,
        'total_grid_tiles': total_grid_tiles,
        'skipped_empty': skipped_count,
        'tiles': [{
            'tile_id': t['tile_id'],
            'sheet_num': t['sheet_num'],
            'col': t['col'],
            'row': t['row'],
            'x0': t['x0'], 'y0': t['y0'],
            'x1': t['x1'], 'y1': t['y1'],
            'w': round(t['x1'] - t['x0'], 1),
            'h': round(t['y1'] - t['y0'], 1)
        } for t in active_tiles]
    }

def export_svg(orig_doc, tree_id, out_dir):
    """Export lightweight vector SVG for the web app."""
    page = orig_doc[0]
    svg_data = page.get_svg_image()
    out_path = os.path.join(out_dir, f'{tree_id}.svg')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_data)
    size_mb = len(svg_data) / (1024 * 1024)
    print(f"  [SVG] Generated {out_path} ({size_mb:.2f} MB)")
    return out_path

def main():
    print("=== Building Grannie's Family Tree Website Assets (Compact Photo + Larger Text Engine) ===")

    search_index = {}
    tree_metadata = []

    for spec in TREE_SPECS:
        tree_id = spec['id']
        pdf_path = os.path.join(PDF_DIR, spec['file'])
        print(f"\nProcessing {tree_id}: {spec['name']}...")

        orig_doc = fitz.open(pdf_path)
        make_background_white_and_remove_frame(orig_doc)

        page = orig_doc[0]
        sw, sh = page.rect.width, page.rect.height

        # 1. Extract Person Entities (with compact photo & larger text footprint), Titles, and Connectors
        persons, titles, lines = extract_entities(page)
        print(f"  [EXTRACT] Extracted {len(persons)} people, {len(titles)} titles, {len(lines)} connectors")

        # 2. Optimize Layout: Shift people & titles away from Letter grid seams
        optimize_tree_layout(persons, titles, lines, sw, sh)

        # 3. Export SVG for web app
        export_svg(orig_doc, tree_id, SVG_DIR)

        # 4. Build Search Index from updated coordinates
        tree_search_persons = []
        for p in persons:
            cx = (p['rect'].x0 + p['rect'].x1) / 2
            cy = (p['rect'].y0 + p['rect'].y1) / 2
            tree_search_persons.append({
                'name': p['name'],
                'details': p['details'],
                'x': round(cx / sw, 5),
                'y': round(cy / sh, 5),
                'raw_x': round(cx, 1),
                'raw_y': round(cy, 1)
            })
        search_index[tree_id] = tree_search_persons
        print(f"  [INDEX] Indexed {len(tree_search_persons)} persons")

        # 5. Generate Printable Tiled PDF (Compact Photo + 15% Larger Text + Continuous Lines)
        tiles_out_path = os.path.join(TILES_DIR, f"{tree_id}_printable_tiles.pdf")
        tile_stats = generate_printable_tiles(orig_doc, persons, titles, lines, spec, tiles_out_path)

        tree_metadata.append({
            'id': tree_id,
            'name': spec['name'],
            'subtitle': spec['subtitle'],
            'description': spec['description'],
            'width_in': spec['width_in'],
            'height_in': spec['height_in'],
            'svg_width_pt': sw,
            'svg_height_pt': sh,
            'person_count': len(persons),
            'tile_pages': tile_stats['active_pages'],
            'total_pdf_pages': tile_stats['total_pdf_pages'],
            'grid_cols': tile_stats['grid_cols'],
            'grid_rows': tile_stats['grid_rows'],
            'total_grid_tiles': tile_stats['total_grid_tiles'],
            'skipped_empty': tile_stats['skipped_empty'],
            'tile_pdf': f"tiles/{tree_id}_printable_tiles.pdf",
            'svg_file': f"svg/{tree_id}.svg",
            'tiles': tile_stats['tiles'],
            'build_version': f"v3.2 • {datetime.datetime.now().strftime('%b %d, %Y %H:%M')}"
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
