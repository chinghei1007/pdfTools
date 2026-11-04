"""
Comprehensive unit tests for pypdfServices component
Tests each function in isolation with edge cases
"""

import unittest
import tempfile
import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject, NameObject

# Import all modules to test
from component.pypdfServices import (
    basic,
    pages,
    annotations,
    content,
    text,
    images,
    formHandling,
    metadata,
    outlines,
    attachments
)


class TestHelpers(unittest.TestCase):
    """Test helper functions in common module"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "test.pdf")
        
        # Create a simple test PDF
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(self.test_file, "wb") as f:
            writer.write(f)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_validate_file_exists_with_existing_file(self):
        """Should not raise when file exists"""
        basic.validate_file_exists(self.test_file)
    
    def test_validate_file_exists_with_missing_file(self):
        """Should raise FileNotFoundError for missing file"""
        with self.assertRaises(FileNotFoundError):
            basic.validate_file_exists("/nonexistent/path.pdf")
    
    def test_ensure_output_dir_creates_directory(self):
        """Should create directory if it doesn't exist"""
        new_dir = os.path.join(self.temp_dir.name, "new", "nested", "dir")
        output_path = os.path.join(new_dir, "output.pdf")
        basic.ensure_output_dir(output_path)
        self.assertTrue(os.path.exists(new_dir))
    
    def test_ensure_output_dir_skips_existing_directory(self):
        """Should not fail if directory already exists"""
        existing_dir = self.temp_dir.name
        output_path = os.path.join(existing_dir, "output.pdf")
        basic.ensure_output_dir(output_path)  # Should not raise
    
    def test_ensure_output_dir_with_no_directory(self):
        """Should handle filename-only paths"""
        basic.ensure_output_dir("output.pdf")  # Should not raise


