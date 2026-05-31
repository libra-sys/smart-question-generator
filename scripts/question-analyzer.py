#!/usr/bin/env python3
"""
智能出题系统 — 题目分析与组卷辅助工具
功能：知识点覆盖率分析、难度分布校验、Bloom层次统计、题目质量评分
"""

import re
import json
import argparse
import sys
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter


# Bloom认知层次
BLOOM_LEVELS = {
    "记忆": {"weight": 1.0, "description": "识别和回忆事实性知识"},
    "理解": {"weight": 1.5, "description": "解释、举例、分类、总结、推断、比较、说明"},
    "应用": {"weight": 2.0, "description": "执行或实施程序、方法"},
    "分析": {"weight": 2.5, "description": "区别、组织、归因"},
    "评价": {"weight": 3.0, "description": "检查、评论、判断"},
    "创造": {"weight": 3.5, "description": "生成、计划、产生"},
}


# 难度等级映射
DIFFICULTY_LEVELS = {
    "易": {"range": (1, 3), "expected_percent": 30},
    "中": {"range": (4, 6), "expected_percent": 50},
    "难": {"range": (7, 9), "expected_percent": 20},
}


# 常见题型
QUESTION_TYPES = [
    "单选题", "多选题", "判断题", "填空题",
    "简答题", "论述题", "案例分析题", "编程题",
    "匹配题", "排序题",
]


