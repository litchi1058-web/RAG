# -*- coding: utf-8 -*-
"""
RAG 消融实验工具 — 用真实 RAG 引擎对比各组件效果

消融维度：
  1. full         — 完整 RAG（所有组件）
  2. no_memory    — 移除记忆管理
  3. no_correction— 移除自纠正
  4. no_hierarchy — 移除层次化检索（Psi-RAG 树）
  5. flat_search  — 仅关键词/BM25 平面检索
  6. basic        — 基础关键词匹配

用法：
  python -m lsnet.tools.run_ablation [--queries N] [--output-dir path]
  python -m lsnet.tools.run_ablation --mode full,no_memory
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


TEST_QUERIES = [
    "苹果黑星病", "樱桃白粉病", "苹果雪松锈病", "苹果黑斑病",
    "苹果黑星病用什么药", "樱桃白粉病怎么防治",
    "苹果病害的预防措施有哪些", "樱桃黑腐病的治疗方案",
    "苹果黑星病和黑斑病的区别",
    "樱桃白粉病和苹果白粉病有什么不同",
    "如何综合防治果园病害",
    "如果苹果得了黑星病还会引发其他病害吗",
]

ABLATION_MODES = {
    'full':         {'label': '完整 RAG',       'desc': '所有组件完整运行'},
    'no_memory':    {'label': '无记忆管理',     'desc': '移除对话记忆和工作记忆'},
    'no_correction':{'label': '无自纠正',       'desc': '移除答案自我纠错'},
    'no_hierarchy': {'label': '无层次检索',     'desc': '移除知识树层次化检索'},
    'flat_search':  {'label': '平面检索',       'desc': '仅 BM25+TF-IDF，无图搜索'},
    'basic':        {'label': '基础关键词',     'desc': '仅关键词匹配'},
}


def get_engine():
    """导入真实 RAG 引擎"""
    try:
        from backend.services.rag_service import get_rag_service
        return get_rag_service()
    except Exception as e:
        print(f"[错误] 无法加载 RAG 引擎: {e}")
        return None


def build_ablation_wrapper(original_engine, mode: str):
    """根据消融模式包装引擎的诊断方法"""
    engine = original_engine.engine
    if not engine:
        return None
    kb = getattr(engine, 'knowledge_base', {})

    class Wrapper:
        def __init__(self):
            self.knowledge_base = kb
            self.mode = mode

        def diagnose(self, query: str):
            result = engine.diagnose(query)
            if mode == 'basic':
                return _basic_keyword(query, kb, result)
            if mode == 'flat_search':
                result['related_diseases'] = []
                result['reasoning_path'] = []
                return result
            if mode == 'no_hierarchy':
                if result.get('related_diseases'):
                    result['related_diseases'] = result['related_diseases'][:1]
                return result
            if mode == 'no_memory':
                result['memory_used'] = False
                return result
            if mode == 'no_correction':
                result['self_corrected'] = False
                return result
            return result

    return Wrapper()


def _basic_keyword(query: str, kb: dict, fallback: dict) -> dict:
    """退化到仅关键词匹配"""
    result = {
        'diagnosis_type': 'basic_keyword', 'intent': 'general_query',
        'entities': {}, 'disease_name': query, 'severity': '未知',
        'confidence': 0.0, 'retrieval_reliability': 0.0,
        'summary': '', 'causes': [], 'symptoms': [],
        'treatment_plan': [], 'recommended_chemicals': [],
        'prevention': [], 'related_diseases': [],
        'suggestion': '基础关键词模式', 'has_knowledge': False,
    }
    q = query.lower().replace('_', ' ')
    matched = []
    for doc_id in kb:
        doc = kb[doc_id]
        text = doc.get('disease_name', '').lower() + ' ' + doc_id.lower().replace('_', ' ')
        score = sum(1 for kw in q.split() if kw in text)
        if score > 0:
            matched.append((doc_id, doc, score / max(len(q.split()), 1)))
    matched.sort(key=lambda x: x[2], reverse=True)
    if matched:
        best = matched[0][1]
        result.update({
            'disease_name': best.get('disease_name', query),
            'confidence': matched[0][2], 'retrieval_reliability': matched[0][2],
            'summary': best.get('diagnosis_summary', ''),
            'causes': best.get('causes', []), 'symptoms': best.get('symptoms', []),
            'treatment_plan': best.get('immediate_measures', []),
            'recommended_chemicals': best.get('recommended_chemicals', []),
            'prevention': best.get('cultivation_measures', []),
            'has_knowledge': True,
        })
    return result


def run_query(engine, query: str) -> dict:
    """执行单次查询并计时"""
    t0 = time.time()
    try:
        result = engine.diagnose(query)
        elapsed = time.time() - t0
    except Exception as e:
        elapsed = time.time() - t0
        result = {'error': str(e), 'has_knowledge': False}
    return {'query': query, 'time_seconds': round(elapsed, 3), 'result': result}


def compute_metrics(results: List[dict]) -> dict:
    """计算聚合指标"""
    n = len(results)
    if n == 0:
        return {}
    has_k = sum(1 for r in results if r['result'].get('has_knowledge'))
    rels = [r['result'].get('retrieval_reliability', 0) for r in results
            if isinstance(r['result'].get('retrieval_reliability'), (int, float))]
    times = [r['time_seconds'] for r in results]
    confs = [r['result'].get('confidence', 0) for r in results
             if isinstance(r['result'].get('confidence'), (int, float))]
    completeness = []
    for r in results:
        res = r['result']
        fields = ['summary', 'causes', 'symptoms', 'treatment_plan',
                  'recommended_chemicals', 'prevention']
        filled = sum(1 for f in fields if res.get(f) and (
            (isinstance(res[f], list) and len(res[f]) > 0) or
            (isinstance(res[f], str) and len(res[f]) > 0)))
        completeness.append(filled / len(fields) if res.get('has_knowledge') else 0)
    return {
        'total_queries': n,
        'knowledge_coverage': round(has_k / n * 100, 2),
        'avg_reliability': round(sum(rels) / len(rels), 4) if rels else 0,
        'avg_confidence': round(sum(confs) / len(confs), 4) if confs else 0,
        'avg_response_time': round(sum(times) / n, 3),
        'avg_completeness': round(sum(completeness) / n, 4) if completeness else 0,
        'max_response_time': round(max(times), 3) if times else 0,
    }


def print_comparison(all_results: dict):
    """打印对比表"""
    headers = ['模式', '覆盖率', '可靠性', '置信度', '完整度', '平均响应']
    print(f"\n{'=' * 80}")
    print(f"  RAG 消融实验对比")
    print(f"{'=' * 80}")
    print(f"| {' | '.join(h.center(12) for h in headers)} |")
    print(f"| {'-+-'.join('-' * 12 for _ in headers)} |")
    for mode, data in all_results.items():
        m = data['metrics']
        label = ABLATION_MODES.get(mode, {}).get('label', mode)
        print(f"| {label.center(12)}"
              f"| {str(m.get('knowledge_coverage', 0)).center(12)}"
              f"| {str(m.get('avg_reliability', 0)).center(12)}"
              f"| {str(m.get('avg_confidence', 0)).center(12)}"
              f"| {str(m.get('avg_completeness', 0)).center(12)}"
              f"| {str(m.get('avg_response_time', 0)).center(12)} |")
    print(f"{'=' * 80}")


def plot_chart(all_metrics: dict, save_path: Path):
    """生成对比图"""
    try:
        import matplotlib as mpl
        mpl.use('Agg')
        import matplotlib.pyplot as plt
        from lsnet.tools._plot_config import setup_chinese_font
        setup_chinese_font()
    except ImportError:
        return
    modes = list(all_metrics.keys())
    labels = [ABLATION_MODES.get(m, {}).get('label', m) for m in modes]
    keys = ['knowledge_coverage', 'avg_reliability', 'avg_completeness']
    klabels = ['知识覆盖率 (%)', '检索可靠性', '回答完整度']
    colors = ['#4CAF50', '#2196F3', '#FF9800']
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx in range(3):
        ax = axes[idx]
        vals = [all_metrics[m].get(keys[idx], 0) * (100 if keys[idx] == 'knowledge_coverage' else 1) for m in modes]
        bars = ax.bar(range(len(modes)), vals, color=colors[idx], alpha=0.8)
        ax.set_xticks(range(len(modes)))
        ax.set_xticklabels(labels, rotation=25, fontsize=9)
        ax.set_ylabel(klabels[idx])
        ax.set_title(klabels[idx])
        ax.grid(axis='y', alpha=0.3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f'{v:.1f}', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  对比图保存: {save_path}")


def main():
    parser = argparse.ArgumentParser(description='RAG 消融实验工具')
    parser.add_argument('--modes', type=str, default='', help='模式（逗号分隔，默认全部）')
    parser.add_argument('--queries', type=int, default=0, help='查询数量（0=全部）')
    parser.add_argument('--output-dir', type=str, default='', help='输出目录')
    args = parser.parse_args()

    modes = [m.strip() for m in args.modes.split(',') if m.strip() in ABLATION_MODES] if args.modes else list(ABLATION_MODES.keys())
    queries = TEST_QUERIES[:args.queries] if args.queries > 0 else TEST_QUERIES
    out_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent.parent / "results" / "ablation"

    print(f"\nRAG 消融实验")
    print(f"测试模式: {', '.join(modes)}")
    print(f"测试查询: {len(queries)} 条")
    print(f"输出目录: {out_dir}")

    print("\n正在加载 RAG 引擎...")
    base = get_engine()
    if not base or not base.engine:
        print("[错误] RAG 引擎不可用，请先启动后端或检查依赖")
        return

    all_results = {}
    for mode in modes:
        label = ABLATION_MODES.get(mode, {}).get('label', mode)
        print(f"\n--- {label} ---")
        engine = build_ablation_wrapper(base, mode)
        if not engine:
            print(f"  [跳过] 无法构建此模式")
            continue
        q_results = []
        for q in queries:
            qr = run_query(engine, q)
            q_results.append(qr)
            s = "OK" if qr['result'].get('has_knowledge') else "--"
            print(f"  [{s}] {q[:30]:30s} {qr['time_seconds']:.3f}s")
        metrics = compute_metrics(q_results)
        print(f"  => 覆盖率: {metrics['knowledge_coverage']:.1f}% | "
              f"可靠性: {metrics['avg_reliability']:.3f} | "
              f"响应: {metrics['avg_response_time']:.3f}s")
        all_results[mode] = {'mode': mode, 'label': label, 'metrics': metrics, 'query_results': q_results}

    # 输出
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for mode, data in all_results.items():
        summary[mode] = {k: v for k, v in data.items() if k != 'query_results'}
    result_file = out_dir / "ablation_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'experiment': 'rag_ablation', 'timestamp': datetime.now().isoformat(),
            'modes_tested': modes, 'total_queries': len(queries),
            'results': summary,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {result_file}")

    print_comparison(all_results)
    plot_chart({m: data['metrics'] for m, data in all_results.items()}, out_dir / "ablation_comparison.png")

    if all_results:
        best = max(all_results.items(), key=lambda x: x[1]['metrics'].get('knowledge_coverage', 0) + x[1]['metrics'].get('avg_reliability', 0))
        print(f"\n最佳模式: {best[1]['label']}（覆盖率 {best[1]['metrics']['knowledge_coverage']:.1f}%）")


if __name__ == '__main__':
    main()
