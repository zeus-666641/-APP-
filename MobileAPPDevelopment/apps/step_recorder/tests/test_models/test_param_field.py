"""ParamField / FieldType 数据完整性测试（Q17-Q19 决策）"""
import pytest

from models.step import (
    STEP_TYPE_REGISTRY,
    FieldType,
    ParamField,
    StepStatus,
    StepType,
    get_step_type_meta,
)


class TestFieldType:
    """FieldType 枚举覆盖 Q19 决策的所有控件类型"""

    def test_all_expected_types_present(self):
        expected = {
            "bool", "int", "int_range", "string", "textarea", "enum", "coordinate",
        }
        actual = {ft.value for ft in FieldType}
        assert actual == expected

    def test_count(self):
        assert len(FieldType) == 7


class TestParamField:
    """ParamField 数据类"""

    def test_required_fields(self):
        f = ParamField(key="x", label_zh="X", field_type=FieldType.STRING)
        assert f.key == "x"
        assert f.label_zh == "X"
        assert f.field_type == FieldType.STRING

    def test_defaults(self):
        f = ParamField(key="x", label_zh="X", field_type=FieldType.STRING)
        assert f.required is False
        assert f.default is None
        assert f.options == ()
        assert f.min_value is None
        assert f.max_value is None
        assert f.step == 1
        assert f.placeholder == ""
        assert f.help_text == ""

    def test_is_frozen(self):
        """frozen dataclass 不可变"""
        f = ParamField(key="x", label_zh="X", field_type=FieldType.STRING)
        with pytest.raises(Exception):
            f.key = "y"  # type: ignore[misc]


class TestRegistryFieldsIntegrity:
    """STEP_TYPE_REGISTRY 的 fields 字段完整性（Q18 决策落地）"""

    def test_all_step_types_have_fields_attribute(self):
        """每个 StepTypeMeta 都有 fields 属性"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            assert hasattr(meta, "fields"), f"{step_type} 缺 fields 属性"
            assert isinstance(meta.fields, tuple), f"{step_type} fields 不是 tuple"

    def test_enum_field_has_options(self):
        """ENUM 类型字段必须有非空 options"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            for f in meta.fields:
                if f.field_type == FieldType.ENUM:
                    assert f.options, (
                        f"{step_type}.{f.key} 是 ENUM 但 options 为空"
                    )
                    assert len(f.options) >= 2, (
                        f"{step_type}.{f.key} ENUM options 至少 2 项"
                    )

    def test_int_range_field_has_bounds(self):
        """INT_RANGE 类型字段必须有 min_value 和 max_value"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            for f in meta.fields:
                if f.field_type == FieldType.INT_RANGE:
                    assert f.min_value is not None, (
                        f"{step_type}.{f.key} INT_RANGE 缺 min_value"
                    )
                    assert f.max_value is not None, (
                        f"{step_type}.{f.key} INT_RANGE 缺 max_value"
                    )
                    assert f.min_value < f.max_value, (
                        f"{step_type}.{f.key} min_value >= max_value"
                    )

    def test_field_keys_unique_per_type(self):
        """每个 StepType 的 fields 中 key 不重复"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            keys = [f.key for f in meta.fields]
            assert len(keys) == len(set(keys)), (
                f"{step_type} 字段 key 重复: {keys}"
            )

    def test_option_pairs_are_str_str(self):
        """ENUM options 每项是 (value, label_zh) 二元组"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            for f in meta.fields:
                if f.field_type != FieldType.ENUM:
                    continue
                for opt in f.options:
                    assert isinstance(opt, tuple), f"{step_type}.{f.key} option 非 tuple"
                    assert len(opt) == 2, f"{step_type}.{f.key} option 非二元组"
                    assert isinstance(opt[0], str), f"{step_type}.{f.key} option.value 非 str"
                    assert isinstance(opt[1], str), f"{step_type}.{f.key} option.label 非 str"

    def test_enum_field_default_in_options(self):
        """ENUM 字段 default 必须在 options 的 value 中"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            for f in meta.fields:
                if f.field_type != FieldType.ENUM:
                    continue
                if f.default is None:
                    continue
                values = [opt[0] for opt in f.options]
                assert f.default in values, (
                    f"{step_type}.{f.key} default '{f.default}' 不在 options {values} 中"
                )


class TestQ18NotImplementedHasFields:
    """Q18 决策：NOT_IMPLEMENTED 类型也填充 fields"""

    def test_not_implemented_types_have_fields_or_none(self):
        """NOT_IMPLEMENTED 类型要么无 fields（动作类），要么 fields 非空"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            if meta.status != StepStatus.NOT_IMPLEMENTED:
                continue
            # 允许 fields=()（如 LOCK_SCREEN），但不能未指定
            assert meta.fields is not None, f"{step_type} NOT_IMPLEMENTED 但 fields 是 None"

    def test_not_implemented_can_save_placeholder_params(self):
        """具体验证：NOT_IMPLEMENTED 类型也允许填参数"""
        # BLUETOOTH 有 state 字段
        bt_meta = get_step_type_meta(StepType.BLUETOOTH)
        assert len(bt_meta.fields) >= 1
        assert bt_meta.fields[0].key == "state"

        # POWER 有 action 字段
        power_meta = get_step_type_meta(StepType.POWER)
        assert len(power_meta.fields) >= 1
        assert power_meta.fields[0].key == "action"


class TestQ19FieldTypeDistribution:
    """Q19 决策：FieldType 类型覆盖"""

    def test_at_least_one_field_of_each_type_exists(self):
        """整个 registry 至少覆盖每种 FieldType 一次（除 COORDINATE 暂未用）"""
        used_types: set[FieldType] = set()
        for meta in STEP_TYPE_REGISTRY.values():
            for f in meta.fields:
                used_types.add(f.field_type)
        # 至少覆盖 BOOL/INT/INT_RANGE/STRING/TEXTAREA/ENUM
        # COORDINATE 暂未启用，单独豁免
        for ft in [FieldType.BOOL, FieldType.INT, FieldType.INT_RANGE,
                   FieldType.STRING, FieldType.TEXTAREA, FieldType.ENUM]:
            assert ft in used_types, f"FieldType.{ft.name} 未被任何字段使用"


class TestFieldsBackwardCompatible:
    """Q17 决策：fields 与旧 params_schema 并存"""

    def test_both_fields_present(self):
        """StepTypeMeta 同时有 fields 和 params_schema"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            assert hasattr(meta, "fields")
            assert hasattr(meta, "params_schema")

    def test_params_schema_still_dict(self):
        """旧字段保持 dict 类型"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            assert isinstance(meta.params_schema, dict)
