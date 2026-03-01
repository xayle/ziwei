# 数据模型优化建议 (v1.0)

## 📊 字段审计 & 精简方案

根据当前schemas.md的设计，这里提出几个**可以精简或调整**的字段。

---

## 1️⃣ Member 模型优化

### 现有设计的冗余之处

```json
{
  "member_id": "uuid",
  "owner_id": "uuid",
  "alias": "string",
  "full_name": "string (optional, sensitive)",
  "birth_info": {
    "date": "YYYY-MM-DD",
    "time_of_birth": "HH:MM (或 null)",
    "is_time_uncertain": "boolean",  // ❌ 冗余
    "location_lon": "number",
    "location_name": "string (optional)"  // ❌ 冗余
  },
  "...computed_data": {
    "pillars": "Pillars",
    "dayun": "DayunModel",
    "current_dayun_summary": "string",  // ❌ 可由dayun[0]推导
    "confidence_score": "number 0-100",
    "confidence_factors": [...]  // ❌ 计算字段，不需持久化
  }
}
```

### 优化方案A: 精简字段

**移除**:
- ❌ `birth_info.is_time_uncertain` → 改用 `time_of_birth == null` 判断  
- ❌ `birth_info.location_name` → 保留 `location_lon`，前端用坐标反查地名
- ❌ `computed_data.current_dayun_summary` → 实时从dayun[0]生成
- ❌ `computed_data.confidence_factors` → 改为cached_at时间戳 + 函数重新计算

**修改后**:
```json
{
  "member_id": "uuid",
  "owner_id": "uuid",
  "alias": "string (1-30)",
  "full_name": "string (optional, sensitive)",
  "birth_info": {
    "date": "YYYY-MM-DD",
    "time_of_birth": "HH:MM (或 null 表示不确定)",
    "location_lon": "number (70-140)",
    "location_lat": "number (18-54)",  // 新增纬度，用于更精准的地理计算
    "location_tz_offset": "number (-12 to 12)",  // 新增时区，用于真太阳时转换
    "is_lunar": "boolean (default: false)"  // 新增：出生日期是否为农历
  },
  "relationship": "enum: SELF | SPOUSE | CHILD | PARENT | SIBLING | EXTENDED | OTHER",
  "authorization": {
    "status": "enum: PENDING | APPROVED | REVOKED",
    "requested_at": "ISO8601",
    "approved_at": "ISO8601 (optional)",
    "approved_by": "uuid (optional)",
    "permission_scope": "enum: FULL | PROFILE_ONLY | ANCESTOR_ONLY"
  },
  "computed_data": {
    "pillars": "Pillars (4柱)",
    "dayun": "DayunModel (大运)",
    "computed_at": "ISO8601 (缓存时间戳)",
    "cached_confidence_score": "number 0-100 (缓存的置信度)",
    "cache_ttl_hours": "number (12小时后重新计算)"
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

**优点**:
- DB存储减少 ~30% (从20字段 → 14字段)
- 不再有"同一数据两处存储"问题
- computed_at + cache_ttl实现"缓存失效"机制

**缺点**:
- 前端需要"反推"时间不确定的UI(need to check `time_of_birth == null`)

### 决策: **推荐采纳**

---

## 2️⃣ Event 模型优化

### 现有设计的问题

```json
{
  "event_id": "uuid",
  "owner_id": "uuid",
  "trigger_member_id": "uuid",
  "event_type": "enum: 8个types",
  "event_subtype": "string (optional)",  // ❌ 模糊不清
  "title": "string",
  "description": "string (max 2000)",  // ❌ 太冗长
  "datetime_info": {
    "occurred_at": "ISO8601 (if OCCURRED)",
    "planned_at": "ISO8601 (if PLANNED)",
    "precision": "enum: EXACT | ESTIMATED_MONTH | ESTIMATED_YEAR | RANGE",
    "date_range_start": "ISO8601 (if RANGE)",
    "date_range_end": "ISO8601 (if RANGE)"
  },
  "scale": "enum: 小 | 中 | 大",
  "scale_context": {  // ❌ 冗余：定义规则后就固定了
    "small_usd": "number",
    "medium_usd": "number",
    "large_usd": "number"
  },
  "status": "enum: 拟办 | 已发生 | 已取消 | 搁置",
  "evidence": {
    "attachments": [  // ❌ 文件管理应该独立为"File"表
      {
        "file_id": "uuid",
        "file_name": "string",
        "file_hash": "sha256",
        "storage_location": "local | s3 | encrypted_local",
        "uploaded_at": "ISO8601",
        "is_sensitive": "boolean"
      }
    ],
    "summary": "string (max 500)"  // ❌ 和description重复
  },
  "computed_impact": {
    "love_score": "number 0-100",
    "wealth_score": "number 0-100",
    "family_score": "number 0-100",
    "computed_at": "ISO8601",
    "model_confidence": "number",
    "impact_timeline_months": "number"  // ❌ 模糊：持续多久?
  },
  "system_recommendation": {
    "summary": "string",
    "reasoning": [...]  // ❌ 列表很长，逐条保存冗余
  },
  "user_feedback": {
    "actions_taken": ["string"],  // ❌ 可改为FK关系(ActionTaken表)
    "actions_ignored": ["string"],
    "outcome_notes": "string"
  },
  "audit": {
    "created_at": "ISO8601",
    "...status_changed_at": "ISO8601",  // ❌ 应该用audit log记录，这里不需要
    "status_changed_by": "uuid"
  }
}
```

### 优化方案B: 拆表 + 反范式化

**问题分析**:
1. `event` 表字段过多 (25+)
2. `evidence.attachments` 应独立为表
3. `system_recommendation.reasoning` 列表应独立为表
4. `user_feedback.actions_taken/ignored` 可改为明细表

**优化后结构**:
```sql
-- 主表 (核心Event信息)
CREATE TABLE events (
  event_id UUID PRIMARY KEY,
  owner_id UUID,  -- FK
  trigger_member_id UUID,  -- FK
  event_type ENUM,
  title VARCHAR(200),
  status ENUM: PLANNED | OCCURRED | CANCELLED | PAUSED,
  planned_at TIMESTAMP NULL,
  occurred_at TIMESTAMP NULL,
  scale ENUM: SMALL | MEDIUM | LARGE,
  created_at TIMESTAMP,
  created_by UUID,
  updated_at TIMESTAMP,
  updated_by UUID,
  INDEX (owner_id, status, created_at)
);

