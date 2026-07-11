# -*- coding: utf-8 -*-
"""
知识图谱 API — Neo4j 图数据库 + 内存降级模式
"""
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
from fastapi import APIRouter, Query, Depends

from backend.api.deps import get_current_user
from backend.models.user import User
from backend.config import NEO4J_ENABLED, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/knowledge-graph', tags=['知识图谱'])

_driver = None


def _get_neo4j_driver():
    global _driver
    if _driver is None and NEO4J_ENABLED:
        try:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with _driver.session() as s:
                s.run("RETURN 1")
            logger.info("Neo4j 连接成功")
        except Exception as e:
            logger.warning(f"Neo4j 连接失败，使用内存模式: {e}")
            return None
    return _driver


def _get_knowledge_base():
    from backend.api.rag import COMPLETE_KNOWLEDGE_BASE, GRAPH_RELATIONS
    return COMPLETE_KNOWLEDGE_BASE, GRAPH_RELATIONS


def _build_memory_graph() -> Dict:
    kb, relations = _get_knowledge_base()
    node_id_counter = [0]
    nodes, edges, node_map = [], [], {}

    def _node(name: str, cat: str, detail: str = '') -> int:
        key = f"{cat}:{name}"
        if key in node_map:
            return node_map[key]
        node_id_counter[0] += 1
        nid = node_id_counter[0]
        nodes.append({'id': nid, 'name': name, 'category': cat, 'detail': detail[:200] if detail else ''})
        node_map[key] = nid
        return nid

    for key, entry in kb.items():
        parts = key.split('_')
        crop_name = parts[0] if len(parts) >= 2 else '未知'
        disease_name = entry.get('disease_name', key)
        crop_id = _node(crop_name, 'crop')
        disease_id = _node(disease_name, 'disease', entry.get('diagnosis_summary', ''))
        # 补充 risk_level 和 severity 到节点，供前端详情面板展示
        for n in nodes:
            if n['id'] == disease_id:
                n['risk_level'] = entry.get('risk_level', '')
                n['severity'] = entry.get('severity', '')[:50]
                break
        edges.append({'source': disease_id, 'target': crop_id, 'label': '属于'})

        sev = entry.get('severity', '')
        if sev:
            edges.append({'source': disease_id, 'target': _node(sev[:30], 'severity'), 'label': '严重程度'})
        risk = entry.get('risk_level', '')
        if risk:
            edges.append({'source': disease_id, 'target': _node(risk, 'risk_level'), 'label': '风险等级'})
        for s in entry.get('symptoms', []):
            edges.append({'source': disease_id, 'target': _node(s[:40], 'symptom', s), 'label': '症状'})
        for c in entry.get('causes', []):
            edges.append({'source': disease_id, 'target': _node(c[:40], 'cause', c), 'label': '成因'})
        for t in entry.get('treatment_plan', []):
            edges.append({'source': disease_id, 'target': _node(t[:40], 'treatment', t), 'label': '治疗方法'})
        for ch in entry.get('recommended_chemicals', []):
            ch_name = ch.get('name', str(ch)) if isinstance(ch, dict) else str(ch)
            edges.append({'source': disease_id, 'target': _node(ch_name[:40], 'chemical'), 'label': '推荐药剂'})
        for p in entry.get('cultivation_measures', []):
            edges.append({'source': disease_id, 'target': _node(p[:40], 'prevention', p), 'label': '预防措施'})

    for src_key, rel_data in relations.items():
        if src_key not in kb:
            continue
        src_name = kb[src_key].get('disease_name', src_key)
        src_id = node_map.get(f"disease:{src_name}")
        if src_id is None:
            continue
        for tgt_key in rel_data.get('related_diseases', []):
            if tgt_key not in kb:
                continue
            tgt_name = kb[tgt_key].get('disease_name', tgt_key)
            tgt_id = node_map.get(f"disease:{tgt_name}")
            if tgt_id:
                edges.append({'source': src_id, 'target': tgt_id, 'label': '相似病害'})

    return {'nodes': nodes, 'links': edges}


