package com.example.manualstudiomobile.ui.main

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.provider.MediaStore
import android.util.Base64
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.navigation3.runtime.NavKey
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * ISO 5807 표준 플로우차트 기호 정의
 */
enum class NodeShape(val label: String, val bgColor: Color, val borderColor: Color) {
    TERMINAL("시작/종료", Color(0xFFECFDF5), Color(0xFF059669)),    // 타원/알약
    PROCESS("일반 작업", Color(0xFFEFF6FF), Color(0xFF2563EB)),     // 직사각형
    DECISION("조건 분기", Color(0xFFFFFBEB), Color(0xFFD97706)),    // 마름모 (다이아몬드)
    IO("데이터 입출력", Color(0xFFF0FDF4), Color(0xFF16A34A)),      // 평행사변형
    DATABASE("데이터베이스", Color(0xFFFAF5FF), Color(0xFF7C3AED)),  // 원통 실린더
    DOCUMENT("문서 서식", Color(0xFFEEF2FF), Color(0xFF4F46E5))     // 하단 물결 문서
}

enum class PortPosition {
    TOP, BOTTOM, LEFT, RIGHT
}

data class FlowNode(
    val id: String,
    val text: String,
    val shape: NodeShape,
    val x: Float,
    val y: Float,
    val width: Float = 66f,
    val height: Float = 30f
)

