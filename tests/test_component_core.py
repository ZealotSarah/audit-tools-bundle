from components.fund_calculator.fund_calculator import insurance_bucket, resolved_visit_type
from components.medical_record.extractor import allocate_quotas, parse_date


def test_medical_record_core_rules_are_available():
    assert allocate_quotas([2024, 2025, 2026], 5) == {2024: 1, 2025: 2, 2026: 2}
    assert parse_date("2024/05/18 09:47:56.000").year == 2024


def test_fund_calculator_core_rules_are_available():
    assert insurance_bucket("310") == 0
    assert insurance_bucket(390.0) == 1
    assert resolved_visit_type("21", "自动识别") == "住院"
    assert resolved_visit_type("11", "自动识别") == "门诊"

