import os
import pymupdf

def generate():
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Hello World", fontsize=12)
    doc.save("sample.pdf")
    doc.close()

    doc = pymupdf.open("sample.pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=72)
    pix.save("sample.png")
    doc.close()
    
    try:
        from docx import Document
        doc = Document()
        doc.add_paragraph('Hello World')
        doc.save('sample.docx')
    except ImportError:
        with open("sample.docx", "wb") as f:
            f.write(b"Dummy DOCX")
            
    with open("sample.xlsx", "wb") as f:
        f.write(b"Dummy XLSX")
        
    with open("sample.pptx", "wb") as f:
        f.write(b"Dummy PPTX")

if __name__ == '__main__':
    generate()