data class FlowEdge(
    val id: String,
    val fromNodeId: String,
    val toNodeId: String,
    val fromPort: PortPosition = PortPosition.BOTTOM,
    val toPort: PortPosition = PortPosition.TOP,
    val label: String = ""
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ManualStudioPrefs", Context.MODE_PRIVATE) }

    // SharedPreferences 영속 데이터 불러오기 (최초 실행 시 완전 빈 캔버스)
    val savedData = remember { loadFlowchartFromPrefs(prefs) }

    var nodes by remember { mutableStateOf(savedData.first) }
    var edges by remember { mutableStateOf(savedData.second) }
    var direction by remember { mutableStateOf(prefs.getString("flow_direction", "TD") ?: "TD") }

    // 선택 상태 (노드 선택 vs 선 선택)
    var selectedNodeId by remember { mutableStateOf<String?>(null) }
    var selectedEdgeId by remember { mutableStateOf<String?>(null) }

    // 마그넷 포트 연결 모드 상태
    var connectMode by remember { mutableStateOf(false) }
    var connectStartNodeId by remember { mutableStateOf<String?>(null) }
    var connectStartPort by remember { mutableStateOf<PortPosition?>(null) }

    var editingNode by remember { mutableStateOf<FlowNode?>(null) }
    var showSendDialog by remember { mutableStateOf(false) }
    var lastCapturedBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var showPhotoDialog by remember { mutableStateOf(false) }

    // 전송 설정 (Wi-Fi 직접 vs 원격 중계)
    var sendMode by remember { mutableStateOf(prefs.getString("send_mode", "wifi") ?: "wifi") } // "wifi" or "cloud"
    var pcIp by remember { mutableStateOf(prefs.getString("pc_ip", "192.168.0.") ?: "192.168.0.") }
    var pcPin by remember { mutableStateOf(prefs.getString("pc_pin", "") ?: "") }
    var cloudServerUrl by remember { mutableStateOf(prefs.getString("cloud_relay_url", "https://pub-4bd1b65a7bcc4eef8993da27e7362727.r2.dev") ?: "https://pub-4bd1b65a7bcc4eef8993da27e7362727.r2.dev") }
    var isSending by remember { mutableStateOf(false) }

    // 변경사항 자동 저장
    fun persistState() {
        saveFlowchartToPrefs(prefs, nodes, edges, direction)
    }

    // 카메라 직접 촬영 런처
    val directCameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            val bitmap = result.data?.extras?.get("data") as? Bitmap
            if (bitmap != null) {
                lastCapturedBitmap = bitmap
                showPhotoDialog = true
            }
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            directCameraLauncher.launch(intent)
        } else {
            Toast.makeText(context, "카메라 권한이 필요합니다.", Toast.LENGTH_SHORT).show()
        }
    }

    fun launchCamera() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            directCameraLauncher.launch(intent)
        } else {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    // 두 노드 간 지능형 연결 함수 (기존 연결선 자동 교체 및 최적 포트 자동 계산)
    fun connectNodesSmart(fromId: String, toId: String, manualFromPort: PortPosition? = null, manualToPort: PortPosition? = null) {
        if (fromId == toId) return

        val nodeMap = nodes.associateBy { it.id }
        val fromNode = nodeMap[fromId] ?: return
        val toNode = nodeMap[toId] ?: return

        val (bestFromPort, bestToPort) = if (manualFromPort != null && manualToPort != null) {
            Pair(manualFromPort, manualToPort)
        } else {
            findOptimalPorts(fromNode, toNode, nodes, edges)
        }

        // 기존에 두 노드 사이에 연결된 선이 있다면 제거 (재차 연결 시 마지막 선만 단일 유지)
        val filteredEdges = edges.filterNot {
            (it.fromNodeId == fromId && it.toNodeId == toId) || (it.fromNodeId == toId && it.toNodeId == fromId)
        }

        val newEdge = FlowEdge(
            id = "e_${System.currentTimeMillis()}",
            fromNodeId = fromId,
            toNodeId = toId,
            fromPort = manualFromPort ?: bestFromPort,
            toPort = manualToPort ?: bestToPort
        )

        edges = filteredEdges + newEdge
        selectedEdgeId = newEdge.id
        persistState()
        Toast.makeText(context, "✅ 연결선이 설정되었습니다 (기존 연결선 자동 정리)", Toast.LENGTH_SHORT).show()
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                modifier = Modifier.statusBarsPadding(),
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "매뉴얼 스튜디오 모바일",
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        if (connectMode) {
                            Surface(
                                color = Color(0xFFEF4444),
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    "연결 모드 ON",
                                    fontSize = 10.sp,
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0F172A)
                ),
                actions = {
                    // 1. 카메라 직접 촬영 버튼
                    IconButton(
                        onClick = { launchCamera() },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text("📷", fontSize = 16.sp)
                    }

                    // 2. 마그넷 연결 모드 토글
                    IconButton(
                        onClick = {
                            connectMode = !connectMode
                            connectStartNodeId = null
                            connectStartPort = null
                            val msg = if (connectMode) "연결 모드: 노드나 접점을 차례로 터치하세요" else "연결 모드 종료"
                            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text(if (connectMode) "🔗" else "⛓️", fontSize = 16.sp)
                    }

                    // 3. 자동정렬 (계층형 트리 재정렬, 실시간 리스트 재생성)
                    IconButton(
                        onClick = {
                            direction = if (direction == "TD") "LR" else "TD"
                            prefs.edit().putString("flow_direction", direction).apply()
                            nodes = autoAlignNodes(nodes, edges, direction)
                            persistState()
                            Toast.makeText(context, "⚡ 자동정렬 완료 (${if (direction == "TD") "상하 TD" else "좌우 LR"})", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text("⚡", fontSize = 16.sp)
                    }

                    // 4. PC 전송 버튼 (원터치 전송)
                    Button(
                        onClick = { showSendDialog = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                        modifier = Modifier
                            .height(30.dp)
                            .padding(end = 6.dp)
                    ) {
                        Text("PC 전송", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }
            )
        },
        bottomBar = {
            // 하단 팔레트 및 선택 조작 패널 (시스템 내비게이션 바 완벽 패딩)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF1E293B))
                    .navigationBarsPadding() // 세로/가로 모드 시 홈 버튼/제스처 바 겹침 완벽 차단
                    .padding(vertical = 4.dp)
            ) {
                // 선택된 노드나 선이 있을 때 나타나는 즉시 조작 액션 바
                if (selectedNodeId != null || selectedEdgeId != null) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 2.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = if (selectedNodeId != null) "선택된 노드: ${nodes.find { it.id == selectedNodeId }?.text}" else "선택된 연결선",
                            fontSize = 11.sp,
                            color = Color(0xFF93C5FD),
                            fontWeight = FontWeight.SemiBold
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            if (selectedNodeId != null) {
                                Button(
                                    onClick = {
                                        editingNode = nodes.find { it.id == selectedNodeId }
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3B82F6)),
                                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                                    modifier = Modifier.height(26.dp)
                                ) {
                                    Text("✏️ 수정", fontSize = 10.sp)
                                }
                            }
                            Button(
                                onClick = {
                                    if (selectedNodeId != null) {
                                        val delId = selectedNodeId
                                        nodes = nodes.filter { it.id != delId }
                                        edges = edges.filter { it.fromNodeId != delId && it.toNodeId != delId }
                                        selectedNodeId = null
                                        persistState()
                                        Toast.makeText(context, "노드가 삭제되었습니다.", Toast.LENGTH_SHORT).show()
                                    } else if (selectedEdgeId != null) {
                                        val delId = selectedEdgeId
                                        edges = edges.filter { it.id != delId }
                                        selectedEdgeId = null
                                        persistState()
                                        Toast.makeText(context, "연결선이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
                                    }
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                                modifier = Modifier.height(26.dp)
                            ) {
                                Text("🗑️ 삭제", fontSize = 10.sp, color = Color.White)
                            }
                            Button(
                                onClick = {
                                    selectedNodeId = null
                                    selectedEdgeId = null
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569)),
                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                                modifier = Modifier.height(26.dp)
                            ) {
                                Text("선택 해제", fontSize = 10.sp)
                            }
                        }
                    }
                    Divider(color = Color(0xFF334155), thickness = 0.5.dp, modifier = Modifier.padding(vertical = 2.dp))
                }

                // 하단 다이어그램 도형 추가 버튼군 (컴팩트 마이크로 버튼)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(5.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    NodeShape.values().forEach { shape ->
                        Button(
                            onClick = {
                                val (nextX, nextY) = findNextSmartPosition(nodes, direction)
                                val newNodeId = "n_${System.currentTimeMillis()}"
                                val newNode = FlowNode(
                                    id = newNodeId,
                                    text = shape.label,
                                    shape = shape,
                                    x = nextX,
                                    y = nextY,
                                    width = 66f,
                                    height = 30f
                                )

                                // 이전 노드가 있다면 자동으로 자연스럽게 연결
                                val newEdges = if (nodes.isNotEmpty()) {
                                    val prev = nodes.last()
                                    val (fPort, tPort) = findOptimalPorts(prev, newNode, nodes, edges)
                                    edges + FlowEdge(
                                        id = "e_${System.currentTimeMillis()}",
                                        fromNodeId = prev.id,
                                        toNodeId = newNodeId,
                                        fromPort = fPort,
                                        toPort = tPort
                                    )
                                } else edges

                                nodes = nodes + newNode
                                edges = newEdges
                                selectedNodeId = newNodeId
                                selectedEdgeId = null
                                persistState()
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = shape.bgColor,
                                contentColor = Color(0xFF1E293B)
                            ),
                            shape = RoundedCornerShape(5.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, shape.borderColor),
                            contentPadding = PaddingValues(horizontal = 7.dp, vertical = 3.dp),
                            modifier = Modifier.height(28.dp)
                        ) {
                            Text(shape.label, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }

                    // 캔버스 전체 초기화 버튼
                    Button(
                        onClick = {
                            nodes = emptyList()
                            edges = emptyList()
                            selectedNodeId = null
                            selectedEdgeId = null
                            persistState()
                            Toast.makeText(context, "캔버스가 초기화되었습니다.", Toast.LENGTH_SHORT).show()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                        shape = RoundedCornerShape(5.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 3.dp),
                        modifier = Modifier.height(28.dp)
                    ) {
                        Text("전체 삭제", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Color(0xFF0B1120))
                .clickable {
                    // 배경 터치 시 선택 해제
                    selectedNodeId = null
                    selectedEdgeId = null
                    connectStartNodeId = null
                    connectStartPort = null
                }
        ) {
            // 1. 커스텀 연결선(FlowEdge) 렌더링 캔버스 (노드 드래그 시 실시간 마그넷 추종)
            Canvas(modifier = Modifier.fillMaxSize()) {
                val nodeMap = nodes.associateBy { it.id }

                edges.forEach { edge ->
                    val fromNode = nodeMap[edge.fromNodeId]
                    val toNode = nodeMap[edge.toNodeId]

                    if (fromNode != null && toNode != null) {
                        val isEdgeSelected = (selectedEdgeId == edge.id)
                        val edgeColor = if (isEdgeSelected) Color(0xFFF59E0B) else Color(0xFF60A5FA)
                        val strokeW = if (isEdgeSelected) 5.5f else 3.5f

                        val start = calculatePortOffset(fromNode, edge.fromPort)
                        val end = calculatePortOffset(toNode, edge.toPort)

                        val path = Path().apply {
                            val pts = buildRoutePts(start, end, edge.fromPort, edge.toPort)
                            moveTo(pts.first().x, pts.first().y)
                            for (pt in pts.drop(1)) lineTo(pt.x, pt.y)
                        }

                        drawPath(path = path, color = edgeColor, style = Stroke(width = strokeW))
                        drawArrowHead(endOffset = end, port = edge.toPort, color = edgeColor)
                    }
                }
            }

            // 2. 연결선 선택을 위한 미니 터치 인터랙터 오버레이
            val nodeMap = nodes.associateBy { it.id }
            edges.forEach { edge ->
                val fromNode = nodeMap[edge.fromNodeId]
                val toNode = nodeMap[edge.toNodeId]
                if (fromNode != null && toNode != null) {
                    val s = calculatePortOffset(fromNode, edge.fromPort)
                    val e = calculatePortOffset(toNode, edge.toPort)
                    val midX = (s.x + e.x) / 2
                    val midY = (s.y + e.y) / 2
                    val isEdgeSelected = (selectedEdgeId == edge.id)

                    Box(
                        modifier = Modifier
                            .offset { IntOffset((midX - 10).roundToInt(), (midY - 10).roundToInt()) }
                            .size(20.dp)
                            .clip(CircleShape)
                            .background(if (isEdgeSelected) Color(0xFFF59E0B) else Color(0x3360A5FA))
                            .border(1.dp, if (isEdgeSelected) Color.White else Color(0x8860A5FA), CircleShape)
                            .clickable {
                                selectedEdgeId = edge.id
                                selectedNodeId = null
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text("✕", fontSize = 9.sp, color = if (isEdgeSelected) Color.White else Color(0xFF93C5FD))
                    }
                }
            }

            // 3. ISO 표준 플로우차트 노드 및 4개 마그넷 접점 렌더링
            nodes.forEach { node ->
                key(node.id) {
                    IsoNodeView(
                        node = node,
                        isSelected = selectedNodeId == node.id,
                        isConnectMode = connectMode,
                        selectedPortPos = if (connectStartNodeId == node.id) connectStartPort else null,
                        onPositionChanged = { dx, dy ->
                            // 노드 좌표를 실시간 리스트 갱신하여 Canvas의 연결선이 즉시 마그넷처럼 따라오도록 보장
                            nodes = nodes.map {
                                if (it.id == node.id) it.copy(x = it.x + dx, y = it.y + dy) else it
                            }
                        },
                        onDragEnd = {
                            persistState()
                        },
                        onNodeClick = {
                            if (connectMode) {
                                if (connectStartNodeId == null) {
                                    connectStartNodeId = node.id
                                    Toast.makeText(context, "시작 노드 선택됨: 연결할 대상 노드를 터치하세요", Toast.LENGTH_SHORT).show()
                                } else {
                                    connectNodesSmart(connectStartNodeId!!, node.id)
                                    connectStartNodeId = null
                                    connectStartPort = null
                                }
                            } else {
                                selectedNodeId = node.id
                                selectedEdgeId = null
                            }
                        },
                        onPortClick = { port ->
                            if (!connectMode) {
                                connectMode = true
                            }
                            if (connectStartNodeId == null) {
                                connectStartNodeId = node.id
                                connectStartPort = port
                                Toast.makeText(context, "시작 접점 선택됨: 대상 노드의 접점을 터치하세요", Toast.LENGTH_SHORT).show()
                            } else {
                                connectNodesSmart(connectStartNodeId!!, node.id, connectStartPort, port)
                                connectStartNodeId = null
                                connectStartPort = null
                            }
                        }
                    )
                }
            }
        }
    }

    // 1. 노드 텍스트 편집 다이얼로그
    editingNode?.let { node ->
        var editText by remember { mutableStateOf(node.text) }
        AlertDialog(
            onDismissRequest = { editingNode = null },
            title = { Text("노드 내용 편집", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("도형 유형: ${node.shape.label}", fontSize = 12.sp, color = Color.Gray)
                    OutlinedTextField(
                        value = editText,
                        onValueChange = { editText = it },
                        label = { Text("표시할 텍스트") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    nodes = nodes.map { if (it.id == node.id) it.copy(text = editText) else it }
                    editingNode = null
                    persistState()
                }) {
                    Text("확인")
                }
            },
            dismissButton = {
                TextButton(onClick = { editingNode = null }) {
                    Text("취소")
                }
            }
        )
    }

    // 2. PC 전송 다이얼로그 (🌐 원격/외부망 전송 vs 📶 사내 Wi-Fi 고속 전송 2트랙 완벽 지원)
    if (showSendDialog) {
        AlertDialog(
            onDismissRequest = { showSendDialog = false },
            title = { Text("PC 매뉴얼 스튜디오로 전송", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    // 전송 모드 탭 선택 (🌐 원격지 vs 📶 Wi-Fi)
                    TabRow(selectedTabIndex = if (sendMode == "wifi") 0 else 1) {
                        Tab(
                            selected = sendMode == "wifi",
                            onClick = {
                                sendMode = "wifi"
                                prefs.edit().putString("send_mode", "wifi").apply()
                            },
                            text = { Text("📶 사내 Wi-Fi") }
                        )
                        Tab(
                            selected = sendMode == "cloud",
                            onClick = {
                                sendMode = "cloud"
                                prefs.edit().putString("send_mode", "cloud").apply()
                            },
                            text = { Text("🌐 원격/LTE 어디서나") }
                        )
                    }

                    if (sendMode == "wifi") {
                        Text("같은 공유기(Wi-Fi)에 연결된 PC로 직접 초고속 전송합니다.", fontSize = 12.sp, color = Color.Gray)
                        OutlinedTextField(
                            value = pcIp,
                            onValueChange = {
                                pcIp = it
                                prefs.edit().putString("pc_ip", it).apply()
                            },
                            label = { Text("PC IP 주소 (예: 192.168.0.25)") },
                            modifier = Modifier.fillMaxWidth()
                        )
                    } else {
                        Text("외부 LTE/5G나 다른 네트워크에서도 PIN 번호만으로 원격 전송합니다.", fontSize = 12.sp, color = Color.Gray)
                        OutlinedTextField(
                            value = cloudServerUrl,
                            onValueChange = {
                                cloudServerUrl = it
                                prefs.edit().putString("cloud_relay_url", it).apply()
                            },
                            label = { Text("원격 릴레이 서버 URL") },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    OutlinedTextField(
                        value = pcPin,
                        onValueChange = {
                            pcPin = it
                            prefs.edit().putString("pc_pin", it).apply()
                        },
                        label = { Text("PC 화면 6자리 PIN (예: 376-310)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        isSending = true
                        CoroutineScope(Dispatchers.IO).launch {
                            val success = if (sendMode == "wifi") {
                                sendDiagramToPc(pcIp, pcPin, nodes, edges, direction)
                            } else {
                                sendDiagramViaCloud(cloudServerUrl, pcPin, nodes, edges, direction)
                            }
                            withContext(Dispatchers.Main) {
                                isSending = false
                                if (success) {
                                    Toast.makeText(context, "🎉 PC 매뉴얼 스튜디오로 전송 성공!", Toast.LENGTH_LONG).show()
                                    showSendDialog = false
                                } else {
                                    val err = if (sendMode == "wifi") "Wi-Fi 연결 실패: IP와 PIN 번호를 확인하세요." else "원격 전송 실패: PIN 번호를 확인하세요."
                                    Toast.makeText(context, err, Toast.LENGTH_LONG).show()
                                }
                            }
                        }
                    },
                    enabled = !isSending
                ) {
                    Text(if (isSending) "전송 중..." else "즉시 전송")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSendDialog = false }) {
                    Text("취소")
                }
            }
        )
    }

    // 3. 직접 촬영 사진 전송 다이얼로그
    if (showPhotoDialog && lastCapturedBitmap != null) {
        AlertDialog(
            onDismissRequest = { showPhotoDialog = false },
            title = { Text("📷 손그림 사진 PC 전송", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("직접 촬영한 손그림/화이트보드 사진을 PC로 즉시 전송하시겠습니까?", fontSize = 12.sp)
                    if (sendMode == "wifi") {
                        OutlinedTextField(
                            value = pcIp,
                            onValueChange = { pcIp = it },
                            label = { Text("PC IP 주소") },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                    OutlinedTextField(
                        value = pcPin,
                        onValueChange = { pcPin = it },
                        label = { Text("6자리 PIN") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        CoroutineScope(Dispatchers.IO).launch {
                            val targetHost = if (sendMode == "wifi") pcIp else cloudServerUrl
                            val success = sendPhotoToPc(targetHost, pcPin, lastCapturedBitmap!!)
                            withContext(Dispatchers.Main) {
                                if (success) {
                                    Toast.makeText(context, "📷 손그림 사진 PC 전송 완료!", Toast.LENGTH_LONG).show()
                                    showPhotoDialog = false
                                } else {
                                    Toast.makeText(context, "전송 실패: 네트워크 및 PIN을 확인하세요.", Toast.LENGTH_LONG).show()
                                }
                            }
                        }
                    }
                ) {
                    Text("PC로 전송")
                }
            },
            dismissButton = {
                TextButton(onClick = { showPhotoDialog = false }) {
                    Text("취소")
                }
            }
        )
    }
}

/**
 * PC 버전과 동일한 비용 기반 16개 포트 조합 평가로 최적 마그넷 포트 자동 판정
 * 4 src_ports × 4 dst_ports = 16 조합을 모두 평가하여 최소 비용 포트 쌍 반환
 */
fun findOptimalPorts(
    from: FlowNode,
    to: FlowNode,
    allNodes: List<FlowNode>,
    existingEdges: List<FlowEdge>
): Pair<PortPosition, PortPosition> {
    val srcPorts = listOf(PortPosition.TOP, PortPosition.BOTTOM, PortPosition.LEFT, PortPosition.RIGHT)
    val dstPorts = listOf(PortPosition.TOP, PortPosition.BOTTOM, PortPosition.LEFT, PortPosition.RIGHT)

    // 현재 포트 사용 현황 집계
    val srcUsedOut = mutableSetOf<PortPosition>()
    val srcUsedIn = mutableSetOf<PortPosition>()
    val dstUsedIn = mutableSetOf<PortPosition>()
    val dstUsedOut = mutableSetOf<PortPosition>()
    for (e in existingEdges) {
        if (e.fromNodeId == from.id) srcUsedOut.add(e.fromPort)
        if (e.toNodeId == from.id) srcUsedIn.add(e.toPort)
        if (e.toNodeId == to.id) dstUsedIn.add(e.toPort)
        if (e.fromNodeId == to.id) dstUsedOut.add(e.fromPort)
    }

    // 장애물 목록 (src, dst 제외)
    val obstacles = allNodes.filter { it.id != from.id && it.id != to.id }

    var bestSp = PortPosition.BOTTOM
    var bestDp = PortPosition.TOP
    var minCost = Float.MAX_VALUE

    for (sp in srcPorts) {
        for (dp in dstPorts) {
            val start = calculatePortOffset(from, sp)
            val end = calculatePortOffset(to, dp)

            // 포트 점유 페널티
            var occupancyPenalty = 0f
            if (sp in srcUsedOut) occupancyPenalty += 2_000_000f
            if (sp in srcUsedIn)  occupancyPenalty += 1_000_000f
            if (dp in dstUsedIn)  occupancyPenalty += 2_000_000f
            if (dp in dstUsedOut) occupancyPenalty += 1_000_000f

            // 경로 포인트 계산
            val pts = buildRoutePts(start, end, sp, dp)

            // 충돌 페널티
            val nodeHits = countNodeHits(pts, obstacles)

            // 경로 길이
            val pathLen = calcPathLen(pts)

            // 꺾임 수 (중간 점 개수)
            val bends = pts.size - 2

            val cost = nodeHits * 1_000_000f + occupancyPenalty + bends * 400f + pathLen

            if (cost < minCost) {
                minCost = cost
                bestSp = sp
                bestDp = dp
            }
        }
    }
    return Pair(bestSp, bestDp)
}

/**
 * 두 포트 간 경로 점들을 반환 (출발, 중간 꺾임들, 도착)
 * 수직 포트(TOP/BOTTOM) → VH, 수평 포트(LEFT/RIGHT) → HV
 */
fun buildRoutePts(start: Offset, end: Offset, sp: PortPosition, dp: PortPosition): List<Offset> {
    // 직선 가능 여부 확인
    if (abs(start.x - end.x) < 4f && sp == PortPosition.TOP && dp == PortPosition.BOTTOM) {
        return listOf(start, end)
    }
    if (abs(start.y - end.y) < 4f && sp == PortPosition.LEFT && dp == PortPosition.RIGHT) {
        return listOf(start, end)
    }
    return if (sp == PortPosition.TOP || sp == PortPosition.BOTTOM) {
        // VH: 수직 먼저 → 수평
        val midY = (start.y + end.y) / 2f
        listOf(start, Offset(start.x, midY), Offset(end.x, midY), end)
    } else {
        // HV: 수평 먼저 → 수직
        val midX = (start.x + end.x) / 2f
        listOf(start, Offset(midX, start.y), Offset(midX, end.y), end)
    }
}

/**
 * 경로 선분들이 장애물 노드 박스를 관통하는 횟수 계산
 */
fun countNodeHits(pts: List<Offset>, obstacles: List<FlowNode>): Int {
    var hits = 0
    for (i in 0 until pts.size - 1) {
        val p1 = pts[i]; val p2 = pts[i + 1]
        for (obs in obstacles) {
            val left = obs.x - 4f; val right = obs.x + obs.width + 4f
            val top = obs.y - 4f; val bot = obs.y + obs.height + 4f
            if (segmentIntersectsRect(p1, p2, left, top, right, bot)) hits++
        }
    }
    return hits
}

/**
 * 축 정렬 선분(HV/VH 경로)과 AABB 박스의 교차 여부 판정
 */
fun segmentIntersectsRect(
    p1: Offset, p2: Offset,
    left: Float, top: Float, right: Float, bottom: Float
): Boolean {
    return if (abs(p1.x - p2.x) < 0.5f) {
        // 수직 선분
        val x = p1.x
        if (x < left || x > right) return false
        val y1 = minOf(p1.y, p2.y); val y2 = maxOf(p1.y, p2.y)
        y2 > top && y1 < bottom
    } else {
        // 수평 선분
        val y = p1.y
        if (y < top || y > bottom) return false
        val x1 = minOf(p1.x, p2.x); val x2 = maxOf(p1.x, p2.x)
        x2 > left && x1 < right
    }
}

/**
 * 경로 포인트 목록의 총 길이 계산
 */
fun calcPathLen(pts: List<Offset>): Float {
    var len = 0f
    for (i in 0 until pts.size - 1) {
        val dx = pts[i + 1].x - pts[i].x
        val dy = pts[i + 1].y - pts[i].y
        len += kotlin.math.sqrt(dx * dx + dy * dy)
    }
    return len
}

/**
 * ISO 5807 표준 플로우차트 노드 뷰 + 4개 마그넷 접점 포트
 */
@Composable
fun IsoNodeView(
    node: FlowNode,
    isSelected: Boolean,
    isConnectMode: Boolean,
    selectedPortPos: PortPosition?,
    onPositionChanged: (Float, Float) -> Unit,
    onDragEnd: () -> Unit,
    onNodeClick: () -> Unit,
    onPortClick: (PortPosition) -> Unit
) {
    Box(
        modifier = Modifier
            .offset { IntOffset(node.x.roundToInt(), node.y.roundToInt()) }
            .size(node.width.dp, node.height.dp)
            .pointerInput(node.id) {
                detectDragGestures(
                    onDrag = { change, dragAmount ->
                        change.consume()
                        onPositionChanged(dragAmount.x, dragAmount.y)
                    },
                    onDragEnd = {
                        onDragEnd()
                    }
                )
            }
            .clickable { onNodeClick() },
        contentAlignment = Alignment.Center
    ) {
        // 1. ISO 표준 도형 그래픽 (Canvas 직접 렌더링)
        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height
            val strokeW = if (isSelected) 5.5f else 3.5f
            val borderCol = if (isSelected) Color(0xFFF59E0B) else node.shape.borderColor

            when (node.shape) {
                NodeShape.TERMINAL -> {
                    val radius = h / 2
                    drawRoundRect(
                        color = node.shape.bgColor,
                        size = size,
                        cornerRadius = CornerRadius(radius, radius),
                        style = Fill
                    )
                    drawRoundRect(
                        color = borderCol,
                        size = size,
                        cornerRadius = CornerRadius(radius, radius),
                        style = Stroke(width = strokeW)
                    )
                }
                NodeShape.PROCESS -> {
                    drawRoundRect(
                        color = node.shape.bgColor,
                        size = size,
                        cornerRadius = CornerRadius(4f, 4f),
                        style = Fill
                    )
                    drawRoundRect(
                        color = borderCol,
                        size = size,
                        cornerRadius = CornerRadius(4f, 4f),
                        style = Stroke(width = strokeW)
                    )
                }
                NodeShape.DECISION -> {
                    val path = Path().apply {
                        moveTo(w / 2, 0f)
                        lineTo(w, h / 2)
                        lineTo(w / 2, h)
                        lineTo(0f, h / 2)
                        close()
                    }
                    drawPath(path = path, color = node.shape.bgColor, style = Fill)
                    drawPath(path = path, color = borderCol, style = Stroke(width = strokeW))
                }
                NodeShape.IO -> {
                    val skew = w * 0.18f
                    val path = Path().apply {
                        moveTo(skew, 0f)
                        lineTo(w, 0f)
                        lineTo(w - skew, h)
                        lineTo(0f, h)
                        close()
                    }
                    drawPath(path = path, color = node.shape.bgColor, style = Fill)
                    drawPath(path = path, color = borderCol, style = Stroke(width = strokeW))
                }
                NodeShape.DATABASE -> {
                    val capH = h * 0.25f
                    val bodyPath = Path().apply {
                        moveTo(0f, capH / 2)
                        lineTo(0f, h - capH / 2)
                        quadraticTo(w / 2, h + capH / 2, w, h - capH / 2)
                        lineTo(w, capH / 2)
                        close()
                    }
                    drawPath(path = bodyPath, color = node.shape.bgColor, style = Fill)
                    drawPath(path = bodyPath, color = borderCol, style = Stroke(width = strokeW))

                    drawOval(color = node.shape.bgColor, topLeft = Offset(0f, 0f), size = Size(w, capH), style = Fill)
                    drawOval(color = borderCol, topLeft = Offset(0f, 0f), size = Size(w, capH), style = Stroke(width = strokeW))
                }
                NodeShape.DOCUMENT -> {
                    val waveH = h * 0.22f
                    val docPath = Path().apply {
                        moveTo(0f, 0f)
                        lineTo(w, 0f)
                        lineTo(w, h - waveH)
                        cubicTo(w * 0.75f, h, w * 0.25f, h - 2 * waveH, 0f, h - waveH)
                        close()
                    }
                    drawPath(path = docPath, color = node.shape.bgColor, style = Fill)
                    drawPath(path = docPath, color = borderCol, style = Stroke(width = strokeW))
                }
            }
        }

        // 2. 텍스트 라벨
        Text(
            text = node.text,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF0F172A),
            textAlign = TextAlign.Center,
            maxLines = 2,
            modifier = Modifier.padding(horizontal = 6.dp)
        )

        // 3. 4개 마그넷 꼭지점 포트 (상, 하, 좌, 우)
        MagnetPort(
            alignment = Alignment.TopCenter,
            isSelected = selectedPortPos == PortPosition.TOP,
            onClick = { onPortClick(PortPosition.TOP) }
        )
        MagnetPort(
            alignment = Alignment.BottomCenter,
            isSelected = selectedPortPos == PortPosition.BOTTOM,
            onClick = { onPortClick(PortPosition.BOTTOM) }
        )
        MagnetPort(
            alignment = Alignment.CenterStart,
            isSelected = selectedPortPos == PortPosition.LEFT,
            onClick = { onPortClick(PortPosition.LEFT) }
        )
        MagnetPort(
            alignment = Alignment.CenterEnd,
            isSelected = selectedPortPos == PortPosition.RIGHT,
            onClick = { onPortClick(PortPosition.RIGHT) }
        )
    }
}

/**
 * 4개 꼭지점 마그넷 포트 도트 위젯
 */
@Composable
fun BoxScope.MagnetPort(
    alignment: Alignment,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .align(alignment)
            .size(10.dp)
            .clip(CircleShape)
            .background(if (isSelected) Color(0xFFEF4444) else Color(0xFF3B82F6))
            .border(1.2.dp, Color.White, CircleShape)
            .clickable { onClick() }
    )
}

fun calculatePortOffset(node: FlowNode, port: PortPosition): Offset {
    val x = node.x
    val y = node.y
    val w = node.width
    val h = node.height

    return when (port) {
        PortPosition.TOP -> Offset(x + w / 2, y)
        PortPosition.BOTTOM -> Offset(x + w / 2, y + h)
        PortPosition.LEFT -> Offset(x, y + h / 2)
        PortPosition.RIGHT -> Offset(x + w, y + h / 2)
    }
}

fun androidx.compose.ui.graphics.drawscope.DrawScope.drawArrowHead(
    endOffset: Offset,
    port: PortPosition,
    color: Color
) {
    val headSize = 10f
    val path = Path()

    when (port) {
        PortPosition.TOP -> {
            path.moveTo(endOffset.x, endOffset.y)
            path.lineTo(endOffset.x - headSize / 2, endOffset.y - headSize)
            path.lineTo(endOffset.x + headSize / 2, endOffset.y - headSize)
            path.close()
        }
        PortPosition.BOTTOM -> {
            path.moveTo(endOffset.x, endOffset.y)
            path.lineTo(endOffset.x - headSize / 2, endOffset.y + headSize)
            path.lineTo(endOffset.x + headSize / 2, endOffset.y + headSize)
            path.close()
        }
        PortPosition.LEFT -> {
            path.moveTo(endOffset.x, endOffset.y)
            path.lineTo(endOffset.x - headSize, endOffset.y - headSize / 2)
            path.lineTo(endOffset.x - headSize, endOffset.y + headSize / 2)
            path.close()
        }
        PortPosition.RIGHT -> {
            path.moveTo(endOffset.x, endOffset.y)
            path.lineTo(endOffset.x + headSize, endOffset.y - headSize / 2)
            path.lineTo(endOffset.x + headSize, endOffset.y + headSize / 2)
            path.close()
        }
    }
    drawPath(path = path, color = color, style = Fill)
}

/**
 * 겹침 방지 스마트 자동 배치 (충분하고 쾌적한 간격 확보)
 */
fun findNextSmartPosition(nodes: List<FlowNode>, direction: String): Pair<Float, Float> {
    if (nodes.isEmpty()) return Pair(35f, 35f)

    val last = nodes.last()
    val gapY = 42f // 세로 넉넉한 간격
    val gapX = 55f // 가로 넉넉한 간격

    return if (direction == "TD") {
        var candY = last.y + last.height + gapY
        var candX = last.x
        if (candY > 360f) {
            candY = 35f
            candX = last.x + last.width + gapX
        }
        Pair(candX, candY)
    } else {
        var candX = last.x + last.width + gapX
        var candY = last.y
        if (candX > 640f) {
            candX = 35f
            candY = last.y + last.height + gapY
        }
        Pair(candX, candY)
    }
}

/**
 * 전체 노드 자동 정렬 (새 객체 인스턴스 반환으로 Compose 실시간 재렌더링 100% 보장)
 */
fun autoAlignNodes(nodes: List<FlowNode>, edges: List<FlowEdge>, direction: String): List<FlowNode> {
    if (nodes.isEmpty()) return emptyList()

    val startX = 40f
    val startY = 40f
    val stepGap = if (direction == "TD") 58f else 95f

    // 연결선 기반 시작 노드 탐색 (들어오는 선이 없는 노드 우선)
    val targetIds = edges.map { it.toNodeId }.toSet()
    val startNodes = nodes.filterNot { targetIds.contains(it.id) }
    val orderedNodes = mutableListOf<FlowNode>()
    val visited = mutableSetOf<String>()

    fun traverse(node: FlowNode) {
        if (visited.contains(node.id)) return
        visited.add(node.id)
        orderedNodes.add(node)
        val outgoingEdges = edges.filter { it.fromNodeId == node.id }
        outgoingEdges.forEach { edge ->
            val nextNode = nodes.find { it.id == edge.toNodeId }
            if (nextNode != null && !visited.contains(nextNode.id)) {
                traverse(nextNode)
            }
        }
    }

    startNodes.forEach { traverse(it) }
    nodes.forEach { if (!visited.contains(it.id)) traverse(it) }

    // 새로운 인스턴스로 반환하여 Compose 강제 리컴포지션 트리거
    return orderedNodes.mapIndexed { index, node ->
        if (direction == "TD") {
            node.copy(x = startX, y = startY + index * stepGap)
        } else {
            node.copy(x = startX + index * stepGap, y = startY)
        }
    }
}

fun saveFlowchartToPrefs(prefs: android.content.SharedPreferences, nodes: List<FlowNode>, edges: List<FlowEdge>, direction: String) {
    try {
        val root = JSONObject()
        root.put("direction", direction)

        val nodesArr = JSONArray()
        nodes.forEach { n ->
            nodesArr.put(JSONObject().apply {
                put("id", n.id)
                put("text", n.text)
                put("shape", n.shape.name)
                put("x", n.x)
                put("y", n.y)
                put("w", n.width)
                put("h", n.height)
            })
        }
        root.put("nodes", nodesArr)

        val edgesArr = JSONArray()
        edges.forEach { e ->
            edgesArr.put(JSONObject().apply {
                put("id", e.id)
                put("from", e.fromNodeId)
                put("to", e.toNodeId)
                put("fromPort", e.fromPort.name)
                put("toPort", e.toPort.name)
                put("label", e.label)
            })
        }
        root.put("edges", edgesArr)

        prefs.edit().putString("saved_flowchart_json", root.toString()).apply()
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

fun loadFlowchartFromPrefs(prefs: android.content.SharedPreferences): Pair<List<FlowNode>, List<FlowEdge>> {
    val rawJson = prefs.getString("saved_flowchart_json", null)
    if (rawJson.isNullOrBlank()) {
        // 최초 실행 시 기본 제공 다이어그램 제거: 완전 빈 캔버스로 시작
        return Pair(emptyList(), emptyList())
    }

    try {
        val root = JSONObject(rawJson)
        val nodesArr = root.optJSONArray("nodes") ?: JSONArray()
        val loadedNodes = mutableListOf<FlowNode>()

        for (i in 0 until nodesArr.length()) {
            val obj = nodesArr.getJSONObject(i)
            val shapeName = obj.optString("shape", "PROCESS")
            val shape = try { NodeShape.valueOf(shapeName) } catch (_: Exception) { NodeShape.PROCESS }
            loadedNodes.add(
                FlowNode(
                    id = obj.getString("id"),
                    text = obj.optString("text", ""),
                    shape = shape,
                    x = obj.getDouble("x").toFloat(),
                    y = obj.getDouble("y").toFloat(),
                    width = obj.optDouble("w", 66.0).toFloat(),
                    height = obj.optDouble("h", 30.0).toFloat()
                )
            )
        }

        val edgesArr = root.optJSONArray("edges") ?: JSONArray()
        val loadedEdges = mutableListOf<FlowEdge>()
        for (i in 0 until edgesArr.length()) {
            val obj = edgesArr.getJSONObject(i)
            loadedEdges.add(
                FlowEdge(
                    id = obj.getString("id"),
                    fromNodeId = obj.getString("from"),
                    toNodeId = obj.getString("to"),
                    fromPort = try { PortPosition.valueOf(obj.optString("fromPort", "BOTTOM")) } catch (_: Exception) { PortPosition.BOTTOM },
                    toPort = try { PortPosition.valueOf(obj.optString("toPort", "TOP")) } catch (_: Exception) { PortPosition.TOP },
                    label = obj.optString("label", "")
                )
            )
        }
        return Pair(loadedNodes, loadedEdges)
    } catch (e: Exception) {
        e.printStackTrace()
        return Pair(emptyList(), emptyList())
    }
}

/**
 * 사내 Wi-Fi 직접 LAN 전송
 */
suspend fun sendDiagramToPc(
    ip: String,
    pin: String,
    nodes: List<FlowNode>,
    edges: List<FlowEdge>,
    direction: String
): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val cleanIp = ip.trim().removePrefix("http://").removeSuffix("/")
            val targetUrl = "http://$cleanIp:19850/api/upload"
            val url = URL(targetUrl)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8")
            conn.setRequestProperty("X-PIN", pin.trim())
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            conn.doOutput = true

            val json = buildPayloadJson(pin, direction, nodes, edges)

            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(json.toString())
            writer.flush()
            writer.close()

            conn.responseCode in 200..299
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}

/**
 * 🌐 원격/LTE 어디서나 클라우드 릴레이 전송
 */
suspend fun sendDiagramViaCloud(
    cloudUrl: String,
    pin: String,
    nodes: List<FlowNode>,
    edges: List<FlowEdge>,
    direction: String
): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val cleanUrl = cloudUrl.trim().removeSuffix("/")
            val targetUrl = "$cleanUrl/api/upload"
            val url = URL(targetUrl)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8")
            conn.setRequestProperty("X-PIN", pin.trim())
            conn.connectTimeout = 8000
            conn.readTimeout = 8000
            conn.doOutput = true

            val json = buildPayloadJson(pin, direction, nodes, edges)

            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(json.toString())
            writer.flush()
            writer.close()

            conn.responseCode in 200..299
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}

fun buildPayloadJson(pin: String, direction: String, nodes: List<FlowNode>, edges: List<FlowEdge>): JSONObject {
    return JSONObject().apply {
        put("pin", pin.trim())
        put("type", "flowchart")
        put("direction", direction)

        val itemsArray = JSONArray()

        nodes.forEach { n ->
            val itemObj = JSONObject().apply {
                put("type", "FlowchartNodeItem")
                put("text", n.text)
                put("x", n.x.toDouble() * 2.0)
                put("y", n.y.toDouble() * 2.0)
                put("w", n.width.toDouble() * 2.0)
                put("h", n.height.toDouble() * 2.0)
                put("shape_type", n.shape.name.lowercase())
                put("style", JSONObject().apply {
                    put("bg_color", when (n.shape) {
                        NodeShape.TERMINAL -> "#ECFDF5"
                        NodeShape.DECISION -> "#FFFBEB"
                        NodeShape.DATABASE -> "#FAF5FF"
                        NodeShape.IO -> "#F0FDF4"
                        NodeShape.DOCUMENT -> "#EEF2FF"
                        else -> "#EFF6FF"
                    })
                    put("border_color", when (n.shape) {
                        NodeShape.TERMINAL -> "#059669"
                        NodeShape.DECISION -> "#D97706"
                        NodeShape.DATABASE -> "#7C3AED"
                        NodeShape.IO -> "#16A34A"
                        NodeShape.DOCUMENT -> "#4F46E5"
                        else -> "#2563EB"
                    })
                    put("border_width", 2)
                    put("text_color", "#1E293B")
                    put("font_size", 12)
                    put("font_bold", true)
                })
            }
            itemsArray.put(itemObj)
        }

        val nodeMap = nodes.associateBy { it.id }
        edges.forEach { e ->
            val fromNode = nodeMap[e.fromNodeId]
            val toNode = nodeMap[e.toNodeId]
            if (fromNode != null && toNode != null) {
                val s = calculatePortOffset(fromNode, e.fromPort)
                val end = calculatePortOffset(toNode, e.toPort)

                val edgeObj = JSONObject().apply {
                    put("type", "ElbowArrowItem")
                    put("start_pos", JSONArray().put(s.x.toDouble() * 2.0).put(s.y.toDouble() * 2.0))
                    put("end_pos", JSONArray().put(end.x.toDouble() * 2.0).put(end.y.toDouble() * 2.0))
                    put("route_mode", if (direction == "TD") "HV" else "VH")
                    put("label", e.label)
                    put("style", JSONObject().apply {
                        put("color", "#2563EB")
                        put("width", 3)
                        put("head_size", 12)
                    })
                }
                itemsArray.put(edgeObj)
            }
        }

        put("data", JSONObject().apply {
            put("items", itemsArray)
        })
    }
}

suspend fun sendPhotoToPc(targetHost: String, pin: String, bitmap: Bitmap): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val cleanHost = targetHost.trim().removeSuffix("/")
            val targetUrl = if (cleanHost.startsWith("http://") || cleanHost.startsWith("https://")) {
                "$cleanHost/api/upload"
            } else {
                "http://$cleanHost:19850/api/upload"
            }
            val url = URL(targetUrl)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8")
            conn.setRequestProperty("X-PIN", pin.trim())
            conn.connectTimeout = 8000
            conn.readTimeout = 8000
            conn.doOutput = true

            val stream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream)
            val b64 = Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)

            val json = JSONObject().apply {
                put("pin", pin.trim())
                put("type", "image")
                put("title", "모바일 촬영 손그림")
                put("image_base64", b64)
            }

            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(json.toString())
            writer.flush()
            writer.close()

            conn.responseCode in 200..299
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}