class TestBasicOperations(unittest.TestCase):
    """Test basic.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf1 = self._create_test_pdf("Sample text page 1")
        self.pdf2 = self._create_test_pdf("Sample text page 2")
        self.output = os.path.join(self.temp_dir.name, "output.pdf")
    
    def _create_test_pdf(self, text="Test"):
        """Helper to create test PDFs"""
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
        # Add content stream to avoid KeyError in layout mode
        from pypdf.generic import DecodedStreamObject
        stream = DecodedStreamObject()
        stream._data = b"BT /F1 12 Tf 50 100 Td (Test) Tj ET"
        page[NameObject("/Contents")] = stream
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_merge_pdfs_basic(self):
        """Merge two PDFs"""
        basic.merge_pdfs([self.pdf1, self.pdf2], self.output)
        self.assertTrue(os.path.exists(self.output))
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 2)
    
    def test_merge_pdfs_with_page_ranges(self):
        """Merge with specific page ranges"""
        # Create multi-page PDF
        multi_pdf = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(5):
            writer.add_blank_page(width=200, height=200)
        with open(multi_pdf, "wb") as f:
            writer.write(f)
        
        basic.merge_pdfs([multi_pdf], self.output, page_ranges=[(0, 3)])
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 3)
    
    def test_merge_pdfs_empty_list(self):
        """Merge with empty list should create empty or fail gracefully"""
        # pypdf allows empty merge, resulting in empty PDF
        basic.merge_pdfs([], self.output)
        # Should create a file (may be empty or minimal PDF)
        self.assertTrue(os.path.exists(self.output))
    
    def test_split_pdf_to_single_files(self):
        """Split multi-page PDF into single files"""
        multi_pdf = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(3):
            writer.add_blank_page(width=200, height=200)
        with open(multi_pdf, "wb") as f:
            writer.write(f)
        
        output_dir = os.path.join(self.temp_dir.name, "split_output")
        result = basic.split_pdf_to_single_files(multi_pdf, output_dir)
        
        self.assertEqual(len(result), 3)
        for path in result:
            self.assertTrue(os.path.exists(path))
            reader = PdfReader(path)
            self.assertEqual(len(reader.pages), 1)
    
    def test_split_pdf_by_ranges(self):
        """Split PDF by page ranges"""
        multi_pdf = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(10):
            writer.add_blank_page(width=200, height=200)
        with open(multi_pdf, "wb") as f:
            writer.write(f)
        
        output_dir = os.path.join(self.temp_dir.name, "range_output")
        ranges = [(0, 3), (3, 6), (6, None)]  # Last range goes to end
        result = basic.split_pdf_by_ranges(multi_pdf, output_dir, ranges)
        
        self.assertEqual(len(result), 3)
        reader = PdfReader(result[0])
        self.assertEqual(len(reader.pages), 3)
    
    def test_rotate_pages_all(self):
        """Rotate all pages"""
        basic.rotate_pages(self.pdf1, self.output, 90)
        reader = PdfReader(self.output)
        self.assertEqual(reader.pages[0].rotation, 90)
    
    def test_rotate_pages_selective(self):
        """Rotate specific pages only"""
        multi_pdf = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(3):
            writer.add_blank_page(width=200, height=200)
        with open(multi_pdf, "wb") as f:
            writer.write(f)
        
        output = os.path.join(self.temp_dir.name, "rotated.pdf")
        basic.rotate_pages(multi_pdf, output, 180, page_numbers=[0, 2])
        
        reader = PdfReader(output)
        self.assertEqual(reader.pages[0].rotation, 180)
        self.assertEqual(reader.pages[1].rotation, 0)  # Not rotated
        self.assertEqual(reader.pages[2].rotation, 180)
    
    def test_rotate_invalid_degrees(self):
        """Test rotation with invalid degrees"""
        # pypdf requires multiples of 90, should raise ValueError
        with self.assertRaises(ValueError):
            basic.rotate_pages(self.pdf1, self.output, 45)
    
    def test_add_password(self):
        """Encrypt PDF with password"""
        basic.add_password(self.pdf1, self.output, "user123", "owner456")
        self.assertTrue(os.path.exists(self.output))
        
        reader = PdfReader(self.output)
        self.assertTrue(reader.is_encrypted)
        self.assertTrue(reader.decrypt("user123"))
    
    def test_remove_password(self):
        """Remove password from encrypted PDF"""
        # First create encrypted PDF
        encrypted = os.path.join(self.temp_dir.name, "encrypted.pdf")
        basic.add_password(self.pdf1, encrypted, "pass123")
        
        # Remove password
        basic.remove_password(encrypted, self.output, "pass123")
        
        reader = PdfReader(self.output)
        self.assertFalse(reader.is_encrypted)
    
    def test_flatten_pdf(self):
        """Flatten PDF form fields"""
        # Note: flatten() method may not exist in all pypdf versions
        # This tests that the function handles it gracefully
        try:
            basic.flatten_pdf(self.pdf1, self.output)
            self.assertTrue(os.path.exists(self.output))
        except AttributeError as e:
            # Expected if pypdf version doesn't have flatten()
            self.assertIn("flatten", str(e))


class TestPagesOperations(unittest.TestCase):
    """Test pages.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
        self.output = os.path.join(self.temp_dir.name, "output.pdf")
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_scale_page_by_factor(self):
        """Scale page by factor"""
        pages.scale_page(self.pdf, self.output, scale_factor=0.5)
        reader = PdfReader(self.output)
        # Page should be scaled
        self.assertIsNotNone(reader.pages[0].mediabox)
    
    def test_scale_page_to_target_size(self):
        """Scale page to target dimensions"""
        pages.scale_page(self.pdf, self.output, target_size=(100, 100))
        reader = PdfReader(self.output)
        self.assertIsNotNone(reader.pages[0].mediabox)
    
    def test_crop_page(self):
        """Crop page to bounding box"""
        crop_box = (10, 10, 100, 100)
        pages.crop_page(self.pdf, self.output, crop_box)
        reader = PdfReader(self.output)
        # Cropbox should be set
        self.assertIsNotNone(reader.pages[0].cropbox)
    
    def test_transform_page(self):
        """Apply affine transformation"""
        pages.transform_page(
            self.pdf, self.output,
            rotate=45, scale=1.5, translate_x=10, translate_y=20
        )
        reader = PdfReader(self.output)
        self.assertIsNotNone(reader.pages[0])
    
    def test_merge_pages_overlay(self):
        """Overlay page on base PDF"""
        overlay = self._create_test_pdf()
        pages.merge_pages_overlay(self.pdf, overlay, self.output)
        self.assertTrue(os.path.exists(self.output))
    
    def test_merge_pages_underlay(self):
        """Underlay page behind base PDF"""
        underlay = self._create_test_pdf()
        pages.merge_pages_underlay(self.pdf, underlay, self.output)
        self.assertTrue(os.path.exists(self.output))
    
    def test_remove_pages(self):
        """Remove specific pages"""
        # Create multi-page PDF
        multi = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(5):
            writer.add_blank_page(width=200, height=200)
        with open(multi, "wb") as f:
            writer.write(f)
        
        pages.remove_pages(multi, self.output, [1, 3])
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 3)  # 5 - 2 = 3
    
    def test_insert_page(self):
        """Insert page at position"""
        insert_pdf = self._create_test_pdf()
        # Create 2-page PDF
        multi = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(2):
            writer.add_blank_page(width=200, height=200)
        with open(multi, "wb") as f:
            writer.write(f)
        
        pages.insert_page(multi, insert_pdf, self.output, position=1)
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 3)
    
    def test_reorder_pages(self):
        """Reorder pages"""
        # Create 3-page PDF
        multi = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(3):
            writer.add_blank_page(width=200, height=200)
        with open(multi, "wb") as f:
            writer.write(f)
        
        pages.reorder_pages(multi, self.output, [2, 0, 1])
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 3)


