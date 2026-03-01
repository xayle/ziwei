# Event推荐理由生成：三种架构方案 (v1.0)

## 问题描述

当前schema中Event.system_recommendation字段包含：
```json
{
  "reasoning": [
    {
      "reason": "用户在2026年6月需注意异常支出",
      "rule_id": "dayun_wealth_conflict_2026",
      "rule_version": "v1.2",
      "rule_reference": "《滴天髓》第三章火生土格局"
    }
  ],
  "mitigations": [
    {
      "action": "建议延迟大额投资至2026年8月",
      "priority": "HIGH"
    }
  ]
}
```

**问题**: 谁来生成这些推荐理由？  
- 手写? → 不可扩展 (100个规则要写100份文案)
- 模板? → 生硬，缺乏个性化
- AI? → 精确性难控，成本高
- 规则引擎? → 可维护，但需要专家编写规则

---

## 🎯 方案A: 规则引擎 + JSON规则库 (推荐，命理学学科化)

### 核心思想
将命理规则显式编码为JSON，Python评估JSON生成推荐。

### 规则库结构

```yaml
# rules/event_rules.json
{
  "rules": [
    {
      "rule_id": "dayun_wealth_conflict",
      "rule_name": "大运冲克财星",
      "category": "wealth",
      "condition": {
        "description": "日干属木/火，且大运天干为金，触发冲克",
        "logic": "AND",
        "checks": [
          {
            "field": "day_master.wuxing",
            "operator": "in",
            "value": ["wood", "fire"]
          },
          {
            "field": "current_dayun.wuxing",
            "operator": "equals",
            "value": "metal"
          }
        ]
      },
      "template": {
        "reason": "日干{day_wuxing}属性，大运{dayun_gan}天干属金，形成{conflict_type}冲克，主财运受阻",
        "recommendation": "建议暂缓大额投资/贷款，宜守财为主",
        "priority": "HIGH",
        "impact_timeline_months": 12,
        "confidence": 0.75
      },
      "references": ["《滴天髓》第三章财运格局", "《命理学基础》p.145"],
      "author": "命理师李某",
      "created_date": "2026-01-15",
      "version": "v1.2",
      "applicable_scenarios": ["investment", "loan", "business"]
    },
    
    {
      "rule_id": "peach_blossom_marriage",
      "rule_name": "桃花年遇",
      "category": "love",
      "condition": {
        "logic": "OR",
        "checks": [
          {
            "field": "current_year.gan",
            "operator": "in",
            "value": ["jia", "yi"],  # 甲乙
            "context": "member_gender = female"
          },
          {
            "field": "current_year.branch",
            "operator": "in",
            "value": ["wu", "you"]  # 午酉
          }
        ]
      },
      "template": {
        "reason": "当年遇到桃花年份{year_gan_zhi}，异性缘增强",
        "recommendation": "宜主动参加社交活动，但需注意筛选",
        "priority": "MEDIUM",
        "confidence": 0.60
      },
      "references": ["《命理学基础》桃花篇"],
      "version": "v1.0"
    }
  ]
}
```

### 推荐生成引擎

