import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit_tools_bundle.app import AuditToolsApp


def main() -> None:
    app = AuditToolsApp()
    app.update()
    for index in range(len(app.notebook.tabs())):
        app.notebook.select(index)
        app._load_selected()
        app.update()
    loaded = sorted(app._loaded)
    app.destroy()
    expected = ["file_renamer", "fund_calculator", "medical_record"]
    if loaded != expected:
        raise RuntimeError(f"标签页未全部加载：{loaded}")
    print("GUI smoke passed:", ", ".join(loaded))


if __name__ == "__main__":
    main()