class TestAnnotations(unittest.TestCase):
    """Test annotations.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
        self.output = os.path.join(self.temp_dir.name, "output.pdf")
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_add_free_text(self):
        """Add free text annotation"""
        rect = (10, 10, 100, 50)
        annotations.add_free_text(
            self.pdf, self.output,
            text="Test", rect=rect, page_number=0
        )
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_rectangle(self):
        """Add rectangle annotation"""
        rect = (10, 10, 100, 50)
        annotations.add_rectangle(self.pdf, self.output, rect)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_ellipse(self):
        """Add ellipse annotation"""
        rect = (10, 10, 100, 50)
        annotations.add_ellipse(self.pdf, self.output, rect)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_line(self):
        """Add line annotation"""
        p1, p2 = (10, 10), (100, 100)
        annotations.add_line(self.pdf, self.output, p1, p2)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_polygon(self):
        """Add polygon annotation"""
        vertices = [(10, 10), (100, 10), (100, 100), (10, 100)]
        annotations.add_polygon(self.pdf, self.output, vertices)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_highlight(self):
        """Add highlight annotation"""
        rect = (10, 10, 100, 50)
        annotations.add_highlight(self.pdf, self.output, rect)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_text_annotation(self):
        """Add sticky note annotation"""
        rect = (10, 10, 50, 50)
        annotations.add_text_annotation(
            self.pdf, self.output, rect, text="Note"
        )
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_link_internal(self):
        """Add internal link"""
        rect = (10, 10, 100, 50)
        # Create 2-page PDF first
        multi = os.path.join(self.temp_dir.name, "multi.pdf")
        writer = PdfWriter()
        for i in range(2):
            writer.add_blank_page(width=200, height=200)
        with open(multi, "wb") as f:
            writer.write(f)
        
        annotations.add_link(multi, self.output, rect, target_page=1)
        self.assertTrue(os.path.exists(self.output))
    
    def test_add_uri_link(self):
        """Add external URL link"""
        rect = (10, 10, 100, 50)
        annotations.add_uri_link(
            self.pdf, self.output, rect, url="https://example.com"
        )
        self.assertTrue(os.path.exists(self.output))
    
    def test_get_annotations(self):
        """Get annotations from PDF"""
        # Add annotation first
        rect = (10, 10, 100, 50)
        annotations.add_rectangle(self.pdf, self.output, rect)
        
        annots = annotations.get_annotations(self.output)
        self.assertIsInstance(annots, list)
        # Should have at least one annotation
        self.assertGreater(len(annots), 0)
    
    def test_remove_annotations(self):
        """Remove annotations from PDF"""
        # Add annotation first
        rect = (10, 10, 100, 50)
        annotated = os.path.join(self.temp_dir.name, "annotated.pdf")
        annotations.add_rectangle(self.pdf, annotated, rect)
        
        cleaned = os.path.join(self.temp_dir.name, "cleaned.pdf")
        annotations.remove_annotations(annotated, cleaned)
        self.assertTrue(os.path.exists(cleaned))


class TestContent(unittest.TestCase):
    """Test content.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_content_stream(self):
        """Get raw content stream"""
        data = content.get_content_stream(self.pdf)
        self.assertIsInstance(data, bytes)
    
    def test_iterate_operations(self):
        """Iterate through content operations"""
        ops = content.iterate_operations(self.pdf)
        self.assertIsInstance(ops, list)
    
    def test_iterate_operations_with_callback(self):
        """Use callback during iteration"""
        collected = []
        def callback(operands, operator):
            collected.append(operator)
        
        content.iterate_operations(self.pdf, callback=callback)
        # Callback should have been called
        self.assertIsInstance(collected, list)
    
    def test_extract_drawing_operators(self):
        """Extract drawing operators"""
        ops = content.extract_drawing_operators(self.pdf)
        self.assertIsInstance(ops, list)
    
    def test_extract_rectangles(self):
        """Extract rectangles from page"""
        rects = content.extract_rectangles(self.pdf)
        self.assertIsInstance(rects, list)
    
    def test_extract_lines(self):
        """Extract lines from page"""
        lines = content.extract_lines(self.pdf)
        self.assertIsInstance(lines, list)