```python
# services/rule_engine_service.py
from typing import List, Dict, Any
import json
from datetime import datetime

class RuleEngineService:
    """规则引擎 - 用JSON规则生成推荐"""
    
    def __init__(self, rules_file: str = "rules/event_rules.json"):
        with open(rules_file) as f:
            self.rules = json.load(f)["rules"]
    
    async def generate_recommendations(self, 
                                      member_data: dict,
                                      event_data: dict) -> dict:
        """
        为event生成system_recommendation
        
        Args:
            member_data: {
              "day_master": {...},
              "wuxing_score": {...},
              "current_dayun": {...},
              "pillars": {...}
            }
            event_data: {
              "event_type": "投资",
              "scale": "大",
              "planned_at": "2026-05-01",
              ...
            }
        
        Returns:
            {
              "reasoning": [
                {
                  "reason": "...",
                  "rule_id": "...",
                  "rule_version": "v1.2",
                  "reason_confidence": 0.75
                }
              ],
              "mitigations": [...],
              "risk_level": "HIGH",
              "summary": "..."
            }
        """
        
        reasoning = []
        mitigations = []
        risk_scores = []
        
        # 1. 遍历所有规则
        for rule in self.rules:
            # 2. 检查规则是否适用
            if self._match_scenario(rule, event_data):
                # 3. 评估条件
                condition_met = await self._evaluate_condition(
                    rule["condition"], 
                    member_data
                )
                
                if condition_met:
                    # 4. 生成推荐理由
                    reason_obj = self._render_template(
                        rule,
                        member_data,
                        event_data
                    )
                    reasoning.append(reason_obj)
                    
                    # 5. 提取风险等级
                    priority = rule["template"].get("priority", "MEDIUM")
                    risk_scores.append(self._priority_to_score(priority))
                    
                    # 6. 生成缓解建议
                    mitigation = {
                        "action": reason_obj["recommendation"],
                        "priority": priority,
                        "category": rule["category"],
                        "rule_id": rule["rule_id"]
                    }
                    mitigations.append(mitigation)
        
        # 7. 汇总
        risk_level = self._calculate_risk_level(risk_scores)
        summary = self._generate_summary(reasoning, risk_level)
        
        return {
            "summary": summary,
            "reasoning": reasoning,
            "mitigations": mitigations,
            "risk_level": risk_level,
            "rule_count": len(reasoning),
            "model_confidence": min([r.get("reason_confidence", 0.7) 
                                    for r in reasoning]) if reasoning else 0.0,
            "generated_at": datetime.now(UTC).isoformat()
        }
    
    def _match_scenario(self, rule: dict, event_data: dict) -> bool:
        """检查规则是否适用于此event_type"""
        applicable = rule.get("applicable_scenarios", [])
        if not applicable:
            return True  # 默认适用所有
        return event_data["event_type"] in applicable
    
    async def _evaluate_condition(self, condition: dict, 
                                 member_data: dict) -> bool:
        """递归评估condition (支持AND/OR逻辑)"""
        logic = condition.get("logic", "AND")
        checks = condition.get("checks", [])
        
        results = []
        for check in checks:
            result = await self._evaluate_check(check, member_data)
            results.append(result)
        
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        return False
    
    async def _evaluate_check(self, check: dict, 
                            member_data: dict) -> bool:
        """评估单个check"""
        field = check["field"]
        operator = check["operator"]
        expected_value = check["value"]
        
        # 获取字段值 (支持嵌套字段 "day_master.wuxing")
        actual_value = self._get_nested_field(member_data, field)
        
        # 比较
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "in":
            return actual_value in expected_value
        elif operator == "gt":
            return actual_value > expected_value
        elif operator == "lt":
            return actual_value < expected_value
        
        return False
    
    def _render_template(self, rule: dict, 
                        member_data: dict, 
                        event_data: dict) -> dict:
        """
        使用模板生成推荐理由
        
        例: "日干{day_wuxing}属性，大运{dayun_gan}..." 
          → "日干火属性，大运金..."
        """
        template = rule["template"]
        
        # 收集模板变量
        variables = {
            "day_wuxing": self._translate_wuxing(
                member_data["day_master"]["wuxing"]
            ),
            "dayun_gan": member_data["current_dayun"]["gan"],
            "dayun_zhi": member_data["current_dayun"]["zhi"],
            "conflict_type": self._get_conflict_type(
                member_data["day_master"]["wuxing"],
                member_data["current_dayun"]["wuxing"]
            ),
            ...
        }
        
        # 渲染
        reason_text = template["reason"].format(**variables)
        recommendation_text = template["recommendation"].format(**variables)
        
        return {
            "reason": reason_text,
            "recommendation": recommendation_text,
            "rule_id": rule["rule_id"],
            "rule_version": rule.get("version", "v1.0"),
            "rule_reference": rule["references"][0] if rule["references"] else "",
            "reason_confidence": template.get("confidence", 0.70)
        }
    
    def _get_nested_field(self, data: dict, field_path: str):
        """获取嵌套字段 e.g., "day_master.wuxing" """
        parts = field_path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    
    def _priority_to_score(self, priority: str) -> float:
        """Convert priority to risk score"""
        mapping = {"HIGH": 0.9, "MEDIUM": 0.5, "LOW": 0.2}
        return mapping.get(priority, 0.5)
    
    def _calculate_risk_level(self, scores: List[float]) -> str:
        """Calculate overall risk level"""
        if not scores:
            return "LOW"
        avg = sum(scores) / len(scores)
        if avg >= 0.75:
            return "CRITICAL"
        elif avg >= 0.5:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _generate_summary(self, reasoning: List[dict], 
                        risk_level: str) -> str:
        """生成一句话总结"""
        if not reasoning:
            return "未检测到特殊命理因素"
        
        if risk_level == "CRITICAL":
            return f"发现{len(reasoning)}个高风险因素，强烈建议暂缓此事件"
        elif risk_level == "HIGH":
            return f"发现{len(reasoning)}个风险因素，建议谨慎推进"
        else:
            return f"发现{len(reasoning)}个需注意的因素，宜择日处理"
```

