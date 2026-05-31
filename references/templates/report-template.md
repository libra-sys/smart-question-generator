# {{exam_title}}

---

## 考试说明

- **学科**: {{subject}}
- **总分**: {{total_score}}分 | **考试时间**: {{duration}}分钟
- **难度分布**: 易{{easy_pct}}% | 中{{medium_pct}}% | 难{{hard_pct}}%
- **Bloom覆盖**: {{bloom_distribution}}
- **知识点覆盖**: {{knowledge_summary}}

---

## 一、{{section1_type}}（共{{section1_count}}题，每题{{section1_points}}分，共{{section1_total}}分）

{{#section1_questions}}
{{> question_block}}
{{/section1_questions}}

---

## 二、{{section2_type}}（共{{section2_count}}题，每题{{section2_points}}分，共{{section2_total}}分）

{{#section2_questions}}
{{> question_block}}
{{/section2_questions}}

---

## 三、{{section3_type}}（共{{section3_count}}题，共{{section3_total}}分）

{{#section3_questions}}
{{> question_block}}
{{/section3_questions}}

---

## 参考答案与评分标准

### 客观题答案

| 题号 | 答案 | 分值 |
|------|------|:----:|
{{#objective_answers}}
| {{number}} | {{answer}} | {{points}} |
{{/objective_answers}}

### 主观题评分标准

{{#subjective_answers}}
#### 题目 {{number}} — 评分标准
{{scoring_rubric}}

{{/subjective_answers}}

---

## 知识点覆盖统计

| 知识点 | 题号 | 分值 | 占比 |
|--------|:----:|:----:|:----:|
{{#knowledge_coverage}}
| {{point}} | {{questions}} | {{score}} | {{percentage}}% |
{{/knowledge_coverage}}

**Bloom层次实际分布**: {{bloom_actual}}

**难度实际分布**: {{difficulty_actual}}

---

> *本试卷由智能出题系统自动生成，基于Bloom认知分类法和教育测量标准。建议教师人工审核后使用。*