-- 详情表 (分离低查询频率的字段)
CREATE TABLE event_details (
  event_id UUID PRIMARY KEY,  -- FK events.event_id
  description TEXT,
  precision ENUM,
  date_range_start TIMESTAMP NULL,
  date_range_end TIMESTAMP NULL
);

-- 计算结果表 (Impact scores)
CREATE TABLE event_impact_scores (
  event_id UUID PRIMARY KEY,
  impact_love SMALLINT (0-100),
  impact_wealth SMALLINT,
  impact_family SMALLINT,
  model_confidence FLOAT,
  impact_timeline_months SMALLINT,
  computed_at TIMESTAMP,
  INDEX (event_id, computed_at)
);

-- 推荐理由表 (每条reasoning单独存储)
CREATE TABLE event_recommendations (
  recommendation_id UUID PRIMARY KEY,
  event_id UUID,  -- FK
  reasoning_order INT,
  reason TEXT,
  rule_id VARCHAR(100),
  rule_version VARCHAR(20),
  rule_reference TEXT,
  reason_confidence FLOAT,
  created_at TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
  INDEX (event_id, reasoning_order)
);

-- 缓解措施表
CREATE TABLE event_mitigations (
  mitigation_id UUID PRIMARY KEY,
  event_id UUID,  -- FK
  action TEXT,
  priority ENUM: HIGH | MEDIUM | LOW,
  category VARCHAR(50),
  created_at TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);

