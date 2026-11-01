"""Builds small PDFs with known accessibility properties for use as test fixtures.

Because each fixture is generated from explicit settings, the expected result of
every check is known independently of the checker (this is the test oracle).
"""


def _build(text, title, lang, tagged, pages, text_pages, images, pad):
    first_page = 5
    info_id = first_page + 2 * pages
    struct_id = info_id + 1
    objs = {}

    catalog = "<< /Type /Catalog /Pages 2 0 R"
    if lang:
        catalog += f" /Lang ({lang})"
    if tagged:
        catalog += f" /MarkInfo << /Marked true >> /StructTreeRoot {struct_id} 0 R"
    catalog += " >>"
    objs[1] = catalog.encode()

    kids = [first_page + 2 * i for i in range(pages)]
    objs[2] = ("<< /Type /Pages /Kids [" + " ".join(f"{k} 0 R" for k in kids)
               + f"] /Count {pages} >>").encode()
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objs[4] = (b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 "
               b"/ColorSpace /DeviceGray /BitsPerComponent 8 /Length 1 >>\n"
               b"stream\n\x00\nendstream")

    for i in range(pages):
        number = i + 1
        page_id = first_page + 2 * i
        content_id = page_id + 1
        resources = "/Font << /F1 3 0 R >>"
        if number in images:
            resources += " /XObject << /Im0 4 0 R >>"
        objs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R /Resources << {resources} >> >>").encode()
        stream = b""
        if text and number in text_pages:
            stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objs[content_id] = (b"<< /Length %d >>\nstream\n" % len(stream)
                            + stream + b"\nendstream")

    objs[info_id] = (f"<< /Title ({title}) >>" if title else "<< >>").encode()
    objs[struct_id] = b"<< /Type /StructTreeRoot >>"

    out = bytearray(b"%PDF-1.7\n")
    line = b"%" + b"x" * 998 + b"\n"
    remaining = pad
    while remaining > 0:
        if remaining >= len(line):
            out += line
            remaining -= len(line)
        else:
            out += b"%" + b"x" * max(remaining - 2, 0) + b"\n"
            remaining = 0

    offsets = {}
    for number in sorted(objs):
        offsets[number] = len(out)
        out += b"%d 0 obj\n" % number + objs[number] + b"\nendobj\n"

    xref_at = len(out)
    size = max(objs) + 1
    out += b"xref\n0 %d\n0000000000 65535 f \n" % size
    for number in range(1, size):
        out += b"%010d 00000 n \n" % offsets[number]
    out += (f"trailer\n<< /Size {size} /Root 1 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


def make_pdf(text="Hello accessible world", title=None, lang=None, tagged=False,
             pages=1, text_pages=None, images=(), size=None):
    """Return the bytes of a PDF.

    text        text drawn on pages in text_pages (None draws no text anywhere)
    title, lang document title and language (None leaves them unset)
    tagged      include a structure tree
    pages       number of pages
    text_pages  1-based pages that carry text (default: all)
    images      1-based pages that reference an image resource
    size        pad the file to exactly this many bytes
    """
    text_pages = set(range(1, pages + 1)) if text_pages is None else set(text_pages)
    images = set(images)
    data = _build(text, title, lang, tagged, pages, text_pages, images, 0)
    if size is None:
        return data
    pad = size - len(data)
    for _ in range(5):
        data = _build(text, title, lang, tagged, pages, text_pages, images, pad)
        if len(data) == size:
            return data
        pad += size - len(data)
    raise RuntimeError("could not pad the PDF to the requested size")


def problemset6_like():
    """Same properties as problemset6.pdf from the handoff: 2 pages, a title, no language,
    no structure tree, no extractable text, one image resource on page 2."""
    return make_pdf(title="Microsoft Word - Assignment-6", lang=None, tagged=False,
                    pages=2, text_pages=(), images=(2,))


def accessible_test_like():
    """Same properties as accessible_test.pdf: 1 page with text, language en, a structure
    tree, and no title."""
    return make_pdf(title=None, lang="en", tagged=True, pages=1)
