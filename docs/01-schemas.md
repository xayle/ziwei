# 数据模型 Schema 定义 (v1.0)

## 目标
为前端表单校验、后端存储、API文档提供**唯一真实来源**。

---

## 1. Member 模型

### 核心结构
```json
{
  "member_id": "uuid",
  "owner_id": "uuid",
  "alias": "string (1-30 chars)",
  "full_name": "string (optional, sensitive)",
  "birth_info": {
    "date": "YYYY-MM-DD",
    "time_of_birth": "HH:MM (或 null 若不确定)",
    "is_time_uncertain": "boolean",
    "location_lon": "number (70-140)",
    "location_name": "string (optional)"
  },
  "relationship": "enum: SELF | SPOUSE | CHILD | PARENT | SIBLING | EXTENDED | OTHER",
  "au
thorization": {
    "status": "enum: PENDING | APPROVED | REVOKED",
    "requested_at": "ISO8601",
    "approved_at": "ISO8601 (optional)",
    "approved_by": "uuid (optional)",
    "permission_scope": "enum: FULL | PROFILE_ONLY | ANCESTOR_ONLY"
  },
  "computed_data": {
    "pillars": "Pillars (4柱)",
    "dayun": "DayunModel (大运)",
    "current_dayun_summary": "string (一句话语)",
    "confidence_score": "number 0-100",
    "confidence_factors": [
      {
        "factor": "enum: birth_precision | evidence_count | historical_accuracy",
        "weight": "number 0-1",
        "value": "number 0-100"
      }
    ]
  },
  "audit": {
    "created_at": "ISO8601",
    "created_by": "uuid",
    "updated_at": "ISO8601",
    "updated_by": "uuid",
    "is_archived": "boolean"
  }
}
```

### 校验规则
```yaml
alias:
  - 必填，1-30个字符
  - 同一owner下唯一
  - 允许中文/英文

birth_info.date:
  - 必填，YYYY-MM-DD格式
  - 不能晚于today

birth_info.time_of_birth:
  - 格式: HH:MM (24小时制)
  - 若is_time_uncertain=true，可为null

birth_info.location_lon:
  - 必填，范围 70-140
  - 用于真太阳时校正

authorization.status:
  - 新member: 若是SELF则自动APPROVED
  - 家族成员: 默认PENDING，需owner审批

relationship:
  - 必填
  - SELF: 只能有1个
```

---

## 2. Event 模型

### 核心结构
```json
{
  "event_id": "uuid",
  "owner_id": "uuid",
  "trigger_member_id": "uuid (FK -> Member)",
  "event_type": "enum: 买房 | 投资 | 贷款担保 | 合伙 | 搬迁 | 赠与 | 离婚 | 健康重大事件 | 其他",
  "event_subtype": "string (optional, 自定义细分)",
  "title": "string (max 200)",
  "description": "string (max 2000, optional)",
  "datetime_info": {
    "occurred_at": "ISO8601 (if status=OCCURRED)",
    "planned_at": "ISO8601 (if status=PLANNED)",
    "precision": "enum: EXACT | ESTIMATED_MONTH | ESTIMATED_YEAR | RANGE",
    "date_range_start": "ISO8601 (if precision=RANGE)",
    "date_range_end": "ISO8601 (if precision=RANGE)"
  },
  "scale": "enum: 小 | 中 | 大",
  "scale_context": {
    "small_usd": "number (default: 0-10000)",
    "medium_usd": "number (default: 10000-100000)",
    "large_usd": "number (default: 100000+)"
  },
  "status": "enum: 拟办 | 已发生 | 已取消 | 搁置",
  "evidence": {
    "attachments": [
      {
        "file_id": "uuid",
        "file_name": "string",
        "file_hash": "sha256 (for integrity check)",
        "storage_location": "local | s3 | encrypted_local",
        "uploaded_at": "ISO8601",
        "is_sensitive": "boolean"
      }
    ],
    "summary": "string (max 500, 用户手工描述)"
  },
  "computed_impact": {
    "love_score": "number 0-100",
    "wealth_score": "number 0-100",
    "family_score": "number 0-100",
    "computed_at": "ISO8601",
    "model_confidence": "number 0-1 (模型的置信度 != 用户数据置信度)",
    "impact_timeline_months": "number"
  },
  "system_recommendation": {
    "summary": "string (一句话结论)",
    "reasoning": [
      {
        "reason": "string",
        "rule_id": "string (用于溯源)",
        "rule_version": "string (日期或版本号)",
        "rule_reference": "string (文献出处)",
        "reason_confidence": "number 0-1"
      }
    ],
    "mitigations": [
      {
        "action": "string",
        "priority": "enum: HIGH | MEDIUM | LOW",
        "category": "enum: 时机选择 | 人事调配 | 财务安排 | 其他"
      }
    ],
    "risk_level": "enum: LOW | MEDIUM | HIGH | CRITICAL"
  },
  "user_feedback": {
    "actions_taken": ["string"] (用户已采纳的建议),
    "actions_ignored": ["string"],
    "outcome_notes": "string (用户记录的实际结果)"
  },
  "audit": {
    "created_at": "ISO8601",
    "created_by": "uuid",
    "status_changed_at": "ISO8601 (上次status变更时间)",
    "status_changed_by": "uuid",
    "impact_recomputed_at": "ISO8601 (上次重算时间)",
    "evidence_updated_at": "ISO8601"
  }
}
```

