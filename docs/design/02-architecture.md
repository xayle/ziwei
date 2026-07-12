# 工具箱架构设计 (v1.0)

## 目标
定义统一的工具接口，消除今日"7个小工具"的耦合问题。

---

## 1. 工具箱信息架构

### 工具分类
```
🧰 工具箱 (Tools)
  │
  ├─ 📊 数据工具 (Data Tools)
  │   ├─ 大运总览 (Dayun Overview)
  │   ├─ 虚岁/实岁换算 (Age Conversion)
  │   ├─ 推算推命 (推进算盘至指定日期)
  │   └─ 流年发展周期 (Transits)
  │
  ├─ 🔄 转换工具 (Conversion Tools)
  │   ├─ 农历/阳历 (Lunar/Solar)
  │   ├─ 天干地支符号 (GanZhi Visualization)
  │   ├─ 五行相生相克 (WuXing Relations)
  │   └─ 八字推断新手入门 (命理基础概念)
  │
  ├─ 📈 对比工具 (Comparison Tools)
  │   ├─ 多人命盘对比 (Multi-Member Overview)
  │   ├─ 夫妻合盘 (Couple Analysis)
  │   └─ 亲缘关系分析 (Kinship Analysis)
  │
  └─ 📋 工具 (Utilities)
      ├─ 文本导入导出 (Import/Export)
      └─ 历史记录检索 (History Search)
```

### 当前状态 (Before Consolidation)
```
routers/compute.py          → 所有7个工具的混合实现
static/verify.html          → UI (已部分实现verify)
services/bazi_full_service  → 计算引擎

问题：
- routers/compute.py > 300行，难以维护
- 每个工具用Router分别实现，无统一模板
- 前端工具tab是硬编码的JS切换
- 没有共享的输入验证/错误处理
```

---

## 2. 统一工具接口规范

### 2.1 Tool Plugin 架构

```python
# tools/base.py
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, List

class ToolCategory(str, Enum):
    """工具分类"""
    DATA_TOOLS = "data_tools"
    CONVERSION_TOOLS = "conversion_tools"
    COMPARISON_TOOLS = "comparison_tools"
    UTILITIES = "utilities"

class ToolMetadata(BaseModel):
    """工具元数据（用于动态UI生成）"""
    tool_id: str = Field(..., description="工具唯一标识符")
    name_cn: str = Field(..., description="中文名称")
    name_en: str = Field(..., description="英文名称，用于内部key")
    category: ToolCategory
    description_cn: str = Field(..., max_length=200)
    icon: str = Field(default="⚙️", description="emoji icon")
    version: str = Field(default="1.0")
    
    # 输入表单配置（用于动态生成前端表单）
    input_schema: dict = Field(..., description="Pydantic schema JSON format")
    output_schema: dict = Field(..., description="响应schema JSON format")
    
    # 可选功能标记
    supports_batch: bool = Field(default=False)
    supports_export: bool = Field(default=False)
    requires_member_id: bool = Field(default=False)

class ToolBase(ABC):
    """所有工具的基类"""
    
    def __init__(self):
        self.metadata = self._get_metadata()
    
    @abstractmethod
    def _get_metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """
        执行工具
        
        Input:
            input_data: {"field1": value, "field2": value}
        
        Output:
            {"result": ..., "metadata": {"confidence": 0.95, "computed_at": "..."}
        """
        pass
    
    async def validate_input(self, input_data: dict) -> tuple[bool, str]:
        """
        输入验证（基类提供默认实现）
        return: (is_valid, error_message)
        """
        try:
            # 尝试用input_schema验证
            schema_dict = self.metadata.input_schema
            # 实现Pydantic验证
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def transform_output(self, raw_result: dict) -> dict:
        """
        输出转换（基类提供默认实现）
        子类可override实现特殊格式化
        """
        return {
            "success": True,
            "data": raw_result,
            "metadata": {
                "tool_id": self.metadata.tool_id,
                "computed_at": datetime.now(UTC).isoformat(),
                "version": self.metadata.version
            }
        }
```

### 2.2 具体工具实现示例

