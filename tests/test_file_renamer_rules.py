from components.file_renamer.legacy_app import FileRenameApp


class Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def make_app():
    return FileRenameApp.__new__(FileRenameApp)


def test_date_format_mapping():
    app = make_app()
    assert app.parse_date_format("YYYY-MM-DD") == "%Y-%m-%d"
    assert app.parse_date_format("unknown") == "%Y%m%d"


def test_sequence_filename_detection_and_next_number():
    app = make_app()
    assert app.is_sequence_filename_format("01_报告_20260913.docx")
    assert app.is_sequence_filename_format("9_报告_26-09-13.pdf")
    assert not app.is_sequence_filename_format("报告_20260913.docx")
    assert app.get_next_sequence_number(["01_甲_20260913.docx", "12_乙_20260913.pdf", "其他.txt"]) == 13


def test_target_extension_prefers_selected_then_custom():
    app = make_app()
    app.extension_var = Value("pdf")
    app.custom_ext_var = Value("docx")
    assert app.get_target_extension() == "pdf"
    app.extension_var = Value("不修改")
    assert app.get_target_extension() == "docx"

