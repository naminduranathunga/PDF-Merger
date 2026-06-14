import math
from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation
from logic.merge_exceptions import MergeCancelledError

def generate_n_up_pdf(input_writer, output_path, options, progress_callback=None, cancel_callback=None):
    """
    Generates a PDF where multiple pages are placed on one page.
    options: {
        'n_up': int, 
        'page_size': (width, height),
        'cols': int,
        'rows': int,
        'gap': float,
        'margin': float,
        'show_border': bool,
        'orientation': str # "v-v", "v-h", "h-v", "h-h" - Note: handled by rows/cols mostly
    }
    """
    # Create a temporary reader from the current writer content
    # Since PdfWriter doesn't directly allow reading back easily without saving,
    # we assume input_writer is a list of PageObjects or similar, but PdfWriter is what we have.
    # We'll write to a temporary buffer if needed, or just iterate pages.
    
    def report_progress(current, total, status=None):
        if progress_callback:
            progress_callback(current, total, status)

    def check_cancelled():
        if cancel_callback and cancel_callback():
            raise MergeCancelledError()

    source_pages = input_writer.pages
    total_source_pages = len(source_pages)
    
    n = options.get('n_up', 1)
    cols = options.get('cols', 1)
    rows = options.get('rows', 1)
    page_width, page_height = options.get('page_size', (595, 842)) # A4 default
    margin = options.get('margin', 20)
    gap = options.get('gap', 10)
    show_border = options.get('show_border', False)

    # Calculate usable area
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)

    # Calculate individual page slot size
    slot_width = (usable_width - (cols - 1) * gap) / cols
    slot_height = (usable_height - (rows - 1) * gap) / rows

    new_writer = PdfWriter()
    
    current_source_idx = 0
    report_progress(0, total_source_pages, "Building N-up layout...")
    while current_source_idx < total_source_pages:
        check_cancelled()
        # Create a new blank output page
        new_page = PageObject.create_blank_page(None, page_width, page_height)
        
        for r in range(rows):
            for c in range(cols):
                if current_source_idx >= total_source_pages:
                    break
                check_cancelled()
                
                src_page = source_pages[current_source_idx]
                
                # Check if we need to rotate source (Orientation mode 2, 3 = Horizontal Source)
                orient_mode = options.get('orientation_mode', 0)
                source_is_h = (orient_mode >= 2)
                
                # Current source dimensions
                src_width = float(src_page.mediabox.width)
                src_height = float(src_page.mediabox.height)
                
                # Apply rotation if needed
                rotation = 0
                if source_is_h:
                    # If it's already wider than tall, maybe it's already horizontal.
                    # But the setting explicitly asks to TREAT it as horizontal.
                    if src_height > src_width:
                        rotation = 90
                        src_width, src_height = src_height, src_width
                
                scale_x = slot_width / src_width
                scale_y = slot_height / src_height
                scale = min(scale_x, scale_y)
                
                scaled_w = src_width * scale
                scaled_h = src_height * scale
                
                # Calculate offsets to center in slot
                slot_top = page_height - margin - r * (slot_height + gap)
                slot_bottom = slot_top - slot_height
                
                offset_x = margin + c * (slot_width + gap) + (slot_width - scaled_w) / 2
                offset_y = slot_bottom + (slot_height - scaled_h) / 2

                # Apply transformation
                trans = Transformation().scale(scale, scale)
                if rotation:
                    # Rotate around center of the scaled page
                    trans = trans.rotate(rotation).translate(scaled_w if rotation == 90 else 0, 0)
                
                trans = trans.translate(offset_x, offset_y)
                src_page.add_transformation(trans)
                
                # Merge into new page
                new_page.merge_page(src_page)
                
                # TODO: Add border if requested (requires canvas/reportlab or complex PDF ops)
                # For now, we'll focus on the layout logic.
                
                current_source_idx += 1
                report_progress(current_source_idx, total_source_pages, f"Placing page {current_source_idx} of {total_source_pages}...")
            if current_source_idx >= total_source_pages:
                break
                
        new_writer.add_page(new_page)

    check_cancelled()
    report_progress(total_source_pages, total_source_pages, "Writing output file...")
    with open(output_path, "wb") as f:
        new_writer.write(f)