def extract_difficulty(text: str) -> Optional[str]:
    """从题目文本中提取难度标注"""
    patterns = [
        r'预估难度[：:]\s*(易|中|难)',
        r'难度[：:]\s*(易|中|难)',
        r'\[(易|中|难)\]',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def extract_bloom(text: str) -> Optional[str]:
    """从题目文本中提取Bloom层次"""
    patterns = [
        r'Bloom层次[：:]\s*(记忆|理解|应用|分析|评价|创造)',
        r'认知层次[：:]\s*(记忆|理解|应用|分析|评价|创造)',
        r'Bloom[：:]\s*(记忆|理解|应用|分析|评价|创造)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def extract_points(text: str) -> Optional[float]:
    """从题目文本中提取分值"""
    patterns = [
        r'建议分值[：:]\s*(\d+(?:\.\d+)?)\s*分',
        r'分值[：:]\s*(\d+(?:\.\d+)?)\s*分',
        r'\[(\d+)分\]',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    return None


def extract_type(text: str) -> Optional[str]:
    """从题目文本中提取题型"""
    patterns = [
        r'题型[：:]\s*(.+?)(?:\n|$)',
        r'\*\*题型\*\*[：:]\s*(.+?)(?:\n|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_knowledge_point(text: str) -> Optional[str]:
    """从题目文本中提取知识点"""
    pattern = r'知识点[：:]\s*(.+?)(?:\n|$)'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def parse_paper(paper_text: str) -> Dict:
    """
    解析试卷文本，提取所有题目信息

    Returns:
        {
            "title": str,
            "subject": str,
            "total_score": float,
            "questions": List[Dict],
            "statistics": Dict
        }
    """
    result = {
        "title": "",
        "subject": "",
        "total_score": 0,
        "questions": [],
        "statistics": {},
    }

    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', paper_text, re.MULTILINE)
    if title_match:
        result["title"] = title_match.group(1).strip()

    # 提取学科
    subj_match = re.search(r'学科[：:]\s*(.+?)(?:\n|$)', paper_text)
    if subj_match:
        result["subject"] = subj_match.group(1).strip()

    # 提取总分
    score_match = re.search(r'总分[：:]\s*(\d+)', paper_text)
    if score_match:
        result["total_score"] = float(score_match.group(1))

    # 按题目拆分
    question_blocks = re.split(r'\n(?=## 题目 |## 第\d+题)', paper_text)

    for i, block in enumerate(question_blocks):
        if not block.strip() or not re.search(r'题目|第\d+题', block):
            continue

        q_info = {
            "index": i + 1,
            "type": extract_type(block),
            "bloom": extract_bloom(block),
            "difficulty": extract_difficulty(block),
            "points": extract_points(block),
            "knowledge_point": extract_knowledge_point(block),
        }
        result["questions"].append(q_info)

    # 统计
    stats = analyze_statistics(result["questions"])
    result["statistics"] = stats

    return result


def analyze_statistics(questions: List[Dict]) -> Dict:
    """分析题目的统计特性"""
    stats = {
        "total_questions": len(questions),
        "total_points": 0,
        "type_distribution": Counter(),
        "bloom_distribution": Counter(),
        "difficulty_distribution": Counter(),
        "knowledge_points": set(),
        "knowledge_coverage_warning": "",
    }

    for q in questions:
        if q["points"]:
            stats["total_points"] += q["points"]
        if q["type"]:
            stats["type_distribution"][q["type"]] += 1
        if q["bloom"]:
            stats["bloom_distribution"][q["bloom"]] += 1
        if q["difficulty"]:
            stats["difficulty_distribution"][q["difficulty"]] += 1
        if q["knowledge_point"]:
            stats["knowledge_points"].add(q["knowledge_point"])

    return stats


def calculate_difficulty_score(
    bloom_level: str,
    step_count: int = 1,
    knowledge_depth: int = 1
) -> Tuple[str, float]:
    """
    基于Bloom层次、解题步骤数、知识点深度计算难度评分

    Args:
        bloom_level: Bloom认知层次
        step_count: 解题所需步骤数
        knowledge_depth: 涉及知识点的深度（1-5）

    Returns:
        (难度等级, 难度评分 1-9)
    """
    bloom_weight = BLOOM_LEVELS.get(bloom_level, {}).get("weight", 1.5)

    score = (bloom_weight * 1.5) + (step_count * 0.5) + (knowledge_depth * 0.3)
    score = min(max(score, 1), 9)

    if score <= 3:
        difficulty = "易"
    elif score <= 6:
        difficulty = "中"
    else:
        difficulty = "难"

    return difficulty, round(score, 1)


def check_difficulty_balance(questions: List[Dict], expected: Dict[str, float]) -> Dict:
    """
    检查难度分布是否符合预期

    Args:
        questions: 题目列表
        expected: 预期的难度比例，如 {"易": 30, "中": 50, "难": 20}

    Returns:
        {
            "balanced": bool,
            "actual": Dict[str, float],
            "expected": Dict[str, float],
            "deviations": Dict[str, float]
        }
    """
    total = len(questions)
    if total == 0:
        return {"balanced": True, "actual": {}, "expected": expected, "deviations": {}}

    actual = {}
    for q in questions:
        diff = q.get("difficulty", "未知")
        actual[diff] = actual.get(diff, 0) + 1

    # 转换为百分比
    actual_pct = {k: round(v / total * 100, 1) for k, v in actual.items()}

    deviations = {}
    balanced = True
    for level, expected_pct in expected.items():
        actual_val = actual_pct.get(level, 0)
        dev = abs(actual_val - expected_pct)
        deviations[level] = round(dev, 1)
        if dev > 5:  # 偏差超过5%判定为不均衡
            balanced = False

    return {
        "balanced": balanced,
        "actual": actual_pct,
        "expected": expected,
        "deviations": deviations,
    }


def check_knowledge_coverage(
    questions: List[Dict],
    required_kps: Set[str],
    min_coverage: float = 0.8
) -> Dict:
    """
    检查知识点覆盖率

    Args:
        questions: 题目列表
        required_kps: 必覆盖知识点集合
        min_coverage: 最低覆盖率阈值（默认80%）

    Returns:
        {
            "covered": int,
            "total": int,
            "coverage": float,
            "passed": bool,
            "missing": List[str]
        }
    """
    covered = set()
    for q in questions:
        kp = q.get("knowledge_point")
        if kp:
            covered.add(kp)

    missing = required_kps - covered
    coverage = len(covered) / len(required_kps) if required_kps else 1.0

    return {
        "covered": len(covered),
        "total": len(required_kps),
        "coverage": round(coverage, 2),
        "passed": coverage >= min_coverage,
        "missing": list(missing),
    }


def suggest_point_allocation(
    bloom_level: str,
    difficulty: str,
    question_type: str
) -> float:
    """
    根据Bloom层次和难度建议分值
    """
    base_scores = {
        "单选题": 2, "多选题": 3, "判断题": 1, "填空题": 2,
        "简答题": 5, "论述题": 10, "案例分析题": 12, "编程题": 15,
    }

    base = base_scores.get(question_type, 5)

    bloom_mult = {
        "记忆": 0.8, "理解": 1.0, "应用": 1.2,
        "分析": 1.5, "评价": 1.8, "创造": 2.0,
    }.get(bloom_level, 1.0)

    diff_mult = {"易": 0.8, "中": 1.0, "难": 1.3}.get(difficulty, 1.0)

    return round(base * bloom_mult * diff_mult)


def main():
    parser = argparse.ArgumentParser(description="智能出题系统分析工具")
    parser.add_argument("--paper", "-p", help="试卷文件路径（Markdown格式）")
    parser.add_argument("--json", "-j", help="题目JSON数据文件")
    parser.add_argument("--check-balance", "-b", action="store_true",
                        help="检查难度分布均衡性")
    parser.add_argument("--check-coverage", "-c", action="store_true",
                        help="检查知识点覆盖率")
    parser.add_argument("--knowledge-points", "-k", nargs="*",
                        help="必覆盖的知识点列表")
    parser.add_argument("--expected-difficulty", "-d", nargs=3, type=float,
                        metavar=("EASY", "MEDIUM", "HARD"),
                        help="预期难度比例（易 中 难），如: 30 50 20")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text",
                        help="输出格式")

    args = parser.parse_args()

    questions = []
    paper_info = {}

    if args.paper:
        try:
            with open(args.paper, "r", encoding="utf-8") as f:
                paper_text = f.read()
        except FileNotFoundError:
            print(f"错误: 文件 '{args.paper}' 不存在", file=sys.stderr)
            sys.exit(1)

        paper_info = parse_paper(paper_text)
        questions = paper_info.get("questions", [])

    elif args.json:
        try:
            with open(args.json, "r", encoding="utf-8") as f:
                data = json.load(f)
            questions = data if isinstance(data, list) else data.get("questions", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"错误: 无法读取JSON文件 - {e}", file=sys.stderr)
            sys.exit(1)

    if not questions:
        print("错误: 未找到任何题目数据", file=sys.stderr)
        sys.exit(1)

    output = {}

    # 统计分析
    stats = analyze_statistics(questions)
    output["statistics"] = stats

    # 难度均衡检查
    if args.check_balance:
        if args.expected_difficulty:
            expected = {
                "易": args.expected_difficulty[0],
                "中": args.expected_difficulty[1],
                "难": args.expected_difficulty[2],
            }
        else:
            expected = {"易": 30, "中": 50, "难": 20}

        balance = check_difficulty_balance(questions, expected)
        output["difficulty_balance"] = balance

    # 知识点覆盖率检查
    if args.check_coverage and args.knowledge_points:
        coverage = check_knowledge_coverage(
            questions,
            set(args.knowledge_points),
        )
        output["knowledge_coverage"] = coverage

    # 格式化输出
    if args.format == "json":
        formatted = json.dumps(output, ensure_ascii=False, indent=2)
    else:
        lines = []
        lines.append("=" * 50)
        lines.append("  智能出题系统 — 题目分析报告")
        lines.append("=" * 50)

        s = output.get("statistics", {})
        lines.append(f"\n📊 题目总数: {s.get('total_questions', 0)}")
        lines.append(f"📊 总分: {s.get('total_points', 0)}")

        lines.append("\n📝 题型分布:")
        for qtype, count in s.get("type_distribution", {}).most_common():
            lines.append(f"  {qtype}: {count}题")

        lines.append("\n🧠 Bloom层次分布:")
        for level in ["记忆", "理解", "应用", "分析", "评价", "创造"]:
            count = s.get("bloom_distribution", {}).get(level, 0)
            lines.append(f"  {level}: {count}题")

        lines.append("\n📈 难度分布:")
        for level in ["易", "中", "难"]:
            count = s.get("difficulty_distribution", {}).get(level, 0)
            lines.append(f"  {level}: {count}题")

        if "difficulty_balance" in output:
            bal = output["difficulty_balance"]
            status = "✅ 均衡" if bal["balanced"] else "❌ 不均衡"
            lines.append(f"\n⚖️  难度均衡检查: {status}")
            for level, pct in bal["actual"].items():
                exp = bal["expected"].get(level, 0)
                dev = bal["deviations"].get(level, 0)
                lines.append(f"  {level}: 实际{pct}% / 预期{exp}% (偏差{dev}%)")

        if "knowledge_coverage" in output:
            cov = output["knowledge_coverage"]
            status = "✅ 达标" if cov["passed"] else "❌ 未达标"
            lines.append(f"\n📚 知识点覆盖率: {cov['coverage']*100:.0f}% {status}")
            lines.append(f"  覆盖: {cov['covered']}/{cov['total']}")
            if cov["missing"]:
                lines.append(f"  未覆盖: {', '.join(cov['missing'])}")

        lines.append("\n" + "=" * 50)
        formatted = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"分析结果已保存至: {args.output}")
    else:
        print(formatted)


if __name__ == "__main__":
    main()
