"""
Generate a clean, standard, valid multi-page PDF document
containing the sample legal contract with zero external dependencies.
"""

def generate_pdf(filename, text_content):
    text_content = text_content.replace('₹', 'Rs. ')
    lines = text_content.strip().split('\n')
    
    # Break into pages (~45 lines per page)
    lines_per_page = 44
    pages = []
    current_page = []
    
    for line in lines:
        current_page.append(line)
        if len(current_page) >= lines_per_page:
            pages.append(current_page)
            current_page = []
    if current_page:
        pages.append(current_page)
        
    num_pages = len(pages)
    
    # PDF objects
    objects = []
    
    def add_obj(content):
        objects.append(content)
        return len(objects) # 1-indexed obj number

    # 1: Catalog
    catalog_id = add_obj("<< /Type /Catalog /Pages 2 0 R >>")
    
    # 2: Pages (placeholder, will fill with page ids)
    pages_id = add_obj("") # placeholder
    
    # 3: Font
    font_id = add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    
    page_ids = []
    for page_num, page_lines in enumerate(pages, 1):
        # Build stream text
        stream_parts = ["BT"]
        stream_parts.append("/F1 10 Tf")
        stream_parts.append("14 TL")
        stream_parts.append("50 780 Td")
        
        for l in page_lines:
            # Escape PDF text characters
            safe = l.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            if any(h in l for h in ['AGREEMENT', 'BETWEEN:', 'WITNESSETH', 'CLAUSES', 'IN WITNESS', 'FIRST PARTY', 'SECOND PARTY']):
                stream_parts.append(f"/F2 10.5 Tf ({safe}) Tj T* /F1 10 Tf")
            else:
                stream_parts.append(f"({safe}) Tj T*")
                
        # Footer
        stream_parts.append(f"0 0 Td (Page {page_num} of {num_pages}) Tj ET")
        stream_content = "\n".join(stream_parts)
        stream_bytes = stream_content.encode('latin1', errors='replace')
        
        content_id = add_obj(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream")
        page_id = add_obj(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R /F2 {font_bold_id} 0 R >> >> >>")
        page_ids.append(f"{page_id} 0 R")
        
    # Update Pages object
    objects[1] = f"<< /Type /Pages /Kids [ {' '.join(page_ids)} ] /Count {num_pages} >>"
    
    # Write full PDF
    with open(filename, 'wb') as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, obj in enumerate(objects, 1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n{obj}\nendobj\n".encode('latin1'))
            
        xref_offset = f.tell()
        f.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode('latin1'))
        for off in offsets:
            f.write(f"{off:010d} 00000 n \n".encode('latin1'))
            
        f.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode('latin1'))

if __name__ == '__main__':
    with open('sample_legal_contract.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    generate_pdf('sample_legal_contract.pdf', text)
    print("Generated sample_legal_contract.pdf successfully!")
