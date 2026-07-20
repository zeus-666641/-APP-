"""StepType 枚举与元数据表测试"""
from models.step import (
    STEP_TYPE_REGISTRY,
    StepCategory,
    StepStatus,
    StepType,
    count_by_category,
    count_by_status,
    get_step_type_meta,
    get_steps_by_category,
    get_steps_by_status,
)


class TestStepType:
    """StepType 枚举基本测试"""

    def test_total_count(self):
        """PRD 第 5 章应有 30+ 类型"""
        assert len(StepType) >= 30, f"步骤类型数量不足: {len(StepType)}"

    def test_all_registered(self):
        """每个枚举值都必须在注册表中有元数据"""
        for step_type in StepType:
            assert step_type in STEP_TYPE_REGISTRY, f"{step_type} 未注册元数据"

    def test_type_id_matches_enum_value(self):
        """type_id 必须与枚举值一致"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            assert meta.type_id == step_type.value

    def test_each_category_has_items(self):
        """5 大分类每个都至少有 4 项"""
        counts = count_by_category()
        for category, count in counts.items():
            assert count >= 4, f"分类 {category} 数量过少: {count}"

    def test_each_status_has_items(self):
        """3 种状态都有项目"""
        counts = count_by_status()
        assert counts[StepStatus.AVAILABLE] >= 5
        assert counts[StepStatus.LIMITED] >= 4
        assert counts[StepStatus.NOT_IMPLEMENTED] >= 14  # 系统控制 14 + 其他


class TestStepTypeMeta:
    """元数据完整性测试"""

    def test_meta_fields_not_empty(self):
        """必填字段非空"""
        for step_type, meta in STEP_TYPE_REGISTRY.items():
            assert meta.name_zh, f"{step_type} name_zh 为空"
            assert meta.icon, f"{step_type} icon 为空"
            assert meta.description, f"{step_type} description 为空"
            assert isinstance(meta.params_schema, dict)

    def test_status_consistent_with_design(self):
        """关键类型状态符合设计"""
        # 完全可用
        assert get_step_type_meta(StepType.OPEN_URL).status == StepStatus.AVAILABLE
        assert get_step_type_meta(StepType.DARK_MODE).status == StepStatus.AVAILABLE
        assert get_step_type_meta(StepType.ALERT).status == StepStatus.AVAILABLE
        assert get_step_type_meta(StepType.DELAY).status == StepStatus.AVAILABLE
        assert get_step_type_meta(StepType.RUN_SUBTASK).status == StepStatus.AVAILABLE

        # 受限
        assert get_step_type_meta(StepType.CLICK).status == StepStatus.LIMITED
        assert get_step_type_meta(StepType.DIAL).status == StepStatus.LIMITED
        assert get_step_type_meta(StepType.NOTIFY).status == StepStatus.LIMITED

        # 未实现
        assert get_step_type_meta(StepType.OPEN_APP).status == StepStatus.NOT_IMPLEMENTED
        assert get_step_type_meta(StepType.BLUETOOTH).status == StepStatus.NOT_IMPLEMENTED
        assert get_step_type_meta(StepType.FLASHLIGHT).status == StepStatus.NOT_IMPLEMENTED


class TestCategoryQueries:
    """分类查询测试"""

    def test_get_steps_by_category(self):
        sim_steps = get_steps_by_category(StepCategory.SIMULATION)
        assert len(sim_steps) == 8  # PRD 5.1 共 8 项

        system_steps = get_steps_by_category(StepCategory.SYSTEM_CONTROL)
        assert len(system_steps) == 14  # PRD 5.2 共 14 项

    def test_get_steps_by_status(self):
        not_impl = get_steps_by_status(StepStatus.NOT_IMPLEMENTED)
        # 系统控制 14 + 模拟2 + 显示6 + 音频3 + OCR + 手电筒 = 26+
        assert len(not_impl) >= 22


class TestCategoryName:
    """分类映射 PRD 5.1-5.5"""

    def test_category_count(self):
        """应有 5 个分类"""
        assert len(StepCategory) == 5

    def test_category_values(self):
        assert StepCategory.SIMULATION.value == "simulation"
        assert StepCategory.SYSTEM_CONTROL.value == "system_control"
        assert StepCategory.DISPLAY.value == "display"
        assert StepCategory.AUDIO_HAPTIC.value == "audio_haptic"
        assert StepCategory.AUXILIARY.value == "auxiliary"