### 校验规则
```yaml
title:
  - 必填
  - max 200字符
  - 不允许纯数字

event_type:
  - 必填
  - 固定的8个类型 + "其他"

datetime_info:
  - status=OCCURRED 时：occurred_at 必填
  - status=PLANNED 时：planned_at 必填
  - precision=RANGE 时：date_range_start 和 date_range_end 都必填

scale:
  - 必填
  - 需要与 scale_context 对应

status:
  - 状态转移规则：
    - 拟办 -> (已发生 | 已取消 | 搁置)
    - 搁置 -> (拟办 | 已取消)
    - 已发生 -> 不可改
    - 已取消 -> 不可改

evidence.is_sensitive:
  - 若为true，导出时自动脱敏文件名
  - 脱敏规则: 保留扩展名，内容hash
```

---

## 3. Scenario 模型

### 核心结构
```json
{
  "scenario_id": "uuid",
  "owner_id": "uuid",
  "name": "string (max 100, 用户自定义场景名)",
  "base_event": {
    "event_type": "string (来自Event.event_type)",
    "trigger_member_id": "uuid (FK)",
    "scale": "enum: 小 | 中 | 大",
    "planned_at": "ISO8601",
    "precision": "enum: EXACT | ESTIMATED_MONTH | ESTIMATED_YEAR"
  },
  "variant_on": {
    "base_event_id": "uuid (optional, 若是某个历史Event的变体)",
    "what_if_changes": {
      "scale": "enum (若改变规模)",
      "timing_shift_months": "number (若推迟/提前)",
      "additional_context": "string"
    }
  },
  "analysis_result": {
    "summary": "string (一句话结论)",
    "impact_breakdown": {
      "love": {
        "score": "number 0-100",
        "explanation": "string"
      },
      "wealth": {
        "score": "number 0-100",
        "explanation": "string"
      },
      "family": {
        "score": "number 0-100",
        "explanation": "string"
      }
    },
    "timeline": {
      "trigger_date": "ISO8601",
      "impact_window_start_months": "number",
      "impact_window_end_months": "number",
      "peak_impact_month": "number"
    },
    "similar_historical_cases": [
      {
        "case_description": "string (template or real case)",
        "actual_year": "number",
        "outcome": "string"
      }
    ],
    "model_metadata": {
      "model_version": "string (e.g., v1_2026)",
      "model_confidence": "number 0-1",
      "computed_at": "ISO8601",
      "computed_duration_ms": "number"
    },
    "rule_chain": [
      {
        "step": "number",
        "rule_id": "string",
        "rule_text": "string (readable Chinese)",
        "rule_reference": "string (文献出处)",
        "intermediate_result": "string"
      }
    ]
  },
  "risk_assessment": {
    "risk_level": "enum: LOW | MEDIUM | HIGH | CRITICAL",
    "if_high_risk": {
      "warning_message": "string (用户见到的高风险警告)",
      "requires_approval": "boolean (是否需强制确认)",
      "approval_required_reason": "string"
    }
  },
  "user_actions": {
    "saved_at": "ISO8601 (optional)",
    "marked_as_occurred_at": "ISO8601 (optional)",
    "evidence_uploaded_at": "ISO8601 (optional)",
    "report_exported_at": "ISO8601 (optional)"
  },
  "audit": {
    "created_at": "ISO8601",
    "created_by": "uuid",
    "updated_at": "ISO8601"
  }
}
```

### 校验规则
```yaml
name:
  - 必填
  - max 100字符
  - 可为中文

base_event:
  - 必填
  - event_type 必须在预定义列表中

base_event.trigger_member_id:
  - 必填，FK -> Member
  - 必须是owner有权限访问的member

variant_on.base_event_id:
  - 可选
  - 若填写，则为某个历史Event的"假如场景"

analysis_result:
  - 生成后为只读
  - 用户不能编辑impact scores，只能编辑user_feedback

risk_assessment.if_high_risk.requires_approval:
  - 若为true，前端必须显示高风险确认弹窗
  - 用户必须手动confirm才能continue
```