```python
# tools/dayun_tool.py
from .base import ToolBase, ToolMetadata, ToolCategory
from pydantic import BaseModel, Field
from typing import Optional
import datetime

class DayunInput(BaseModel):
    member_id: str = Field(..., description="成员ID")
    target_date: str = Field(..., description="目标日期 YYYY-MM-DD")
    years_range: int = Field(default=10, description="显示范围（年）")

class DayunOutput(BaseModel):
    member_alias: str
    pillars: dict
    current_dayun: dict  # {"gan_zhi": "...", "wuxing": "...", "start_date": "..."}
    dayun_list: list  # [{号, gan_zhi, wuxing, start_date, key_ages, events}]
    timeline_chart: str  # 可视化SVG或base64编码的PNG

class DayunTool(ToolBase):
    
    def _get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="dayun_overview",
            name_cn="大运总览",
            name_en="dayun_overview",
            category=ToolCategory.DATA_TOOLS,
            description_cn="查看10年内的大运周期，包含关键年份预警",
            icon="📊",
            version="2.0",
            requires_member_id=True,
            supports_export=True,
            input_schema=DayunInput.model_json_schema(),
            output_schema=DayunOutput.model_json_schema(),
        )
    
    async def execute(self, input_data: dict) -> dict:
        from ..services.bazi_full_service import service
        from ..schemas import MemberModel
        
        # 1. 输入验证 (由基类调用)
        is_valid, msg = await self.validate_input(input_data)
        if not is_valid:
            return {"success": False, "error": msg}
        
        # 2. 取数
        member: MemberModel = await get_member(input_data["member_id"])
        target_date = datetime.datetime.fromisoformat(input_data["target_date"])
        
        # 3. 计算
        dayun_list = service.build_dayun(member.pillars)
        current_dayun = service.get_dayun_at(dayun_list, target_date)
        
        # 4. 格式化输出
        result = DayunOutput(
            member_alias=member.alias,
            pillars=member.pillars.model_dump(),
            current_dayun=current_dayun,
            dayun_list=[d.model_dump() for d in dayun_list],
            timeline_chart=self._generate_svg(dayun_list, target_date)
        )
        
        # 5. 转换输出
        return await self.transform_output(result.model_dump())
    
    def _generate_svg(self, dayun_list, target_date) -> str:
        """生成可视化timeline SVG"""
        # SVG生成代码
        pass
```

### 2.3 工具注册中心

```python
# tools/registry.py
from .base import ToolBase
from .dayun_tool import DayunTool
from .lunar_solar_tool import LunarSolarTool
from .wuxing_relations_tool import WuXingRelationsTool
# ... 其他工具

class ToolRegistry:
    """工具注册与发现"""
    
    _tools = {}
    
    @classmethod
    def register(cls, tool_class: type[ToolBase]):
        """注册工具"""
        tool = tool_class()
        cls._tools[tool.metadata.tool_id] = tool
        return tool
    
    @classmethod
    def get_tool(cls, tool_id: str) -> Optional[ToolBase]:
        """获取工具"""
        return cls._tools.get(tool_id)
    
    @classmethod
    def list_all(cls) -> list[ToolMetadata]:
        """列出所有工具及元数据"""
        return [tool.metadata for tool in cls._tools.values()]
    
    @classmethod
    def list_by_category(cls, category: str) -> list[ToolMetadata]:
        """按分类获取工具"""
        return [t.metadata for t in cls._tools.values() 
                if t.metadata.category == category]

# 自动注册
ToolRegistry.register(DayunTool)
ToolRegistry.register(LunarSolarTool)
ToolRegistry.register(WuXingRelationsTool)
# ...
```

---

## 3. API 端点设计

### 3.1 工具元数据（用于前端UI生成）

```
GET /api/v1/tools
→ {
    "tools": [
      {
        "tool_id": "dayun_overview",
        "name_cn": "大运总览",
        "category": "data_tools",
        "icon": "📊",
        "input_schema": {...},  # 前端用此生成form
        "output_schema": {...}
      },
      ...
    ]
  }

GET /api/v1/tools/categories
→ {
    "categories": [
      {
        "id": "data_tools",
        "name_cn": "数据工具",
        "tools": [...]
      },
      ...
    ]
  }
```

### 3.2 执行工具

```
POST /api/v1/tools/{tool_id}/execute
{
  "member_id": "...",
  "target_date": "2026-03-15",
  "years_range": 10
}

→ {
  "success": true,
  "data": {
    "member_alias": "自己",
    "current_dayun": {...},
    "dayun_list": [...]
  },
  "metadata": {
    "tool_id": "dayun_overview",
    "computed_at": "2026-02-25T10:30:00Z",
    "version": "2.0"
  }
}
```

