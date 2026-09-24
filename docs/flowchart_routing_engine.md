# 플로우차트 라우팅 엔진 기술 문서
> **최종 업데이트**: 2026-09-23  
> **대상 파일**: `manual_capture_studio.py` (20,117줄)  
> **관련 클래스**: `MermaidFlowchartParser`, `MermaidLayoutEngine`, `FlowchartRoutingEngine`

---

## 1. 파이프라인 전체 흐름

```
[사용자 입력: Mermaid 스크립트]
        ↓
MermaidFlowchartParser.parse()
  → { nodes, edges, direction }
        ↓
MermaidLayoutEngine.build_flowchart()
  → 노드 배치(x,y) + port_usage_map 관리
  → FlowchartRoutingEngine.find_optimal_connector() 호출 (간선별)
        ↓
FlowchartRoutingEngine.find_optimal_connector()
  → 4×4 = 16개 포트 조합 순회
  → 각 조합에 대해 calculate_optimal_route() 호출
  → 비용 최소 조합 선택
        ↓
FlowchartRoutingEngine.calculate_optimal_route()
  → STRAIGHT / HV / VH / VHV / HVH / HVHV / VHVH 후보 생성
  → 장애물 회피 채널(per-obstacle + global) 포함
  → 비용 최소 경로 반환
        ↓
[캔버스에 FlowchartNodeItem + ElbowArrowItem 배치]
```

---

## 2. Mermaid 파서 (`MermaidFlowchartParser`)

### 지원 노드 형식
| Mermaid 문법 | shape_type | 설명 |
|---|---|---|
| `A[텍스트]` | `process` | 직사각형 |
| `A(텍스트)` | `terminal` | 둥근 직사각형(알약) |
| `A{텍스트}` | `decision` | 다이아몬드 |
| `A[(텍스트)]` | `database` | 원통 |
| `A[/텍스트/]` | `io` | 평행사변형 |
| `A([텍스트])` | `terminal` | 타원 |

### 지원 간선 문법
```
A --> B          # 레이블 없음
A -->|레이블| B   # 레이블 있음 (분기 조건 표시)
A --- B          # 화살표 없는 연결
```

### 파서 출력 구조
```python
{
  "direction": "TD" | "LR",
  "nodes": {
    "node_id": {
      "text": "표시 텍스트",
      "shape": "process" | "terminal" | "decision" | "database" | "io"
    }
  },
  "edges": [
    { "from": "A", "to": "B", "label": "조건" }
  ]
}
```

---

## 3. 레이아웃 엔진 (`MermaidLayoutEngine`)

### 계층 배치 알고리즘
1. **DFS로 back_edges 탐지** (순환 방지)
2. **위상 정렬 기반 rank 계산** (back_edges 제외)
3. **같은 rank 내 중앙 정렬**

### 간격 기준
| 방향 | x_step | y_step |
|---|---|---|
| TD (상→하) | node_w + 30px | node_h + 50px |
| LR (좌→우) | node_w + 60px | node_h + 28px |

기본값: `node_w=75, node_h=32`

### port_usage_map 구조
```python
port_usage_map[node_item] = {
    "in":  set(),  # 이 노드로 들어오는 화살표가 사용한 포트 집합
    "out": set()   # 이 노드에서 나가는 화살표가 사용한 포트 집합
}
```

간선 처리 순서: `sp → item_u["out"]`, `dp → item_v["in"]` 순으로 기록

### routed_segments
이미 그려진 모든 경로 선분 `(p1, p2)` 리스트.  
후속 간선의 `count_collisions()` 에서 선 교차 비용 계산에 활용.

---

## 4. 라우팅 엔진 (`FlowchartRoutingEngine`)

### 4.1 핵심 설계 원칙
> **"16개 포트 조합(4×4)을 전부 계산하고, 충돌·포트중복이 없는 것 중 실제 경로 길이가 가장 짧은 것을 선택한다."**

- `dir_penalty` 없음 (2026-09-23 제거): 방향 기반 패널티는 중복이며 오히려 더 짧은 경로를 탈락시키는 원인이었음
- `lane_offset` 고정 0.0 (2026-09-23 제거): `hash(id())` 기반으로 비결정적 동작의 원인이었음
- `dynamic_gap_mode` 없음 (2026-09-23 제거): 장애물 0개 시 간격 0pt 문제. 고정 24pt만 사용

### 4.2 비용 함수 (최종)

```python
cost = (node_hits     * 1_000_000.0)   # 노드 관통 → 절대 배제
     + (line_crossings * 500.0)         # 기존 선과 교차 → 강하게 회피
     + occupancy_penalty                # 포트 중복 → 절대 배제
     + (bends          * 400.0)         # 꺾임 수 → 단순한 경로 선호
     + (path_len       * 1.0)           # 실제 경로 길이 → 최종 결정자
```

