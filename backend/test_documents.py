import tempfile
from io import BytesIO

from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from app.services.documents import DocumentStore, extract_text


with tempfile.TemporaryDirectory() as directory:
    store = DocumentStore(f"{directory}/test.db")
    store.initialize()
    text = extract_text("contract.txt", b"Payment is due on 1 June.")
    doc_id = store.save(text, "contract.txt")
    assert store.get_text(doc_id) == "Payment is due on 1 June."

    docx = Document()
    docx.add_paragraph("DOCX clause")
    docx_bytes = BytesIO()
    docx.save(docx_bytes)
    assert extract_text("contract.docx", docx_bytes.getvalue()) == "DOCX clause"

    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 10 10 Td (PDF clause) Tj ET")
    page[NameObject("/Contents")] = content
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    assert extract_text("contract.pdf", pdf_bytes.getvalue()) == "PDF clause"