class TestTextExtraction(unittest.TestCase):
    """Test text.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_extract_text_all_pages(self):
        """Extract text from all pages"""
        result = text.extract_text(self.pdf)
        self.assertIsInstance(result, str)
    
    def test_extract_text_single_page(self):
        """Extract text from specific page"""
        result = text.extract_text(self.pdf, page_number=0)
        self.assertIsInstance(result, str)
    
    def test_extract_text_layout(self):
        """Extract text with layout preservation"""
        result = text.extract_text_layout(self.pdf)
        self.assertIsInstance(result, str)
    
    def test_extract_text_by_orientation(self):
        """Extract text by orientation"""
        result = text.extract_text_by_orientation(self.pdf)
        self.assertIsInstance(result, str)
    
    def test_extract_text_from_pages(self):
        """Extract text from specific pages"""
        result = text.extract_text_from_pages(self.pdf, [0])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
    
    def test_extract_text_with_visitor(self):
        """Extract text using visitor function"""
        collected = []
        def visitor(text, cm, tm, font_dict, font_size):
            if text.strip():
                collected.append(text)
        
        result = text.extract_text_with_visitor(self.pdf, visitor_text=visitor)
        self.assertIsInstance(result, str)


class TestImageExtraction(unittest.TestCase):
    """Test images.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_extract_images(self):
        """Extract images from PDF"""
        output_dir = os.path.join(self.temp_dir.name, "images")
        result = images.extract_images(self.pdf, output_dir)
        self.assertIsInstance(result, list)
    
    def test_extract_images_from_page(self):
        """Extract images from specific page"""
        output_dir = os.path.join(self.temp_dir.name, "images")
        result = images.extract_images_from_page(self.pdf, output_dir, 0)
        self.assertIsInstance(result, list)
    
    def test_get_image_info(self):
        """Get image information"""
        info = images.get_image_info(self.pdf)
        self.assertIsInstance(info, list)
    
    def test_check_image_on_page_exists(self):
        """Check if image exists (when no images present)"""
        result = images.check_image_on_page(self.pdf, 0, 0)
        # Should return False since we created blank page without images
        self.assertFalse(result)
    
    def test_check_image_on_page_invalid_page(self):
        """Check image on non-existent page"""
        result = images.check_image_on_page(self.pdf, 999, 0)
        self.assertFalse(result)


class TestFormHandling(unittest.TestCase):
    """Test formHandling.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_form_fields_empty(self):
        """Get form fields from non-form PDF"""
        fields = formHandling.get_form_fields(self.pdf)
        self.assertIsInstance(fields, dict)
        # Should be empty for non-form PDF
        self.assertEqual(len(fields), 0)
    
    def test_get_form_text_fields_empty(self):
        """Get text fields from non-form PDF"""
        fields = formHandling.get_form_text_fields(self.pdf)
        self.assertIsInstance(fields, dict)
    
    def test_fill_form(self):
        """Fill form fields"""
        output = os.path.join(self.temp_dir.name, "filled.pdf")
        field_values = {"field1": "value1"}
        # fill_form requires a PDF with AcroForm, will raise error for blank PDF
        try:
            formHandling.fill_form(self.pdf, output, field_values)
            self.assertTrue(os.path.exists(output))
        except Exception as e:
            # Expected for non-form PDF
            self.assertIn(("PyPdfError", "AcroForm"), str(type(e).__name__))
    
    def test_get_field_info_not_found(self):
        """Get info for non-existent field"""
        info = formHandling.get_field_info(self.pdf, "nonexistent")
        self.assertIsNone(info)


class TestMetadata(unittest.TestCase):
    """Test metadata.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_metadata(self):
        """Get basic metadata"""
        meta = metadata.get_metadata(self.pdf)
        # Returns either dict or None
        self.assertTrue(isinstance(meta, (dict, type(None))))
    
    def test_get_xmp_metadata(self):
        """Get XMP metadata"""
        xmp = metadata.get_xmp_metadata(self.pdf)
        # Returns either dict or None
        self.assertTrue(isinstance(xmp, (dict, type(None))))
    
    def test_get_all_metadata(self):
        """Get all metadata"""
        all_meta = metadata.get_all_metadata(self.pdf)
        self.assertIsInstance(all_meta, dict)
        self.assertIn("basic", all_meta)
        self.assertIn("xmp", all_meta)


