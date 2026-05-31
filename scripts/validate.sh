#!/bin/bash
# 智能出题系统试卷格式验证脚本
# 用法: bash validate.sh <试卷文件.md>

set -e

PAPER="$1"

if [ -z "$PAPER" ]; then
    echo "用法: bash validate.sh <试卷文件.md>"
    exit 1
fi

if [ ! -f "$PAPER" ]; then
    echo "错误: 文件 '$PAPER' 不存在"
    exit 1
fi

ERRORS=0
WARNINGS=0

echo "=========================================="
echo "  智能出题系统试卷格式验证"
echo "  目标文件: $PAPER"
echo "=========================================="

# 1. 试卷标题检查
echo ""
echo "[1/12] 试卷标题检查..."
if grep -q "^# " "$PAPER"; then
    TITLE=$(grep "^# " "$PAPER" | head -1 | sed 's/^# //')
    echo "  ✅ 试卷标题: $TITLE"
else
    echo "  ❌ 缺少一级标题（试卷标题）"
    ERRORS=$((ERRORS + 1))
fi

# 2. 考试说明检查
echo ""
echo "[2/12] 考试说明检查..."
EXAM_INFO=("学科" "总分" "难度分布" "Bloom")
for item in "${EXAM_INFO[@]}"; do
    if grep -q "$item" "$PAPER"; then
        echo "  ✅ $item"
    else
        echo "  ⚠️  缺少考试信息: $item"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 3. 题型标注检查
echo ""
echo "[3/12] 题型标注检查..."
QUESTION_TYPES=0
for qtype in "选择题" "填空题" "判断题" "简答题" "论述题" "案例分析" "编程题" "解答题"; do
    count=$(grep -c "题型.*$qtype\|$qtype.*共.*题" "$PAPER" || true)
    if [ "$count" -gt 0 ]; then
        echo "  ✅ $qtype ($count 处)"
        QUESTION_TYPES=$((QUESTION_TYPES + 1))
    fi
done
if [ "$QUESTION_TYPES" -eq 0 ]; then
    echo "  ❌ 未找到任何题型标注"
    ERRORS=$((ERRORS + 1))
fi

# 4. 题目Bloom层次标注检查
echo ""
echo "[4/12] Bloom层次标注检查..."
BLOOM_COUNT=$(grep -c "Bloom层次\|Bloom.*层次\|认知层次" "$PAPER" || true)
if [ "$BLOOM_COUNT" -ge 3 ]; then
    echo "  ✅ Bloom层次标注 ($BLOOM_COUNT 处)"
else
    echo "  ⚠️  Bloom层次标注不足 ($BLOOM_COUNT 处，建议≥3)"
    WARNINGS=$((WARNINGS + 1))
fi

# 5. 题目难度标注检查
echo ""
echo "[5/12] 题目难度标注检查..."
DIFF_COUNT=$(grep -c "预估难度\|难度.*易\|难度.*中\|难度.*难" "$PAPER" || true)
if [ "$DIFF_COUNT" -ge 3 ]; then
    echo "  ✅ 难度标注 ($DIFF_COUNT 处)"
else
    echo "  ⚠️  难度标注不足 ($DIFF_COUNT 处)"
    WARNINGS=$((WARNINGS + 1))
fi

# 6. 知识点标注检查
echo ""
echo "[6/12] 知识点标注检查..."
if grep -q "知识点" "$PAPER"; then
    echo "  ✅ 包含知识点标注"
else
    echo "  ❌ 缺少知识点标注"
    ERRORS=$((ERRORS + 1))
fi

# 7. 答案区域检查
echo ""
echo "[7/12] 答案区域检查..."
if grep -q "答案\|参考答案" "$PAPER"; then
    echo "  ✅ 包含答案区域"
else
    echo "  ❌ 缺少答案区域"
    ERRORS=$((ERRORS + 1))
fi

# 8. 解析完整性检查
echo ""
echo "[8/12] 解析完整性检查..."
PARSE_COUNT=$(grep -c "解析\|解题思路\|解题步骤\|分析" "$PAPER" || true)
QUESTION_COUNT=$(grep -c "^## 题目\|^## 第.*题" "$PAPER" || true)
if [ "$PARSE_COUNT" -ge "$QUESTION_COUNT" ] 2>/dev/null; then
    echo "  ✅ 解析覆盖完整 ($PARSE_COUNT/$QUESTION_COUNT)"
else
    echo "  ⚠️  解析可能不完整 ($PARSE_COUNT/$QUESTION_COUNT)"
    WARNINGS=$((WARNINGS + 1))
fi

# 9. 分值标注检查
echo ""
echo "[9/12] 分值标注检查..."
if grep -q "建议分值\|分值.*分\|每题.*分" "$PAPER"; then
    echo "  ✅ 包含分值标注"
else
    echo "  ⚠️  缺少明确的分值标注"
    WARNINGS=$((WARNINGS + 1))
fi

# 10. 评分标准检查
echo ""
echo "[10/12] 评分标准检查..."
if grep -q "评分标准\|评分细则\|给分标准\|扣分" "$PAPER"; then
    echo "  ✅ 包含评分标准"
else
    echo "  ⚠️  未找到评分标准（简答/论述题建议包含）"
    WARNINGS=$((WARNINGS + 1))
fi

# 11. 选择题选项检查
echo ""
echo "[11/12] 选择题选项检查..."
if grep -q "^[A-D][.、)]" "$PAPER" || grep -q "\*\*A\*\*\|选项.*A\." "$PAPER"; then
    OPT_A=$(grep -c "^[A][.、)] \|A[.、] \|A\." "$PAPER" || true)
    OPT_B=$(grep -c "^[B][.、)] \|B[.、] \|B\." "$PAPER" || true)
    OPT_C=$(grep -c "^[C][.、)] \|C[.、] \|C\." "$PAPER" || true)
    OPT_D=$(grep -c "^[D][.、)] \|D[.、] \|D\." "$PAPER" || true)
    echo "  ✅ 选择题选项 (A:$OPT_A B:$OPT_B C:$OPT_C D:$OPT_D)"
else
    echo "  ⚠️  未检测到标准选择题选项格式"
    WARNINGS=$((WARNINGS + 1))
fi

# 12. 题目编号连续性检查
echo ""
echo "[12/12] 题目编号连续性检查..."
SEQ=$(grep -oP '^## 题目 \K[0-9]+|^## 第\K[0-9]+(?=题)' "$PAPER" 2>/dev/null || true)
if [ -z "$SEQ" ]; then
    echo "  ⚠️  无法检测题目编号连续性（可能使用非标准编号格式）"
    WARNINGS=$((WARNINGS + 1))
else
    echo "  ✅ 检测到题目编号序列"
fi

# 汇总
echo ""
echo "=========================================="
echo "  验证结果汇总"
echo "=========================================="
echo "  错误: $ERRORS"
echo "  警告: $WARNINGS"

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo "  状态: ✅ 通过"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo "  状态: ⚠️  通过（有 $WARNINGS 个建议改进项）"
    exit 0
else
    echo "  状态: ❌ 不通过（$ERRORS 个错误需修复）"
    exit 1
fi