def _compute_stats(graph: Dict) -> Dict:
    nodes, edges = graph.get('nodes', []), graph.get('links', [])
    cc = defaultdict(int)
    for n in nodes:
        cc[n.get('category', 'unknown')] += 1
    max_e = len(nodes) * (len(nodes) - 1) / 2
    return {'total_nodes': len(nodes), 'total_edges': len(edges),
            'category_counts': dict(cc), 'density': round(len(edges) / max_e, 6) if max_e > 0 else 0}


def _seed_neo4j(driver):
    kb, relations = _get_knowledge_base()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        for lbl in ['Crop', 'Disease', 'Symptom', 'Cause', 'Treatment', 'Chemical', 'Prevention', 'Severity', 'RiskLevel']:
            try:
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{lbl}) REQUIRE n.name IS UNIQUE")
            except Exception:
                pass
        cache = {}

        def _en(lbl: str, name: str, detail: str = ''):
            key = f"{lbl}:{name}"
            if key in cache:
                return cache[key]
            r = session.run(f"MERGE (n:{lbl} {{name: $name}}) SET n.detail = $detail RETURN elementId(n)",
                            name=name, detail=detail[:500])
            nid = r.single()[0]
            cache[key] = nid
            return nid

        for key, entry in kb.items():
            parts = key.split('_')
            crop, dname = (parts[0], entry.get('disease_name', key))
            cid, did = _en('Crop', crop), _en('Disease', dname, entry.get('diagnosis_summary', ''))
            session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:BELONGS_TO]->(b)", a=did, b=cid)
            sev, risk = entry.get('severity', ''), entry.get('risk_level', '')
            if sev:
                nid = _en('Severity', sev[:100])
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:HAS_SEVERITY]->(b)", a=did, b=nid)
            if risk:
                nid = _en('RiskLevel', risk)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:HAS_RISK]->(b)", a=did, b=nid)
            for sym in entry.get('symptoms', []):
                nid = _en('Symptom', sym[:100], sym)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:HAS_SYMPTOM]->(b)", a=did, b=nid)
            for cause in entry.get('causes', []):
                nid = _en('Cause', cause[:100], cause)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:CAUSED_BY]->(b)", a=did, b=nid)
            for treat in entry.get('treatment_plan', []):
                nid = _en('Treatment', treat[:100], treat)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:TREATED_BY]->(b)", a=did, b=nid)
            for chem in entry.get('recommended_chemicals', []):
                cn = chem.get('name', str(chem)) if isinstance(chem, dict) else str(chem)
                nid = _en('Chemical', cn)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:USES_CHEMICAL]->(b)", a=did, b=nid)
            for prev in entry.get('cultivation_measures', []):
                nid = _en('Prevention', prev[:100], prev)
                session.run("MATCH (a) WHERE elementId(a)=$a MATCH (b) WHERE elementId(b)=$b MERGE (a)-[:PREVENTED_BY]->(b)", a=did, b=nid)

        for s_key, rd in relations.items():
            if s_key not in kb: continue
            sn = kb[s_key].get('disease_name', s_key)
            for t_key in rd.get('related_diseases', []):
                if t_key not in kb: continue
                tn = kb[t_key].get('disease_name', t_key)
                session.run("MATCH (a:Disease {name: $s}) MATCH (b:Disease {name: $t}) MERGE (a)-[:SIMILAR_TO]->(b)", s=sn, t=tn)