-- 证据文件表 (独立管理)
CREATE TABLE event_attachments (
  attachment_id UUID PRIMARY KEY,
  event_id UUID,  -- FK
  file_name VARCHAR(255),
  file_size BIGINT,
  file_hash VARCHAR(64) UNIQUE,  -- SHA256
  storage_location ENUM: LOCAL | S3 | ENCRYPTED_LOCAL,
  uploaded_at TIMESTAMP,
  uploaded_by UUID,
  is_sensitive BOOLEAN,
  FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
  INDEX (event_id, uploaded_at)
);

-- 用户反馈表 (用户采纳了哪些建议)
CREATE TABLE user_feedback_actions (
  feedback_id UUID PRIMARY KEY,
  event_id UUID,  -- FK
  mitigation_id UUID,  -- 对应的mitigation
  action_taken ENUM: ADOPTED | IGNORED | MODIFIED,
  outcome_notes TEXT,
  created_at TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (mitigation_id) REFERENCES event_mitigations(mitigation_id)
);
```

**Pydantic模型调整**:
```python
class EventResponse(BaseModel):
    """简化后的Event响应"""
    event_id: str
    owner_id: str
    trigger_member_id: str
    event_type: str
    title: str
    status: str
    planned_at: Optional[datetime]
    occurred_at: Optional[datetime]
    scale: str
    created_at: datetime
    
    # 按需加载关联数据
    details: Optional[EventDetails] = None  # 可选
    impact_scores: Optional[ImpactScores] = None  # 可选
    recommendations: Optional[List[Recommendation]] = None  # 可选
    attachments: Optional[List[Attachment]] = None  # 可选
    user_feedback: Optional[UserFeedback] = None  # 可选

class EventDetailRequest(BaseModel):
    """查询事件详情时的请求"""
    event_id: str
    include_recommendation: bool = True
    include_feedback: bool = True
    include_attachments: bool = True
```

**查询API示例**:
```python
@router.get("/api/v1/events/{event_id}")
async def get_event(event_id: str, include: str = "details,recommendations"):
    """
    查询event
    
    Query ?include=details,recommendations,attachments
    支持按需加载确实需要的关联数据
    """
    event = await events_repo.get(event_id)
    
    # 只加载指定的关联数据
    if "recommendations" in include:
        event.recommendations = await recommendations_repo.find_by_event_id(event_id)
    
    if "attachments" in include:
        event.attachments = await attachments_repo.find_by_event_id(event_id)
    
    return event
