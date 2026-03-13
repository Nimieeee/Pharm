import pytest
from app.services.postprocessing.export_processor import ExportProcessor

class TestExportProcessor:
    @pytest.fixture
    def processor(self):
        return ExportProcessor()

    def test_svg_sanitization_removes_script_tags(self, processor):
        """SVG with <script> tags must be sanitized."""
        dirty_svg = '<svg><script>alert("xss")</script><path d="M10 10"/></svg>'
        sanitized = processor.sanitize_svg(dirty_svg)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert '<path d="M10 10"/>' in sanitized

    def test_svg_sanitization_removes_event_handlers(self, processor):
        """SVG with event handlers must be sanitized."""
        dirty_svg = '<svg onload="alert(1)" onclick=\'console.log("x")\'><rect x="0" y="0"/></svg>'
        sanitized = processor.sanitize_svg(dirty_svg)
        assert "onload" not in sanitized
        assert "onclick" not in sanitized
        assert '<rect x="0" y="0"/>' in sanitized

    def test_csv_format_escapes_commas(self, processor):
        """CSV values containing commas must be quoted."""
        columns = ["Name", "Description"]
        data = [
            ["Aspirin", "Common, reliable painkiller"],
            {"Name": "Diazepam", "Description": "Sedative, used for anxiety"}
        ]
        csv_output = processor.format_csv(data, columns)
        
        # Check if rows are present
        assert "Aspirin" in csv_output
        assert '"Common, reliable painkiller"' in csv_output
        assert "Diazepam" in csv_output
        assert '"Sedative, used for anxiety"' in csv_output

    def test_csv_format_handles_unicode(self, processor):
        """CSV must handle UTF-8 characters correctly."""
        columns = ["Symbol", "Name"]
        data = [["α", "Alpha"], ["β", "Beta"]]
        csv_output = processor.format_csv(data, columns)
        assert "α" in csv_output
        assert "β" in csv_output

    def test_json_export_pretty_print(self, processor):
        """JSON export should be pretty printed."""
        data = {"key": "value", "list": [1, 2, 3]}
        json_output = processor.format_json_export(data)
        assert '"key": "value"' in json_output
        assert '  "list": [' in json_output  # Check for indentation