---

## 4. 置信度模型 (ConfidenceModel)

### 核心结构
```json
{
  "confidence_score": "number 0-100 (整体)",
  "breakdown": {
    "birth_precision": {
      "value": "number 0-100",
      "weight": "0.4",
      "factors": [
        {
          "name": "time_certainty",
          "value": "number",
          "description": "时辰确定性"
        },
        {
          "name": "date_certainty",
          "value": "number",
          "description": "出生日期是否官方记录"
        }
      ]
    },
    "evidence_quantity": {
      "value": "number 0-100",
      "weight": "0.3",
      "evidence_items_count": "number",
      "calculation": "min(evidence_items_count * 10, 100)"
    },
    "historical_accuracy": {
      "value": "number 0-100",
      "weight": "0.3",
      "factors": [
        {
          "name": "event_outcome_match",
          "value": "number",
          "description": "历史事件预测准确率"
        }
      ]
    }
  },
  "how_to_improve": [
    {
      "action": "补充出生时辰",
      "potential_gain": "number (若完成可增加多少)"
    },
    {
      "action": "上传事件证据",
      "potential_gain": "number"
    }
  ]
}
```

---

## 5. 跨模型关系

### ER 图
```
┌──────────────┐
│   Member     │
├──────────────┤
│ member_id(PK)├──┐
│ owner_id(FK) │  │
│ relationship │  │
│              │  │
└──────────────┘  │
       │          │
       │ (1:N)    │
       ▼          │
┌──────────────┐  │
│   Event      │  │
├──────────────┤  │
│ event_id(PK) │  │
│ trigger_member_id ┤──┘
│ owner_id(FK) │
│              │
└──────────────┘
       │
       │ (1:N)
       ▼
┌──────────────┐
│  Scenario    │
├──────────────┤
│scenario_id(PK)
│base_event.trigger_member_id
│base_event_id(optional FK)
│owner_id(FK) │
│              │
└──────────────┘
```

### 外键约束
```yaml
Event.trigger_member_id:
  - FK -> Member.member_id
  - 且 Member.owner_id == Event.owner_id
  - 删除Member时：Event.status必须在(已发生|已取消)中，否则soft delete

Event.owner_id:
  - FK -> User.user_id

Scenario.base_event_id:
  - FK -> Event.event_id (optional)
  - 若为null，则为模拟场景

Member.owner_id:
  - FK -> User.user_id
```

---

## 6. 版本控制与变更

### 何时更新Schema

- 新增字段：PATCH版本
- 删除字段：major版本
- 改变类型：major版本
- 枚举扩展：MINOR版本
- 文档调整：无版本变更

### 变更日志格式

```
# v1.1.0 (2026-02-26)
- [MINOR] 新增 Member.birth_info.location_name 字段 (可选)
- [PATCH] Event.event_subtype 从 optional 变为 optional (文案调整)

# v1.0.0 (2026-02-25)
- 初始发布
```

---

## 7. API 序列化示例

### 请求体示例
```json
POST /api/v1/scenarios
{
  "owner_id": "user-123",
  "name": "假如提前2个月投资房产",
  "base_event": {
    "event_type": "投资",
    "trigger_member_id": "member-456",
    "scale": "大",
    "planned_at": "2026-05-01",
    "precision": "ESTIMATED_MONTH"
  },
  "variant_on": {
    "base_event_id": "event-789",
    "what_if_changes": {
      "timing_shift_months": -2
    }
  }
}
```

### 响应体示例
```json
{
  "scenario_id": "scenario-001",
  "name": "假如提前2个月投资房产",
  "analysis_result": {
    "summary": "提前投资可降低5年内的流年冲击，但需防范2026年9月节气变化",
    "impact_breakdown": {
      "love": {"score": 60, "explanation": "..."},
      "wealth": {"score": 78, "explanation": "..."},
      "family": {"score": 72, "explanation": "..."}
    },
    "model_confidence": 0.82
  },
  "risk_assessment": {
    "risk_level": "MEDIUM"
  }
}
```

---

## 检查清单 (Before Dev)

- [ ] 所有FK都要在代码中添加唯一索引
- [ ] 所有枚举值在constant.py中定义，前后端共享
- [ ] 所有timestamp字段用ISO8601 + UTC存储
- [ ] sensitive 字段在backup/export时自动脱敏
- [ ] 所有validation在 Pydantic schema 中定义
- [ ] 所有changelog在此doc中更新

