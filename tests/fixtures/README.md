# Test Fixtures

This directory contains PDF files used by `tests/runner.py`.

## Built-In Acceptance Fixtures
1. `fixture_accessible.pdf`: Synthetic accessible document with title metadata, language tag (`en`), structure tree (`/StructTreeRoot`), and extractable text.
2. `fixture_scanned.pdf`: Synthetic scanned document with no title, no language tag, no structure tree, and empty text stream.
3. `fixture_images.pdf`: Document containing an embedded raster image resource.

## Team-Supplied Test PDFs
Any additional `.pdf` files placed in this folder will be automatically discovered and evaluated when running:
```bash
python -m tests.runner
```
Or specify a custom directory:
```bash
python -m tests.runner path/to/custom_pdfs/
```