```

**优点**:
- 主表只需3ms查询 (字段少，索引高效)
- 按需加载推荐理由 (不需要每次都返回50条)
- 易扩展 (后续新增字段只需新表)
- DB存储优化 (推荐理由不再嵌入主行)

**缺点**:
- 代码复杂度增加 (需要JOIN多个表)
- API调用数增加 (若要获取所有数据需多次query)

### 决策: **推荐采纳** (但建议从Phase 2实施，Phase 1先用嵌入式模型)

---

## 3️⃣ Scenario 模型优化

### 现有设计的问题

```json
{
  "scenario_id": "uuid",
  "owner_id": "uuid",
  "name": "string",
  "base_event": {
    "event_type": "string",
    "trigger_member_id": "uuid",
    "scale": "enum",
    "planned_at": "ISO8601",
    "precision": "enum"
  },
  "variant_on": {  // ❌ 表意不清：是"基于历史event修改"还是"纯虚拟假如"?
    "base_event_id": "uuid (optional)",
    "what_if_changes": {
      "scale": "enum (若改变规模)",  // ❌ 只支持scale?
      "timing_shift_months": "number",
      "additional_context": "string"
    }
  },
  "analysis_result": {
    "timeline": {
      "trigger_date": "ISO8601",
      "impact_window_start_months": "number",  // ❌ 模糊：相对于什么时间算起?
      "impact_window_end_months": "number",
      "peak_impact_month": "number"
    },
    "similar_historical_cases": [  // ❌ 这些数据来自哪里?
      {
        "case_description": "string",
        "actual_year": "number",
        "outcome": "string"
      }
    ]
  }
}
```

### 优化方案C: 明确concept + 添加字段

**改进**:
```json
{
  "scenario_id": "uuid",
  "owner_id": "uuid",
  "name": "string",
  "scenario_type": "enum: HYPOTHETICAL | BASED_ON_ACTUAL_EVENT",  // 新增：明确类型
  
  // 类型1: 虚拟假如场景
  "hypothetical_variant": {  // 改名，更清楚
    "scenario_for_member_id": "uuid",
    "reference_event_type": "enum: 投资 | 搬迁 | ...",
    "what_if_differences": {
      "planned_date_shift_months": "number",  // 改为更明确的名字
      "planned_scale_override": "enum: SMALL | MEDIUM | LARGE (可选)",
      "additional_context": "string"
    }
  },
  
  // 类型2: 基于历史event的变体
  "actual_variant": {  // 新增option
    "based_on_event_id": "uuid (FK events.event_id)",
    "assumed_changes": "string (e.g., '若规模提升50%')"
  },
  
  "analysis_result": {
    "summary": "string",
    "impact_breakdown": {
      "love": {"score": 0-100, "explanation": "string"},
      "wealth": {"score": 0-100, "explanation": "string"},
      "family": {"score": 0-100, "explanation": "string"}
    },
    "timeline": {
      "event_trigger_date": "ISO8601",  // 更明确
      "impact_window": {
        "start_months_after": "number",  // "相对于trigger_date"
        "end_months_after": "number",
        "peak_impact_month_after": "number"
      },
      "recovery_timeline": "string (e.g., '2026年9月后逐步恢复')"
    },
    "similar_cases": [
      {
        "case_id": "uuid (指向case库)",  // 改为ID，可追踪来源
        "case_year": "number",
        "outcome_summary": "string",
        "match_confidence": "number 0-1"
      }
    ],
    "model_metadata": {
      "model_version": "string",
      "model_confidence": "number 0-1",
      "computed_at": "ISO8601"
    }
  },
  "risk_assessment": {
    "risk_level": "enum: LOW | MEDIUM | HIGH | CRITICAL",
    "risk_factors": [  // 新增：风险构成
      {
        "factor": "string (e.g., '大运冲克财星')",
        "weight": "number 0-1",
        "contribution_to_risk": "number %"
      }
    ],
    "if_high_risk": {
      "warning_message": "string",
      "requires_approval": "boolean",
      "approval_reason": "string"
    }
  },
  "audit": {
    "created_at": "ISO8601",
    "created_by": "uuid",
    "updated_at": "ISO8601",
    "last_analyzed_at": "ISO8601"  // 新增：上次分析时间
  }
}
```

**优点**:
- 清确区分2种scenario (虚拟 vs 基于实际)
- Timeline逻辑明确 ("相对于event trigger date")
- 可追踪case来源和置信度
- 风险因素可视化分解

**缺点**:
- 字段略多 (但逻辑更清晰)

### 决策: **推荐采纳**

---

## 4️⃣ confidence_score计算公式明确化

### 当前问题
```python
confidence_score = weighted_sum(
    birth_precision[0.4] + 
    evidence_quantity[0.3] + 
    historical_accuracy[0.3]
)
```
✓ 公式没问题，但需要**明确各因子的计算方式**

### 优化方案D: 补充计算细节

```python
# constants/confidence.py
CONFIDENCE_CALCULATION = {
    "birth_precision": {
        "weight": 0.4,
        "factors": {
            "time_exact": 100,  # 时辰精确到刻
            "time_estimated_quarter_hour": 80,  # 精确到1刻钟
            "time_estimated_hour": 60,  # 精确到某时
            "time_uncertain": 30,  # 只有年月日
            "date_exact": 100,  # 有出生证明
            "date_estimated": 50,  # 家人回忆
            "date_approximated": 20,  # 只知道大概月份
        },
        "formula": "avg(time_score, date_score)"
    },
    "evidence_quantity": {
        "weight": 0.3,
        "factors": {
            "formula": "min(evidence_count * 10, 100)",  # 10项证据达到100分
        }
    },
    "historical_accuracy": {
        "weight": 0.3,
        "factors": {
            "formula": "historical_event_prediction_accuracy %"  # 历史事件验证准确率
        }
    }
}