### 4.3 occupancy_penalty 기준
| 상황 | 페널티 |
|---|---|
| 출발 포트가 이미 동일 방향 OUT으로 사용 중 | +2,000,000 |
| 출발 포트에 이미 IN이 있음 (역주행) | +1,000,000 |
| 도착 포트가 이미 동일 방향 IN으로 사용 중 | +2,000,000 |
| 도착 포트에 이미 OUT이 있음 (역주행) | +1,000,000 |

### 4.4 포트 순위 목록 (탐색 순서)

`find_optimal_connector` 내부에서 비용 계산 전에 src/dst 포트를 방향에 따라 정렬:

| 조건 | src_ports | dst_ports |
|---|---|---|
| 거의 수직(dx≤18) + 아래 | `[bottom, right, left, top]` | `[top, left, right, bottom]` |
| 거의 수직(dx≤18) + 위 | `[top, right, left, bottom]` | `[bottom, left, right, top]` |
| 거의 수평(dy≤18) + 오른쪽 | `[right, bottom, top, left]` | `[left, top, bottom, right]` |
| 거의 수평(dy≤18) + 왼쪽 | `[left, bottom, top, right]` | `[right, top, bottom, left]` |
| 수직 우세(dy≥dx) + 아래 | `[bottom, top, right, left]` | `[top, bottom, left, right]` |
| 수직 우세(dy≥dx) + 위 | `[top, bottom, right, left]` | `[bottom, top, left, right]` |
| 수평 우세(dx>dy) + 오른쪽 | `[right, left, bottom, top]` | `[left, right, top, bottom]` |
| 수평 우세(dx>dy) + 왼쪽 | `[left, right, bottom, top]` | `[right, left, top, bottom]` |

**포트 정렬은 탐색 순서만 결정**하며, 비용 함수로 실제 선택이 이루어짐.  
동일 비용이면 먼저 탐색된 포트가 선택됨.

### 4.5 `calculate_optimal_route` 경로 후보 종류

| 모드 | 꺾임 수 | 설명 |
|---|---|---|
| `STRAIGHT` | 0 | 완전한 직선 (수직/수평 축 일치 시) |
| `HV` | 1 | 수평 → 수직 L자 |
| `VH` | 1 | 수직 → 수평 L자 |
| `VHV` | 2 | 수직 → 수평 → 수직 (C자형) |
| `HVH` | 2 | 수평 → 수직 → 수평 (Z자형) |
| `HVHV` | 3 | 글로벌 우회 채널 |
| `VHVH` | 3 | 글로벌 우회 채널 |

### 4.6 글로벌 우회 채널 (최후 수단)
- 모든 노드의 외곽 바운딩 박스 계산 후 고정 **+24pt** 여백 추가
- 토폴로지 데드락(어떤 경로도 충돌 없이 연결 불가)에서만 발동
- 공식: `safe_margin = margin(14pt) + 24pt = 38pt`

---

## 5. 결정론적 동작 보장

### 제거된 비결정적 요소
```python
# ❌ 제거됨 (2026-09-23)
lane_offset = (hash((id(src_node), id(dst_node))) % 5) * 8.0
# 이유: id()는 매번 다른 메모리 주소, hash()는 PYTHONHASHSEED 랜덤으로
#       동일 스크립트도 실행마다 다른 결과를 냄
```

### 현재 상태
- 동일한 Mermaid 스크립트 → 항상 동일한 라우팅 결과 ✅

---

## 6. Android 앱 (`MainScreen.kt`) 대응 표

| PC (Python) | Android (Kotlin) |
|---|---|
| `find_optimal_connector()` | `findOptimalPorts()` |
| `calculate_optimal_route()` | `buildRoutePts()` |
| `count_collisions()` | `countNodeHits()` + `segmentIntersectsRect()` |
| `port_usage_map` | `srcUsedOut`, `srcUsedIn`, `dstUsedIn`, `dstUsedOut` |
| `FlowchartNodeItem.get_magnet_points()` | `calculatePortOffset()` |
| `ElbowArrowItem` 드로잉 | `Canvas { drawPath() }` |

---

## 7. 주요 변경 이력

| 날짜 | 변경 내용 |
|---|---|
| 2026-09-23 | `dir_penalty × 50,000` 제거 → `path_len × 1.0` 강화 |
| 2026-09-23 | `lane_offset = hash(id()) % 5 * 8.0` → `0.0` 고정 (결정론 확보) |
| 2026-09-23 | `dynamic_gap_mode` + 체크박스 전체 제거 (고정 24pt 유지) |
| 2026-09-23 | `occupancy_penalty`: 동일 포트 중복 2,000,000 / 역주행 1,000,000 |
| 2026-09-23 | `count_collisions()` 반환 타입: `(node_hits, line_crossings)` 튜플 언패킹 수정 |
