from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    label: str
    factory: str
    risk: str

    def load_factory(self):
        module_name, attribute = self.factory.split(":", 1)
        return getattr(import_module(module_name), attribute)


COMPONENTS = (
    ComponentSpec(
        "file_renamer", "文件批量编码", "audit_tools_bundle.tabs.file_renamer:FileRenamerTab",
        "原地修改文件名，执行前检查预览",
    ),
    ComponentSpec(
        "medical_record", "病历自动抽取", "audit_tools_bundle.tabs.medical_record:MedicalRecordTab",
        "只读源 Excel，结果写入新文件",
    ),
    ComponentSpec(
        "fund_calculator", "基金金额测算", "audit_tools_bundle.tabs.fund_calculator:FundCalculatorTab",
        "修改工作簿并保留测算前备份",
    ),
)