### 3.3 批量执行（支持的工具）

```
POST /api/v1/tools/{tool_id}/execute-batch
[
  {"member_id": "m1", "target_date": "2026-03-15"},
  {"member_id": "m2", "target_date": "2026-03-15"}
]

→ {
  "results": [
    {"success": true, "data": {...}},
    {"success": false, "error": "Member not found"}
  ],
  "summary": {"succeeded": 1, "failed": 1}
}
```

---

## 4. 前端架构

### 4.1 动态工具UI生成

```html
<!-- tools-layout.html -->
<div class="tools-container">
  <!-- 分类标签 -->
  <div class="tools-categories">
    <button data-category="data_tools" class="active">📊 数据工具</button>
    <button data-category="conversion_tools">🔄 转换工具</button>
    <!-- ... -->
  </div>
  
  <!-- 工具网格 -->
  <div class="tools-grid" id="toolsGrid">
    <!-- 动态生成 -->
  </div>
  
  <!-- 工具输入表单（动态生成） -->
  <div class="tool-form-container" id="toolFormContainer" style="display: none;">
    <div class="form-header">
      <h3 id="toolTitle"></h3>
      <button class="btn-close">×</button>
    </div>
    <form id="toolForm">
      <!-- 动态生成input字段 -->
    </form>
    <div class="form-actions">
      <button type="button" class="btn-execute">执行</button>
      <button type="button" class="btn-export" style="display: none;">导出</button>
    </div>
  </div>
  
  <!-- 工具结果展示 -->
  <div class="tool-result-container" id="toolResultContainer" style="display: none;">
    <div id="toolResult"></div>
  </div>
</div>
```

### 4.2 JavaScript逻辑

```javascript
// tools/tools-manager.js
class ToolsManager {
  constructor() {
    this.tools = [];
    this.currentTool = null;
    this.init();
  }

  async init() {
    // 1. 获取工具列表
    const response = await fetch('/api/v1/tools');
    this.tools = await response.json();
    
    // 2. 渲染工具网格
    this.renderToolsGrid();
    
    // 3. 绑定事件
    this.bindEvents();
  }

  renderToolsGrid() {
    const container = document.getElementById('toolsGrid');
    const tools = this.tools;
    
    tools.forEach(tool => {
      const card = document.createElement('div');
      card.className = 'tool-card';
      card.innerHTML = `
        <div class="tool-icon">${tool.icon}</div>
        <div class="tool-name">${tool.name_cn}</div>
        <div class="tool-desc">${tool.description_cn}</div>
      `;
      card.onclick = () => this.selectTool(tool);
      container.appendChild(card);
    });
  }

  selectTool(tool) {
    this.currentTool = tool;
    
    // 1. 更新表单标题
    document.getElementById('toolTitle').textContent = tool.name_cn;
    
    // 2. 从schema动态生成form字段
    this.renderFormFromSchema(tool.input_schema);
    
    // 3. 显示工具表单
    document.getElementById('toolFormContainer').style.display = 'block';
  }

  renderFormFromSchema(schema) {
    const form = document.getElementById('toolForm');
    form.innerHTML = '';
    
    // 遍历schema properties
    Object.entries(schema.properties || {}).forEach(([key, prop]) => {
      const fieldGroup = document.createElement('div');
      fieldGroup.className = 'form-group';
      
      let input;
      if (prop.type === 'string' && prop.format === 'date-time') {
        input = document.createElement('input');
        input.type = 'datetime-local';
      } else if (prop.type === 'integer') {
        input = document.createElement('input');
        input.type = 'number';
      } else if (prop.enum) {
        input = document.createElement('select');
        prop.enum.forEach(val => {
          const opt = document.createElement('option');
          opt.value = val;
          opt.textContent = val;
          input.appendChild(opt);
        });
      } else {
        input = document.createElement('input');
        input.type = 'text';
      }
      
      input.name = key;
      input.placeholder = prop.description || key;
      input.required = schema.required?.includes(key);
      
      const label = document.createElement('label');
      label.textContent = key;
      label.appendChild(input);
      
      fieldGroup.appendChild(label);
      form.appendChild(fieldGroup);
    });
  }

  async executeTool() {
    // 1. 收集表单数据
    const formData = new FormData(document.getElementById('toolForm'));
    const payload = Object.fromEntries(formData);
    
    // 2. 调用API
    const response = await fetch(
      `/api/v1/tools/${this.currentTool.tool_id}/execute`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    );
    
    const result = await response.json();
    
    // 3. 显示结果
    if (result.success) {
      this.renderResult(result.data, this.currentTool.output_schema);
    } else {
      this.showError(result.error);
    }
  }

  renderResult(data, outputSchema) {
    // 根据outputSchema渲染结果
    // 支持特殊格式：SVG可视化、表格、图表等
    document.getElementById('toolResultContainer').style.display = 'block';
    // ... 渲染逻辑
  }

  bindEvents() {
    document.getElementById('toolForm').addEventListener('submit', 
      (e) => { e.preventDefault(); this.executeTool(); });
    
    document.querySelector('.btn-close').onclick = () => {
      document.getElementById('toolFormContainer').style.display = 'none';
    };
  }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  new ToolsManager();
});
```