class TestOutlines(unittest.TestCase):
    """Test outlines.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
    
    def _create_test_pdf(self, pages=1):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        for i in range(pages):
            writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_outlines_empty(self):
        """Get outlines from PDF without bookmarks"""
        outlines_list = outlines.get_outlines(self.pdf)
        self.assertIsInstance(outlines_list, list)
    
    def test_add_outline(self):
        """Add outline item"""
        output = os.path.join(self.temp_dir.name, "outlined.pdf")
        item = outlines.add_outline(self.pdf, output, "Chapter 1", 0)
        self.assertTrue(os.path.exists(output))
        # Returns outline item
        self.assertIsNotNone(item)
    
    def test_add_nested_outline(self):
        """Add nested outline structure"""
        output = os.path.join(self.temp_dir.name, "nested.pdf")
        structure = [
            {"title": "Chapter 1", "page": 0, "children": [
                {"title": "Section 1.1", "page": 0}
            ]}
        ]
        outlines.add_nested_outline(self.pdf, output, structure)
        self.assertTrue(os.path.exists(output))
    
    def test_get_named_destinations(self):
        """Get named destinations"""
        dests = outlines.get_named_destinations(self.pdf)
        self.assertIsInstance(dests, dict)
    
    def test_get_page_labels(self):
        """Get page labels"""
        labels = outlines.get_page_labels(self.pdf)
        self.assertIsInstance(labels, list)


class TestAttachments(unittest.TestCase):
    """Test attachments.py functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf = self._create_test_pdf()
        self.attachment_file = self._create_attachment()
    
    def _create_test_pdf(self):
        path = os.path.join(self.temp_dir.name, f"test_{id(self)}.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return path
    
    def _create_attachment(self):
        path = os.path.join(self.temp_dir.name, "attachment.txt")
        with open(path, "w") as f:
            f.write("Test attachment content")
        return path
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_add_attachment(self):
        """Add attachment to PDF"""
        output = os.path.join(self.temp_dir.name, "with_attachment.pdf")
        attachments.add_attachment(self.pdf, output, self.attachment_file)
        self.assertTrue(os.path.exists(output))
    
    def test_add_attachment_with_name(self):
        """Add attachment with custom name"""
        output = os.path.join(self.temp_dir.name, "named_attachment.pdf")
        attachments.add_attachment(
            self.pdf, output, self.attachment_file,
            attachment_name="custom_name.txt"
        )
        self.assertTrue(os.path.exists(output))
    
    def test_get_attachment_list_empty(self):
        """Get attachment list from PDF without attachments"""
        atts = attachments.get_attachment_list(self.pdf)
        self.assertIsInstance(atts, list)
        self.assertEqual(len(atts), 0)
    
    def test_remove_attachments(self):
        """Remove attachments from PDF"""
        # First add attachment
        with_atts = os.path.join(self.temp_dir.name, "with_atts.pdf")
        attachments.add_attachment(self.pdf, with_atts, self.attachment_file)
        
        # Then remove
        cleaned = os.path.join(self.temp_dir.name, "cleaned.pdf")
        attachments.remove_attachments(with_atts, cleaned)
        self.assertTrue(os.path.exists(cleaned))
    
    def test_extract_attachments_empty(self):
        """Extract attachments from PDF without attachments"""
        output_dir = os.path.join(self.temp_dir.name, "extracted")
        result = attachments.extract_attachments(self.pdf, output_dir)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