### API集成
```python
# routers/bazi.py
from services.rule_engine_service import RuleEngineService

rule_engine = RuleEngineService()

@router.post("/api/v1/scenarios")
async def create_scenario(payload: ScenarioCreateRequest):
    """创建假如场景"""
    
    # 1. 取出member数据
    member = await member_service.get(payload.base_event.trigger_member_id)
    
    # 2. 用规则引擎生成推荐
    recommendations = await rule_engine.generate_recommendations(
        member_data={
            "day_master": member.pillars.day.__dict__,
            "wuxing_score": member.computed_data.wuxing_score,
            "current_dayun": member.computed_data.current_dayun,
            "pillars": member.pillars.__dict__
        },
        event_data=payload.base_event.dict()
    )
    
    # 3. 保存scenario
    scenario = Scenario(
        analysis_result={
            "summary": recommendations["summary"],
            "reasoning": recommendations["reasoning"],
            "mitigations": recommendations["mitigations"],
            ...
        },
        risk_assessment={
            "risk_level": recommendations["risk_level"]
        }
    )
    
    await scenario_repo.save(scenario)
    return scenario
```

### 优点 ✅
- 可维护: 规则集中在一个JSON文件
- 可追踪: 每个推荐都有rule_id + version + reference (可问出处)
- 可扩展: 新增规则只需加JSON
- 易于审核: 非技术人员可读JSON规则

### 缺点 ❌
- 初期工作量大 (需要命理专家编写50+个规则)
- 规则表达能力受限 (JSON的condition有局限)

---

## 🎯 方案B: 预定义模板库 (快速上线，轻量级)

### 核心思想
维护一个推荐模板库，根据event_type + risk_level直接查表取模板。

### 实现

```python
# services/recommendation_templates.py

RECOMMENDATION_TEMPLATES = {
    ("投资", "HIGH"): [
        {
            "reason_pattern": "流年{year}与命盘主星冲克，主财运不利",
            "recommendation": "建议推迟至{safe_month}月后执行",
            "priority": "HIGH"
        },
        {
            "reason_pattern": "大运{dayun}处于衰弱阶段",
            "recommendation": "宜金额缩小50%以降低风险",
            "priority": "HIGH"
        }
    ],
    ("婚配", "MEDIUM"): [
        {
            "reason_pattern": "双方五行配置显示{conflict}现象",
            "recommendation": "建议咨询命理师深入分析后再定",
            "priority": "MEDIUM"
        }
    ],
    ("搬迁", "LOW"): [
        {
            "reason_pattern": "当年运势平和，无特殊禁忌",
            "recommendation": "可按计划进行，择吉日即可",
            "priority": "LOW"
        }
    ]
}

async def generate_recommendations_from_templates(
    event_type: str,
    risk_level: str,
    member_data: dict
) -> dict:
    """生成推荐 (用模板匹配)"""
    
    key = (event_type, risk_level)
    templates = RECOMMENDATION_TEMPLATES.get(key, [])
    
    reasoning = []
    for template in templates:
        # 填入变量
        reason = template["reason_pattern"].format(
            year=member_data["current_year"],
            dayun=member_data["current_dayun"]["gan_zhi"],
            conflict="相冲" if check_conflict(...) else "相生"
        )
        
        reasoning.append({
            "reason": reason,
            "recommendation": template["recommendation"],
            "priority": template["priority"],
            "rule_id": f"template_{event_type}_{risk_level}"
        })
    
    return {"reasoning": reasoning, ...}
```

### 优点 ✅
- 快速上线 (一天完成)
- 维护简单 (只需维护模板库)
- 性能好 (直接查表，无复杂计算)

### 缺点 ❌
- 灵活性差 (模板容易显得生硬)
- 无法追踪rule版本 (无法回答"为什么这么说")
- 扩展性差 (新增event_type要加模板)

---

## 🎯 方案C: LLM辅助生成 (高级，高成本)

### 核心思想
用大模型 (ChatGPT/Claude/本地LLM) 基于命理规则生成自然语言推荐。

### 实现