def calculate_confidence_score(member_data: dict) -> dict:
    """
    计算置信度
    
    Returns:
        {
          "overall_score": 75,
          "breakdown": {
            "birth_precision": {"score": 80, "factors": {...}},
            "evidence_quantity": {"score": 70, "factors": {...}},
            "historical_accuracy": {"score": 65, "factors": {...}}
          },
          "interpretation": "中等置信，建议补充时辰信息"
        }
    """
    
    bp_score = ...  # 计算birth_precision
    eq_score = ...  # 计算evidence_quantity
    ha_score = ...  # 计算historical_accuracy
    
    overall = (bp_score * 0.4 + eq_score * 0.3 + ha_score * 0.3)
    
    # 生成人类可读的解释
    if overall >= 90:
        interpretation = "高置信，可作为重要决策依据"
    elif overall >= 70:
        interpretation = "中等置信，建议结合其他因素判断"
    else:
        interpretation = "低置信，建议补充信息后重新计算"
    
    return {
        "overall_score": round(overall),
        "breakdown": {
            "birth_precision": {"score": bp_score, ...},
            "evidence_quantity": {"score": eq_score, ...},
            "historical_accuracy": {"score": ha_score, ...}
        },
        "interpretation": interpretation,
        "next_actions": [...]  # 如何提升置信度
    }
```

### 决策: **推荐采纳** (内部补充，无需改schema)

---

## 📋 总结：推荐的数据模型调整清单

| 编号 | 模型 | 调整 | 优先级 | Phase |
|------|------|------|--------|-------|
| A1 | Member | 移除`is_time_uncertain`, 用`time_of_birth==null`判断 | P2 | 1 |
| A2 | Member | 移除`current_dayun_summary`，改为实时计算 | P2 | 1 |
| A3 | Member | 添加`location_lat`, `location_tz_offset`, `is_lunar` | P2 | 1 |
| B1 | Event | 拆表：event主表 + event_details + impact_scores + recommendations | P2 | 2 |
| B2 | Event | 移除`scale_context`，改为constants | P1 | 1 |
| B3 | Event | 移除status_changed_at/by，用audit log记录 | P1 | 1 |
| C1 | Scenario | 添加`scenario_type`区分虚拟vs实际 | P2 | 1-2 |
| C2 | Scenario | 明确`timeline.impact_window`相对于trigger_date | P2 | 1-2 |
| C3 | Scenario | 添加`risk_factors`明细分解 | P2 | 2 |
| D1 | ConfidenceModel | 在constants中明确计算公式 | P1 | 1 |

---

## 🚀 实施建议

### Phase 1 (Week 1-2): 内部调整 (无schema变更)
- [x] 常量化`scale_context`, `CONFIDENCE_CALCULATION`
- [x] Docstring补充说明(birth_precision, timeline相对计算)

### Phase 2 (Week 3-10): 数据模型优化
- [ ] 执行表拆分 (Event → event + event_details + ...)
- [ ] 添加新字段 (Member.location_lat/tz_offset, Scenario.scenario_type等)
- [ ] 数据迁移脚本

### Phase 3+ (Month 2+): 后续优化
- [ ] 为大多数字段添加index
- [ ] 收集用户反馈，迭代schema

---

## ❓ 快速QA

**Q: 为什么不从开始就用最优化的schema?**
A: MVP需要快速上线。优化后的schema更符合最佳实践，但实施成本更高。建议先用简单模型验证产品市场匹配度，再优化。

**Q: Event表拆分后性能会更快吗?**
A: 主表查询更快 ✓ (字段少)，但若需要所有关联数据要JOIN或多次query，可能总耗时相同。建议后续用DB profile测量。

**Q: Member的location_lat/tz_offset是必须的吗?**
A: 目前可选 (v1.0)。真太阳时转换现在只用location_lon。但若后续要精确地理定位，就需要lat + tz_offset。

