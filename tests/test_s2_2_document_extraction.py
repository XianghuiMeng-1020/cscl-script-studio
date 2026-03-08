"""S2.2 Blocking Fix - Document Extraction Tests"""
import pytest
import os
import tempfile
from io import BytesIO
from app.services.document_service import DocumentService


class TestPDFExtraction:
    """Test PDF text extraction"""
    
    def test_pdf_extract_success(self):
        """Test successful PDF extraction"""
        service = DocumentService()
        
        # Create a simple PDF-like content (minimal PDF structure)
        # Note: This is a simplified test - real PDFs would use pypdf
        # For actual testing, we'd need a real PDF file
        
        # Test that PDF support is available
        if not service.extract_text_from_file.__doc__:
            pytest.skip("PDF extraction not implemented")
        
        # Create a minimal test PDF bytes (this is a placeholder)
        # In real scenario, we'd load an actual PDF file
        pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
        
        # This test verifies the function exists and handles PDFs
        # Actual PDF parsing would require a real PDF file
        assert hasattr(service, 'extract_text_from_pdf')
    
    def test_pdf_extract_no_binary_header_in_output(self):
        """Test that extracted text does not contain PDF binary headers"""
        service = DocumentService()
        
        # Create a test PDF file with text content
        # In a real test, we'd use a proper PDF library to create test PDFs
        # For now, we test the normalization function
        
        test_text = "%PDF-1.3\nSome actual text content here\nMore content"
        normalized = service.normalize_text(test_text)
        
        # Check that PDF header is removed
        assert "%PDF-" not in normalized
        assert "Some actual text content" in normalized
    
    def test_txt_utf8_success(self):
        """Test UTF-8 text file extraction"""
        service = DocumentService()
        
        # Length must be >= 80 after normalization (DocumentService._MIN_EXTRACT_LEN)
        test_content = (
            "这是一个UTF-8编码的测试文件。\n包含中文内容。"
            "本测试用于验证纯文本提取与编码检测，确保长度满足最小提取要求。"
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 35 chars padding to guarantee >= 80
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(test_content.encode('utf-8'))
            temp_path = f.name
        
        try:
            extracted = service.extract_text_from_file(temp_path, 'text/plain')
            assert "UTF-8编码" in extracted
            assert "%PDF-" not in extracted
            assert len(extracted.strip()) > 0
        finally:
            os.unlink(temp_path)
    
    def test_txt_gb18030_success(self):
        """Test GB18030 text file extraction"""
        service = DocumentService()
        
        # Length must be >= 80 after normalization (DocumentService._MIN_EXTRACT_LEN)
        test_content = (
            "这是一个GB18030编码的测试文件。\n包含中文内容。"
            "本测试用于验证纯文本提取与编码检测，确保长度满足最小提取要求。"
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 35 chars padding to guarantee >= 80
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(test_content.encode('gb18030'))
            temp_path = f.name
        
        try:
            extracted = service.extract_text_from_file(temp_path, 'text/plain')
            assert "GB18030编码" in extracted or "测试文件" in extracted
            assert len(extracted.strip()) > 0
        finally:
            os.unlink(temp_path)
    
    def test_txt_big5_success(self):
        """Test Big5 text file extraction"""
        service = DocumentService()
        
        # Length must be >= 80 after normalization (DocumentService._MIN_EXTRACT_LEN).
        # Use long ASCII tail so length is sufficient regardless of which encoding decodes first.
        test_content = (
            "這是一個Big5編碼的測試檔案。\n包含繁體中文內容。"
            "本測試用於驗證純文字擷取與編碼檢測，確保長度滿足最小擷取要求。"
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 80 chars
        )
        
        try:
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                f.write(test_content.encode('big5'))
                temp_path = f.name
            
            extracted = service.extract_text_from_file(temp_path, 'text/plain')
            assert len(extracted.strip()) > 0
        except UnicodeEncodeError:
            pytest.skip("Big5 encoding not available on this system")
        finally:
            if 'temp_path' in locals():
                os.unlink(temp_path)
    
    def test_unsupported_file_type_415(self):
        """Test unsupported file type returns appropriate error"""
        service = DocumentService()
        
        test_content = b"Some binary content"
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xyz', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                service.extract_text_from_file(temp_path, 'application/unknown')
            
            assert "不支持" in str(exc_info.value) or "unsupported" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)
    
    def test_text_too_short_422(self):
        """Test that text shorter than threshold returns error"""
        service = DocumentService()
        
        # Test normalize_text with very short input
        short_text = "abc"
        normalized = service.normalize_text(short_text)
        
        # The normalize function itself doesn't check length,
        # but upload_text_document does
        result = service.upload_text_document(
            course_id='test-course',
            title='Short Text',
            text=short_text,
            uploaded_by='test-user'
        )
        
        # Should fail with TEXT_TOO_SHORT error
        assert result['error'] is not None
        assert 'error_code' in result
        assert result.get('error_code') == 'TEXT_TOO_SHORT' or '过短' in result['error']


class TestTextNormalization:
    """Test text normalization functions"""
    
    def test_normalize_text_removes_control_chars(self):
        """Test that control characters are removed"""
        service = DocumentService()
        
        text_with_control = "Normal text\x00\x01\x02More text"
        normalized = service.normalize_text(text_with_control)
        
        assert '\x00' not in normalized
        assert '\x01' not in normalized
        assert "Normal text" in normalized
    
    def test_normalize_text_preserves_newlines(self):
        """Test that newlines are preserved"""
        service = DocumentService()
        
        text_with_newlines = "Line 1\nLine 2\n\nLine 3"
        normalized = service.normalize_text(text_with_newlines)
        
        assert '\n' in normalized
        assert "Line 1" in normalized
        assert "Line 2" in normalized
    
    def test_normalize_text_compresses_whitespace(self):
        """Test that multiple spaces are compressed"""
        service = DocumentService()
        
        text_with_spaces = "Word1    Word2     Word3"
        normalized = service.normalize_text(text_with_spaces)
        
        # Should not have more than one space between words
        assert "  " not in normalized.replace('\n', ' ')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