```python
# services/llm_recommendation_service.py
import anthropic

class LLMRecommendationService:
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate_with_llm(self, 
                               member_profile: str,
                               event_description: str,
                               rule_base: str) -> dict:
        """
        用LLM生成推荐理由
        
        Prompt思路:
        - 系统提示: 我是命理顾问，基于以下规则库生成建议
        - 输入: 成员信息 + 事件 + 规则库
        - 输出: JSON格式的reasoning + mitigations
        """
        
        prompt = f"""
你是一位资深命理师。基于以下命理规则库，为用户事件生成建议。

【命理规则库】
{rule_base}

【用户信息】
{member_profile}

【计划事件】
{event_description}

请输出JSON格式的建议，包含:
1. reasoning: 推荐理由列表 (每条包含reason/rule_id/confidence)
2. mitigations: 缓解措施列表 (每条包含action/priority)
3. risk_level: 风险等级 (LOW/MEDIUM/HIGH/CRITICAL)
4. summary: 一句话总结

要求:
- 每条理由必须有明确的命理学依据
- confidence范围0-1，表示该理由的可信度
- 优先使用rule_base中的rule_id
- 若rule_base无对应规则，需明确说明这是"非标准规则"
"""
        
        message = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析response
        response_text = message.content[0].text
        json_obj = json.loads(extract_json_from_text(response_text))
        
        return {
            "reasoning": json_obj["reasoning"],
            "mitigations": json_obj["mitigations"],
            "risk_level": json_obj["risk_level"],
            "summary": json_obj["summary"],
            "model": "claude-3-opus",
            "llm_generated": True,
            "confidence_disclaimer": "该建议由AI生成，建议咨询专业命理师确认"
        }
```

### 优点 ✅
- 自然流畅 (LLM生成的文案质量高)
- 灵活性强 (可处理规则库外的情况)
- 个性化 (每次生成不同，更接近真实顾客体验)

### 缺点 ❌
- **成本高**: 每个API调用 ~0.01 USD
- **可信度低**: LLM可能幻觉 (生成错误的命理理由)
- **难以追踪**: "为什么这样说" → "LLM说的" (用户信任度差)
- **需要人工审核**: 每个推荐都需要命理师过目

---

## 📊 方案对比

| 指标 | 方案A (规则) | 方案B (模板) | 方案C (LLM) |
|------|----------|---------|---------|
| **上线时间** | 4-6周 | 3天 ✓ | 1周 |
| **维护成本** | 中 | 低 ✓ | 高 |
| **灵活性** | 高 | 低 | 高 ✓ |
| **精准度** | 高 ✓ | 中 | 中 |
| **可追踪性** | 高 ✓ | 低 | 低 |
| **成本** | 免费 ✓ | 免费 ✓ | $0.01/API |
| **用户信任** | 高 ✓ | 中 | 低 |

---

## 🎯 推荐方案：混合方案 Z (最佳实践)

### 架构
```
Phase 1 (Week 1-2): 上线方案B (模板) ✓
  • 3天快速上线
  • 满足MVP需求
  • 获得用户反馈

Phase 2 (Week 3-6): 迁移到方案A (规则) ✓
  • 用命理师编写规则库
  • 替换硬编码的模板
  • 提升精准度

Phase 3 (Month 2+): 可选方案C (LLM)
  • 用于"非标准"事件类型
  • LLM生成初稿 → 命理师审核 → 保存为规则
  • 逐步构建规则库
```

### 实现示例

```python
# services/recommendation_service_hybrid.py

class HybridRecommendationService:
    
    def __init__(self):
        self.template_service = TemplateService()  # 快速方案
        self.rule_engine = RuleEngineService()     # 规则引擎
        self.llm_service = LLMService()             # LLM服务
    
    async def generate_recommendations(self, member, event):
        """混合方案: 按优先级尝试"""
        
        # Level 1: 优先用规则引擎 (最精准)
        if self.rule_engine.is_applicable(event):
            return await self.rule_engine.generate(member, event)
        
        # Level 2: 退到模板 (快速、可靠)
        if self.template_service.has_template(event.type, event.scale):
            return await self.template_service.generate(member, event)
        
        # Level 3: 用LLM生成 (灵活、但需审核)
        llm_result = await self.llm_service.generate(member,event)
        llm_result["review_status"] = "PENDING_MANUAL_REVIEW"
        
        # 存储为草稿规则 (供后续转为正式规则)
        await self._save_draft_rule(llm_result)
        
        return llm_result
```

---

## 🚀 立即行动 (建议顺序)

### Week 1 (MVP)
- [ ] 实现方案B (模板) - 3天快速上线

### Week 2
- [ ] 由命理师编写规则库 (30-50个规则)

### Week 3-4
- [ ] 实现方案A (规则引擎) - 迁移模板

### Month 2+ (可选)
- [ ] 集成方案C (LLM) - 用于非标准case