def _query_neo4j_graph(driver) -> Dict:
    with driver.session() as session:
        nodes_rec = session.run("MATCH (n) RETURN id(n) AS nid, labels(n) AS lbls, n.name AS name, n.detail AS detail")
        cat_map = {'Crop': 'crop', 'Disease': 'disease', 'Symptom': 'symptom', 'Cause': 'cause',
                   'Treatment': 'treatment', 'Chemical': 'chemical', 'Prevention': 'prevention',
                   'Severity': 'severity', 'RiskLevel': 'risk_level'}
        nodes, id_map = [], {}
        for r in nodes_rec:
            cat = 'unknown'
            for l in r['lbls']:
                if l in cat_map: cat = cat_map[l]; break
            n = {'id': r['nid'], 'name': r['name'] or '', 'category': cat, 'detail': (r['detail'] or '')[:200]}
            nodes.append(n)
            id_map[r['nid']] = n
        rel_map = {'BELONGS_TO': '属于', 'CAUSED_BY': '成因', 'HAS_SYMPTOM': '症状', 'TREATED_BY': '治疗方法',
                   'PREVENTED_BY': '预防措施', 'SIMILAR_TO': '相似病害', 'USES_CHEMICAL': '推荐药剂',
                   'HAS_SEVERITY': '严重程度', 'HAS_RISK': '风险等级'}
        edges_rec = session.run("MATCH (a)-[r]->(b) RETURN id(a) AS s, id(b) AS t, type(r) AS tpe")
        edges = [{'source': r['s'], 'target': r['t'], 'label': rel_map.get(r['tpe'], r['tpe'])} for r in edges_rec]
        return {'nodes': nodes, 'links': edges}


_memory_graph = None


def _get_graph() -> Dict:
    driver = _get_neo4j_driver()
    if driver:
        try:
            return _query_neo4j_graph(driver)
        except Exception as e:
            logger.warning(f"Neo4j 查询失败，回退内存: {e}")
    global _memory_graph
    if _memory_graph is None:
        _memory_graph = _build_memory_graph()
    return _memory_graph


def _bfs_path(graph, source_id: int, target_id: int) -> Optional[List]:
    adj, nm = defaultdict(list), {}
    for n in graph.get('nodes', []):
        nm[n['id']] = n
    for e in graph.get('links', []):
        adj[e['source']].append((e['target'], e.get('label', '')))
        adj[e['target']].append((e['source'], e.get('label', '')))
    if source_id not in nm or target_id not in nm:
        return None
    visited, q = {source_id}, deque()
    q.append((source_id, [dict(nm[source_id], relation='start')]))
    while q:
        cur, path = q.popleft()
        if cur == target_id:
            return path
        for nb, rl in adj.get(cur, []):
            if nb not in visited:
                visited.add(nb)
                q.append((nb, path + [dict(nm[nb], relation=rl)]))
    return None


@router.get('')
def get_graph(current_user: User = Depends(get_current_user)):
    return {'success': True, 'data': _get_graph()}


@router.get('/stats')
def get_graph_stats(current_user: User = Depends(get_current_user)):
    return {'success': True, 'data': _compute_stats(_get_graph())}


@router.get('/search')
def search_graph(q: str = Query(..., min_length=1, max_length=100), current_user: User = Depends(get_current_user)):
    query = q.lower().strip()
    results = []
    for node in _get_graph().get('nodes', []):
        if query in node.get('name', '').lower() or query in node.get('detail', '').lower()[:50]:
            results.append({'id': node['id'], 'name': node['name'], 'category': node.get('category', 'unknown')})
    return {'success': True, 'data': results[:50]}


@router.get('/path')
def find_path(source: int = Query(...), target: int = Query(...), current_user: User = Depends(get_current_user)):
    path = _bfs_path(_get_graph(), source, target)
    return {'success': True, 'data': {'found': path is not None, 'path': path or []}}


@router.post('/rebuild')
def rebuild_graph(current_user: User = Depends(get_current_user)):
    driver = _get_neo4j_driver()
    if driver:
        try:
            _seed_neo4j(driver)
            return {'success': True, 'message': 'Neo4j 知识图谱重建完成'}
        except Exception as e:
            logger.error(f"Neo4j 重建失败: {e}")
    global _memory_graph
    _memory_graph = None
    _get_graph()
    return {'success': True, 'message': '内存知识图谱重建完成'}