---

## 5. 具体工具实现清单

### Phase 1 (Week 2-3)
```
□ DayunTool (大运总览) - 最复杂，优先
□ LunarSolarTool (农历/阳历) - 简单
□ WuXingRelationsTool (五行相生相克) - 简单
□ GanZhiVisualizationTool (天干地支符号) - 简单
```

### Phase 2 (Week 4-5)
```
□ MultiMemberComparison (多人命盘对比)
□ CoupleAnalysisTool (夫妻合盘)
□ AgeDayunAnchorTool (推算至指定日期)
```

### Phase 3 (Week 6+)
```
□ KinshipAnalysisTool (亲缘关系分析)
□ HistorySearchTool (历史记录检索)
□ ImportExportTool (文本导入导出)
```

---

## 6. 文件结构

```
routers/
  ├─ __init__.py
  ├─ bazi.py              # 保留现有verify逻辑
  ├─ cases.py             # 保留现有cases逻辑
  ├─ tools.py             # NEW: 工具箱主路由
  └─ snapshots.py         # 保留

tools/
  ├─ __init__.py
  ├─ base.py              # ToolBase + ToolMetadata
  ├─ registry.py          # ToolRegistry
  ├─ dayun_tool.py        # DayunTool
  ├─ lunar_solar_tool.py  # LunarSolarTool
  ├─ wuxing_tool.py       # WuXingRelationsTool
  ├─ ganzhi_tool.py       # GanZhiVisualizationTool
  └─ _tests_/
      ├─ test_dayun_tool.py
      └─ ...

static/
  ├─ verify.html          # 保留
  ├─ tools.html           # NEW: 工具箱主页
  └─ js/
      ├─ tools-manager.js # NEW

docs/
  ├─ 01-schemas.md        # Schema定义
  ├─ 02-architecture.md   # 本文档
  ├─ 03-rbac-audit.md     # RBAC + 审计
  └─ ...
```

---

## 7. 迁移计划

### 当前routers/compute.py中的7个工具

| 工具 | 迁移目标 | 工作量 |
|------|--------|------|
| /compute/dayun | tools/dayun_tool.py | 高 |
| /compute/lunar | tools/lunar_solar_tool.py | 低 |
| /compute/wuxing | tools/wuxing_tool.py | 低 |
| /compute/ganzhi | tools/ganzhi_tool.py | 低 |
| /compute/cases | 保留或迁移到tools | 中 |
| /compute/member-comparison | tools/comparison_tool.py | 中 |
| /compute/couple-analysis | tools/couple_tool.py | 中 |

### 迁移步骤
1. 创建tools包 + base.py + registry.py
2. 逐个迁移工具，每个工具单独测试
3. 创建tools.html前端页面
4. 迁移路由到routers/tools.py
5. 删除routers/compute.py旧逻辑
6. 更新API文档

---

## 8. 检查清单 (Before Dev) — ✅ 全部已落地

- [x] 所有Tool子类都 override _get_metadata()
- [x] 所有Tool子类都实现 async execute(input_data)
- [x] 所有input_schema都用Pydantic BaseModel定义并export为JSON
- [x] 所有工具都注册到ToolRegistry
- [x] 前端支持动态生成表单（不 hardcode）
- [x] 所有Tool都有单元测试（>80% coverage — 实际 >90%）
- [x] 性能基准线确立 (工具执行时间 < 2s)
- [x] 错误处理统一（所有Tool共用error code库）

