---
name: manual-studio-routing
description: >-
  Manual Studio 플로우차트 라우팅 엔진(FlowchartRoutingEngine) 및 Mermaid 레이아웃 엔진(MermaidLayoutEngine) 
  설계 원칙, 비용 함수, 결정론 규칙, Android 포팅 대응표. 
  manual_capture_studio.py 의 플로우차트 기능 수정 시 반드시 참조.
---

# Manual Studio — 플로우차트 라우팅 엔진 설계 원칙

## ⚠️ 절대 규칙 (변경 금지)

### 1. 비결정적 요소 사용 금지
```python
# ❌ 절대 사용 금지
lane_offset = (hash((id(src_node), id(dst_node))) % 5) * 8.0
# 이유: id() = 매번 다른 메모리 주소, hash() = PYTHONHASHSEED 랜덤
#       → 동일 스크립트도 실행마다 다른 라우팅 결과
```
동일한 Mermaid 스크립트는 항상 동일한 라우팅 결과를 내야 한다.  
`lane_offset = 0.0` 고정 유지.

### 2. 비용 함수 구조 (확정)
```python
cost = (node_hits      * 1_000_000.0)   # 노드 관통 → 절대 배제
     + (line_crossings * 500.0)          # 선 교차 → 강하게 회피
     + occupancy_penalty                 # 포트 중복 → 절대 배제
     + (bends          * 400.0)          # 꺾임 수 → 단순 경로 선호
     + (path_len       * 1.0)            # 실제 거리 → 최종 결정자
```
- `dir_penalty` 없음: 중복 패널티로 더 짧은 경로를 탈락시키는 원인이었음. 영구 제거.
- `path_len` 가중치 = `1.0` (이전 `0.05`는 너무 약해서 역할 불가했음)

### 3. 포트 조합은 16개 전부 탐색
4 src_ports × 4 dst_ports = 16조합 모두 `calculate_optimal_route()`로 계산.  
방향 힌트는 `src_ports/dst_ports` 리스트 순서만으로 처리 (페널티 아님).

### 4. occupancy_penalty 기준
| 상황 | 페널티 |
|---|---|
| 출발 포트 동일 방향 OUT 중복 | 2,000,000 |
| 출발 포트 역주행 (IN에 OUT 연결) | 1,000,000 |
| 도착 포트 동일 방향 IN 중복 | 2,000,000 |
| 도착 포트 역주행 (OUT에 IN 연결) | 1,000,000 |

### 5. 글로벌 우회 채널 이격 = 고정 24pt
```python
dynamic_gap = 24.0  # 고정. 장애물 수에 무관.
safe_margin = margin(14pt) + 24pt = 38pt
```
`obs_count * 24pt` 공식 금지: 장애물 0개 시 간격 0pt 문제 발생.

---

## 함수 체인 (파라미터 추가 시 4단계 모두 업데이트 필수)

```
on_insert_clicked()
    ↓ 파라미터 전달
MermaidLayoutEngine.build_flowchart()
    ↓
FlowchartRoutingEngine.find_optimal_connector()
    ↓
FlowchartRoutingEngine.calculate_optimal_route()
```

---

## count_collisions 반환 타입

```python
# 반드시 튜플 언패킹
node_hits, line_crossings = FlowchartRoutingEngine.count_collisions(...)
# 단일 변수 할당 금지: hits * 1000000.0 → TypeError
```

---

## port_usage_map 구조

```python
port_usage_map[node_item] = {"in": set(), "out": set()}
# 간선 처리 후: sp → item_u["out"], dp → item_v["in"] 순으로 기록
```

---

## Android Kotlin 대응 (`MainScreen.kt`)

| PC Python | Android Kotlin |
|---|---|
| `find_optimal_connector()` | `findOptimalPorts()` |
| `calculate_optimal_route()` | `buildRoutePts()` |
| `count_collisions()` | `countNodeHits()` + `segmentIntersectsRect()` |
| `port_usage_map` | `srcUsedOut/In`, `dstUsedIn/Out` |
| `get_magnet_points()` | `calculatePortOffset()` |

동일한 비용 공식을 Kotlin으로 구현:
```kotlin
val cost = nodeHits * 1_000_000f + occupancyPenalty + bends * 400f + pathLen
```

---

## 상세 문서 위치
`d:\01.AntiGravity\999.매뉴얼제작\docs\flowchart_routing_engine.md`
