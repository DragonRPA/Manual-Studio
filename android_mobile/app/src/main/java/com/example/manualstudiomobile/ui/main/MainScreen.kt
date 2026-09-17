package com.example.manualstudiomobile.ui.main

import androidx.compose.ui.draw.clip
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
    var text: String,
    val shape: NodeShape,
    var x: Float,
    var y: Float,
    val width: Float = 66f,
    val height: Float = 30f
)

data class FlowEdge(
    val id: String,
    val fromNodeId: String,
    val toNodeId: String,
    val fromPort: PortPosition = PortPosition.BOTTOM,
    val toPort: PortPosition = PortPosition.TOP,
    var label: String = ""
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ManualStudioPrefs", Context.MODE_PRIVATE) }

    // SharedPreferences 영속 데이터 불러오기 (화면 회전/앱 재실행 시 100% 복원)
    val savedData = remember { loadFlowchartFromPrefs(prefs) }

    var nodes by remember { mutableStateOf(savedData.first) }
    var edges by remember { mutableStateOf(savedData.second) }
    var direction by remember { mutableStateOf(prefs.getString("flow_direction", "TD") ?: "TD") }

    // 변경사항 자동 저장
    fun persistState() {
        saveFlowchartToPrefs(prefs, nodes, edges, direction)
    }

    // 마그넷 포트 연결 모드 상태
    var connectMode by remember { mutableStateOf(false) }
    var selectedPortNodeId by remember { mutableStateOf<String?>(null) }
    var selectedPortPos by remember { mutableStateOf<PortPosition?>(null) }

    var selectedNodeForEdit by remember { mutableStateOf<FlowNode?>(null) }
    var showSendDialog by remember { mutableStateOf(false) }
    var lastCapturedBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var showPhotoDialog by remember { mutableStateOf(false) }

    var pcIp by remember { mutableStateOf(prefs.getString("pc_ip", "192.168.0.") ?: "192.168.0.") }
    var pcPin by remember { mutableStateOf(prefs.getString("pc_pin", "") ?: "") }
    var isSending by remember { mutableStateOf(false) }

    // 카메라 직접 촬영 런처 (파일 선택기 우회, 카메라 앱 직접 실행)
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

    // 카메라 권한 요청 런처
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
                                color = Color(0xFF2563EB),
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    "연결 모드",
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

                    // 2. 마그넷 연결선 모드 토글 버튼
                    IconButton(
                        onClick = {
                            connectMode = !connectMode
                            selectedPortNodeId = null
                            selectedPortPos = null
                            val msg = if (connectMode) "연결 모드: 노드의 접점을 차례로 터치하세요" else "연결 모드 종료"
                            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text(if (connectMode) "🔗" else "⛓️", fontSize = 16.sp)
                    }

                    // 3. 자동정렬 (TD/LR 전환 및 겹침 제로 정렬)
                    IconButton(
                        onClick = {
                            direction = if (direction == "TD") "LR" else "TD"
                            prefs.edit().putString("flow_direction", direction).apply()
                            nodes = autoAlignNodes(nodes, direction)
                            persistState()
                            Toast.makeText(context, "자동정렬 완료 (${if (direction == "TD") "상하 TD" else "좌우 LR"})", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text("⚡", fontSize = 16.sp)
                    }

                    // 4. PC 전송 버튼
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
            // 하단 초슬림 팔레트 (시스템 내비게이션 바 겹침 완벽 방지)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF1E293B))
                    .navigationBarsPadding() // 필수: 세로/가로 모드 시 홈 버튼 및 제스처 바 겹침 완벽 차단
                    .padding(vertical = 4.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(5.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // ISO 표준 다이어그램 도형 추가 버튼군 (컴팩트 마이크로 사이즈)
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
                                // 이전 노드가 있으면 자동으로 연결선 연결
                                val newEdges = if (nodes.isNotEmpty()) {
                                    val prev = nodes.last()
                                    edges + FlowEdge(
                                        id = "e_${System.currentTimeMillis()}",
                                        fromNodeId = prev.id,
                                        toNodeId = newNodeId,
                                        fromPort = if (direction == "TD") PortPosition.BOTTOM else PortPosition.RIGHT,
                                        toPort = if (direction == "TD") PortPosition.TOP else PortPosition.LEFT
                                    )
                                } else edges

                                nodes = nodes + newNode
                                edges = newEdges
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
                            Text(
                                shape.label,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }

                    // 캔버스 초기화 버튼
                    Button(
                        onClick = {
                            nodes = emptyList()
                            edges = emptyList()
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
        ) {
            // 1. 커스텀 연결선(FlowEdge) 렌더링 캔버스
            Canvas(modifier = Modifier.fillMaxSize()) {
                val nodeMap = nodes.associateBy { it.id }

                edges.forEach { edge ->
                    val fromNode = nodeMap[edge.fromNodeId]
                    val toNode = nodeMap[edge.toNodeId]

                    if (fromNode != null && toNode != null) {
                        val start = calculatePortOffset(fromNode, edge.fromPort)
                        val end = calculatePortOffset(toNode, edge.toPort)

                        // 직각 꺾임선 패스 계산
                        val path = Path().apply {
                            moveTo(start.x, start.y)
                            if (edge.fromPort == PortPosition.BOTTOM && edge.toPort == PortPosition.TOP) {
                                val midY = (start.y + end.y) / 2
                                lineTo(start.x, midY)
                                lineTo(end.x, midY)
                                lineTo(end.x, end.y)
                            } else if (edge.fromPort == PortPosition.RIGHT && edge.toPort == PortPosition.LEFT) {
                                val midX = (start.x + end.x) / 2
                                lineTo(midX, start.y)
                                lineTo(midX, end.y)
                                lineTo(end.x, end.y)
                            } else {
                                val midX = (start.x + end.x) / 2
                                lineTo(midX, start.y)
                                lineTo(midX, end.y)
                                lineTo(end.x, end.y)
                            }
                        }

                        // 연결선 본체
                        drawPath(
                            path = path,
                            color = Color(0xFF60A5FA),
                            style = Stroke(width = 3.5f)
                        )

                        // 화살표 머리 그리기
                        drawArrowHead(
                            endOffset = end,
                            port = edge.toPort,
                            color = Color(0xFF60A5FA)
                        )
                    }
                }
            }

            // 2. ISO 표준 플로우차트 노드 및 4개 마그넷 접점 렌더링
            nodes.forEach { node ->
                key(node.id) {
                    IsoNodeView(
                        node = node,
                        isConnectMode = connectMode,
                        selectedPortPos = if (selectedPortNodeId == node.id) selectedPortPos else null,
                        onPositionChanged = { dx, dy ->
                            node.x += dx
                            node.y += dy
                            persistState()
                        },
                        onNodeClick = {
                            selectedNodeForEdit = node
                        },
                        onPortClick = { port ->
                            if (!connectMode) {
                                connectMode = true
                            }
                            if (selectedPortNodeId == null) {
                                selectedPortNodeId = node.id
                                selectedPortPos = port
                                Toast.makeText(context, "시작 접점 선택됨: 대상 노드의 접점을 터치하세요", Toast.LENGTH_SHORT).show()
                            } else {
                                if (selectedPortNodeId != node.id) {
                                    val newEdge = FlowEdge(
                                        id = "e_${System.currentTimeMillis()}",
                                        fromNodeId = selectedPortNodeId!!,
                                        toNodeId = node.id,
                                        fromPort = selectedPortPos ?: PortPosition.BOTTOM,
                                        toPort = port
                                    )
                                    edges = edges + newEdge
                                    persistState()
                                    Toast.makeText(context, "✅ 연결선 생성 완료!", Toast.LENGTH_SHORT).show()
                                }
                                selectedPortNodeId = null
                                selectedPortPos = null
                            }
                        }
                    )
                }
            }
        }
    }

    // 1. 노드 텍스트 수정 및 삭제 다이얼로그
    selectedNodeForEdit?.let { node ->
        var editText by remember { mutableStateOf(node.text) }
        AlertDialog(
            onDismissRequest = { selectedNodeForEdit = null },
            title = { Text("노드 편집", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("유형: ${node.shape.label}", fontSize = 12.sp, color = Color.Gray)
                    OutlinedTextField(
                        value = editText,
                        onValueChange = { editText = it },
                        label = { Text("표시할 내용") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    node.text = editText
                    selectedNodeForEdit = null
                    persistState()
                }) {
                    Text("확인")
                }
            },
            dismissButton = {
                Row {
                    TextButton(onClick = {
                        nodes = nodes.filter { it.id != node.id }
                        edges = edges.filter { it.fromNodeId != node.id && it.toNodeId != node.id }
                        selectedNodeForEdit = null
                        persistState()
                    }) {
                        Text("삭제", color = Color(0xFFDC2626))
                    }
                    TextButton(onClick = { selectedNodeForEdit = null }) {
                        Text("취소")
                    }
                }
            }
        )
    }

    // 2. PC 전송 다이얼로그 (노드 + 연결선 일체형 JSON 전송)
    if (showSendDialog) {
        AlertDialog(
            onDismissRequest = { showSendDialog = false },
            title = { Text("PC 매뉴얼 스튜디오로 전송", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("PC 화면의 QR 코드 또는 IP/PIN 번호를 입력하세요.", fontSize = 12.sp, color = Color.Gray)
                    OutlinedTextField(
                        value = pcIp,
                        onValueChange = { pcIp = it },
                        label = { Text("PC IP 주소 (예: 192.168.0.25)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = pcPin,
                        onValueChange = { pcPin = it },
                        label = { Text("6자리 PIN (예: 376-310)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        prefs.edit().putString("pc_ip", pcIp).putString("pc_pin", pcPin).apply()
                        isSending = true
                        CoroutineScope(Dispatchers.IO).launch {
                            val success = sendDiagramToPc(pcIp, pcPin, nodes, edges, direction)
                            withContext(Dispatchers.Main) {
                                isSending = false
                                if (success) {
                                    Toast.makeText(context, "🎉 PC 매뉴얼 스튜디오로 전송 성공!", Toast.LENGTH_LONG).show()
                                    showSendDialog = false
                                } else {
                                    Toast.makeText(context, "전송 실패: IP와 PIN 번호를 확인하세요.", Toast.LENGTH_LONG).show()
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
                    OutlinedTextField(
                        value = pcIp,
                        onValueChange = { pcIp = it },
                        label = { Text("PC IP 주소") },
                        modifier = Modifier.fillMaxWidth()
                    )
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
                        prefs.edit().putString("pc_ip", pcIp).putString("pc_pin", pcPin).apply()
                        CoroutineScope(Dispatchers.IO).launch {
                            val success = sendPhotoToPc(pcIp, pcPin, lastCapturedBitmap!!)
                            withContext(Dispatchers.Main) {
                                if (success) {
                                    Toast.makeText(context, "📷 손그림 사진 PC 전송 완료!", Toast.LENGTH_LONG).show()
                                    showPhotoDialog = false
                                } else {
                                    Toast.makeText(context, "전송 실패: 연결을 확인하세요.", Toast.LENGTH_LONG).show()
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
 * ISO 5807 표준 플로우차트 노드 뷰 + 4개 마그넷 접점 포트
 */
@Composable
fun IsoNodeView(
    node: FlowNode,
    isConnectMode: Boolean,
    selectedPortPos: PortPosition?,
    onPositionChanged: (Float, Float) -> Unit,
    onNodeClick: () -> Unit,
    onPortClick: (PortPosition) -> Unit
) {
    var offsetX by remember { mutableStateOf(node.x) }
    var offsetY by remember { mutableStateOf(node.y) }

    LaunchedEffect(node.x, node.y) {
        offsetX = node.x
        offsetY = node.y
    }

    Box(
        modifier = Modifier
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .size(node.width.dp, node.height.dp)
            .pointerInput(node.id) {
                detectDragGestures { change, dragAmount ->
                    change.consume()
                    offsetX += dragAmount.x
                    offsetY += dragAmount.y
                    onPositionChanged(dragAmount.x, dragAmount.y)
                }
            }
            .clickable { onNodeClick() },
        contentAlignment = Alignment.Center
    ) {
        // 1. ISO 표준 도형 그래픽 (Canvas로 직접 렌더링)
        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height

            when (node.shape) {
                NodeShape.TERMINAL -> {
                    // 시작/종료: 완전한 둥근 알약형 (Stadium/Capsule)
                    val radius = h / 2
                    drawRoundRect(
                        color = node.shape.bgColor,
                        size = size,
                        cornerRadius = CornerRadius(radius, radius),
                        style = Fill
                    )
                    drawRoundRect(
                        color = node.shape.borderColor,
                        size = size,
                        cornerRadius = CornerRadius(radius, radius),
                        style = Stroke(width = 3.5f)
                    )
                }
                NodeShape.PROCESS -> {
                    // 일반 작업: 표준 직사각형
                    drawRoundRect(
                        color = node.shape.bgColor,
                        size = size,
                        cornerRadius = CornerRadius(4f, 4f),
                        style = Fill
                    )
                    drawRoundRect(
                        color = node.shape.borderColor,
                        size = size,
                        cornerRadius = CornerRadius(4f, 4f),
                        style = Stroke(width = 3.5f)
                    )
                }
                NodeShape.DECISION -> {
                    // 조건 분기: ISO 표준 마름모 (Rhombus / Diamond)
                    val path = Path().apply {
                        moveTo(w / 2, 0f)
                        lineTo(w, h / 2)
                        lineTo(w / 2, h)
                        lineTo(0f, h / 2)
                        close()
                    }
                    drawPath(path = path, color = node.shape.bgColor, style = Fill)
                    drawPath(path = path, color = node.shape.borderColor, style = Stroke(width = 3.5f))
                }
                NodeShape.IO -> {
                    // 데이터 입출력: ISO 표준 평행사변형 (Parallelogram)
                    val skew = w * 0.18f
                    val path = Path().apply {
                        moveTo(skew, 0f)
                        lineTo(w, 0f)
                        lineTo(w - skew, h)
                        lineTo(0f, h)
                        close()
                    }
                    drawPath(path = path, color = node.shape.bgColor, style = Fill)
                    drawPath(path = path, color = node.shape.borderColor, style = Stroke(width = 3.5f))
                }
                NodeShape.DATABASE -> {
                    // 데이터베이스: ISO 표준 원통형 실린더 (Cylinder)
                    val capH = h * 0.25f
                    val bodyPath = Path().apply {
                        moveTo(0f, capH / 2)
                        lineTo(0f, h - capH / 2)
                        quadraticTo(w / 2, h + capH / 2, w, h - capH / 2)
                        lineTo(w, capH / 2)
                        close()
                    }
                    drawPath(path = bodyPath, color = node.shape.bgColor, style = Fill)
                    drawPath(path = bodyPath, color = node.shape.borderColor, style = Stroke(width = 3.5f))

                    // 상단 타원 캡
                    drawOval(
                        color = node.shape.bgColor,
                        topLeft = Offset(0f, 0f),
                        size = Size(w, capH),
                        style = Fill
                    )
                    drawOval(
                        color = node.shape.borderColor,
                        topLeft = Offset(0f, 0f),
                        size = Size(w, capH),
                        style = Stroke(width = 3.5f)
                    )
                }
                NodeShape.DOCUMENT -> {
                    // 문서 서식: ISO 표준 하단 물결형 문서 (Document with wavy bottom)
                    val waveH = h * 0.22f
                    val docPath = Path().apply {
                        moveTo(0f, 0f)
                        lineTo(w, 0f)
                        lineTo(w, h - waveH)
                        cubicTo(
                            w * 0.75f, h,
                            w * 0.25f, h - 2 * waveH,
                            0f, h - waveH
                        )
                        close()
                    }
                    drawPath(path = docPath, color = node.shape.bgColor, style = Fill)
                    drawPath(path = docPath, color = node.shape.borderColor, style = Stroke(width = 3.5f))
                }
            }
        }

        // 2. 텍스트 라벨 (컴팩트 폰트, 시인성 극대화)
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

/**
 * 포트 위치에 따른 절대 오프셋 좌표 계산
 */
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

/**
 * 화살표 머리(삼각형) 렌더링
 */
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
 * 겹침 방지 스마트 자동 배치 (Anti-collision Smart Placement)
 */
fun findNextSmartPosition(nodes: List<FlowNode>, direction: String): Pair<Float, Float> {
    if (nodes.isEmpty()) return Pair(40f, 40f)

    val last = nodes.last()
    val gap = 20f

    return if (direction == "TD") {
        var candY = last.y + last.height + gap
        var candX = last.x
        if (candY > 360f) {
            candY = 40f
            candX = last.x + last.width + gap + 10f
        }
        Pair(candX, candY)
    } else {
        var candX = last.x + last.width + gap
        var candY = last.y
        if (candX > 640f) {
            candX = 40f
            candY = last.y + last.height + gap + 10f
        }
        Pair(candX, candY)
    }
}

/**
 * 전체 노드 자동 격자 정렬 (⚡ 버튼)
 */
fun autoAlignNodes(nodes: List<FlowNode>, direction: String): List<FlowNode> {
    val startX = 40f
    val startY = 40f
    val gap = if (direction == "TD") 50f else 85f

    nodes.forEachIndexed { index, node ->
        if (direction == "TD") {
            node.x = startX
            node.y = startY + index * gap
        } else {
            node.x = startX + index * gap
            node.y = startY
        }
    }
    return nodes
}

/**
 * SharedPreferences 영속 저장
 */
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

/**
 * SharedPreferences 영속 복원
 */
fun loadFlowchartFromPrefs(prefs: android.content.SharedPreferences): Pair<List<FlowNode>, List<FlowEdge>> {
    val rawJson = prefs.getString("saved_flowchart_json", null)
    if (rawJson.isNullOrBlank()) {
        // 기본 시작 템플릿
        val defaultNodes = listOf(
            FlowNode("n1", "시작", NodeShape.TERMINAL, 40f, 40f, 66f, 30f),
            FlowNode("n2", "작업 수행", NodeShape.PROCESS, 40f, 90f, 66f, 30f),
            FlowNode("n3", "성공 여부?", NodeShape.DECISION, 40f, 140f, 66f, 30f),
            FlowNode("n4", "완료", NodeShape.TERMINAL, 40f, 190f, 66f, 30f)
        )
        val defaultEdges = listOf(
            FlowEdge("e1", "n1", "n2", PortPosition.BOTTOM, PortPosition.TOP),
            FlowEdge("e2", "n2", "n3", PortPosition.BOTTOM, PortPosition.TOP),
            FlowEdge("e3", "n3", "n4", PortPosition.BOTTOM, PortPosition.TOP, "Yes")
        )
        return Pair(defaultNodes, defaultEdges)
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
 * PC 매뉴얼 스튜디오로 노드 + 연결선 일체형 JSON 전송
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

            val json = JSONObject().apply {
                put("pin", pin.trim())
                put("type", "flowchart")
                put("direction", direction)

                val itemsArray = JSONArray()

                // 1. 노드 아이템
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

                // 2. 연결선 아이템 (ElbowArrowItem)
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

            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(json.toString())
            writer.flush()
            writer.close()

            val responseCode = conn.responseCode
            responseCode in 200..299
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}

/**
 * 손그림 직접 촬영 사진 전송
 */
suspend fun sendPhotoToPc(ip: String, pin: String, bitmap: Bitmap): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val cleanIp = ip.trim().removePrefix("http://").removeSuffix("/")
            val targetUrl = "http://$cleanIp:19850/api/upload"
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
