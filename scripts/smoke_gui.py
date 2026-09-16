import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit_tools_bundle import BUNDLE_VERSION
from audit_tools_bundle.app import FlightInspectionToolsApp, get_work_area


def main() -> None:
    app = FlightInspectionToolsApp()
    app.update()
    if app.title() != f"飞检工具包 V{BUNDLE_VERSION}":
        raise RuntimeError(f"窗口版本标题错误：{app.title()}")
    left, top, right, bottom = get_work_area(app)
    if app.winfo_width() > right - left or app.winfo_height() > bottom - top:
        raise RuntimeError("主窗口超出 Windows 可用工作区")
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
    app.geometry("960x560")
    app.update()
    for component_id, frame in app._loaded.items():
        app.notebook.select(frame)
        app.update()
        scroller = getattr(frame, "scroller", None)
        if scroller is None or not scroller.winfo_ismapped():
            raise RuntimeError(f"{component_id} 未启用小屏幕滚动容器")
        if not scroller.canvas.cget("scrollregion"):
            raise RuntimeError(f"{component_id} 未生成滚动区域")
        scroller.canvas.yview_moveto(1.0)
        scroller.canvas.yview_moveto(0.0)
    renamer_scroller = app._loaded["file_renamer"].scroller
    if renamer_scroller.horizontal_scrollbar is None:
        raise RuntimeError("文件批量编码页未启用横向滚动")
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
