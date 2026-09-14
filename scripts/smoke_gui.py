import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit_tools_bundle.app import FlightInspectionToolsApp


def main() -> None:
    app = FlightInspectionToolsApp()
    app.update()
    if tuple(int(value) for value in app.resizable()) != (1, 1):
        raise RuntimeError("主窗口未启用自由缩放")
    expected_labels = ["文件批量编码", "病历自动抽取", "基金金额测算"]
    actual_labels = [app.notebook.tab(tab, "text") for tab in app.notebook.tabs()]
    if actual_labels != expected_labels:
        raise RuntimeError(f"标签页顺序错误：{actual_labels}")
    for index in range(len(app.notebook.tabs())):
        app.notebook.select(index)
        app._load_selected()
        app.update()
    medical = app._loaded["medical_record"]
    medical.mode_var.set("按科室基金支付总金额前十")
    medical._mode_changed()
    if str(medical.count_entry.cget("state")) != "disabled" or str(medical.seed_entry.cget("state")) != "disabled":
        raise RuntimeError("科室前十模式未禁用随机参数")
    medical.mode_var.set("按年份随机抽取")
    medical._mode_changed()
    if str(medical.count_entry.cget("state")) != "normal" or str(medical.seed_entry.cget("state")) != "normal":
        raise RuntimeError("随机模式未启用随机参数")
    loaded = sorted(app._loaded)
    app.destroy()
    expected = ["file_renamer", "fund_calculator", "medical_record"]
    if loaded != expected:
        raise RuntimeError(f"标签页未全部加载：{loaded}")
    print("GUI smoke passed:", ", ".join(loaded))


if __name__ == "__main__":
    main()
