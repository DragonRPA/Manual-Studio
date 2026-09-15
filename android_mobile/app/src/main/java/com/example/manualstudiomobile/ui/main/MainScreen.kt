package com.example.manualstudiomobile.ui.main

import android.content.Context
import android.graphics.Bitmap
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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

enum class NodeShape(val label: String, val bgColor: Color, val borderColor: Color) {
    TERMINAL("시작/종료", Color(0xFFECFDF5), Color(0xFF059669)),
    PROCESS("일반 작업", Color(0xFFEFF6FF), Color(0xFF2563EB)),
    DECISION("조건 분기", Color(0xFFFFFBEB), Color(0xFFD97706)),
    IO("데이터 입출력", Color(0xFFF0FDF4), Color(0xFF16A34A)),
    DATABASE("데이터베이스", Color(0xFFFAF5FF), Color(0xFF7C3AED)),
    DOCUMENT("문서 서식", Color(0xFFEEF2FF), Color(0xFF4F46E5))
}

data class FlowNode(
    val id: String,
    var text: String,
    val shape: NodeShape,
    var x: Float,
    var y: Float,
    val width: Float = 75f,
    val height: Float = 32f
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ManualStudioPrefs", Context.MODE_PRIVATE) }

    var nodes by remember {
        mutableStateOf(
            listOf(
                FlowNode("n1", "시작", NodeShape.TERMINAL, 120f, 40f, 75f, 32f),
                FlowNode("n2", "작업 수행", NodeShape.PROCESS, 120f, 85f, 75f, 32f),
                FlowNode("n3", "성공 여부?", NodeShape.DECISION, 120f, 130f, 75f, 32f),
                FlowNode("n4", "완료", NodeShape.TERMINAL, 120f, 175f, 75f, 32f)
            )
        )
    }

    var direction by remember { mutableStateOf("TD") }
    var selectedNodeForEdit by remember { mutableStateOf<FlowNode?>(null) }
    var showSendDialog by remember { mutableStateOf(false) }
    var lastCapturedBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var showPhotoDialog by remember { mutableStateOf(false) }

    // SharedPreferences 저장된 IP/PIN 불러오기
    var pcIp by remember { mutableStateOf(prefs.getString("pc_ip", "192.168.0.") ?: "192.168.0.") }
    var pcPin by remember { mutableStateOf(prefs.getString("pc_pin", "") ?: "") }
    var isSending by remember { mutableStateOf(false) }

    // 카메라 캡처 런처
    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicturePreview()
    ) { bitmap ->
        if (bitmap != null) {
            lastCapturedBitmap = bitmap
            showPhotoDialog = true
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "매뉴얼 스튜디오 모바일",
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0F172A)
                ),
                actions = {
                    // 카메라 촬영
                    IconButton(onClick = { cameraLauncher.launch(null) }) {
                        Text("📷", fontSize = 18.sp)
                    }
                    // 자동정렬
                    IconButton(onClick = {
                        direction = if (direction == "TD") "LR" else "TD"
                        nodes = autoAlignNodes(nodes, direction)
                        Toast.makeText(context, "자동정렬 완료 (${if (direction == "TD") "상하 TD" else "좌우 LR"})", Toast.LENGTH_SHORT).show()
                    }) {
                        Text("⚡", fontSize = 18.sp)
                    }
                    // PC 전송
                    Button(
                        onClick = { showSendDialog = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        Text("PC 전송", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                }
            )
        },
        bottomBar = {
            // 하단 도형 팔레트
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF1E293B))
                    .padding(vertical = 8.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 12.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    NodeShape.values().forEach { shape ->
                        Button(
                            onClick = {
                                val nextY = 50f + (nodes.size % 8) * 38f
                                val nextX = 40f + (nodes.size % 4) * 20f
                                val newNode = FlowNode(
                                    id = "n_${System.currentTimeMillis()}",
                                    text = shape.label,
                                    shape = shape,
                                    x = nextX,
                                    y = nextY,
                                    width = 75f,
                                    height = 32f
                                )
                                nodes = nodes + newNode
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = shape.bgColor,
                                contentColor = Color(0xFF1E293B)
                            ),
                            shape = RoundedCornerShape(8.dp),
                            border = ButtonDefaults.outlinedButtonBorder.copy(
                                brush = androidx.compose.ui.graphics.SolidColor(shape.borderColor)
                            ),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                        ) {
                            Text(shape.label, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }

                    Button(
                        onClick = {
                            nodes = emptyList()
                            Toast.makeText(context, "캔버스가 초기화되었습니다.", Toast.LENGTH_SHORT).show()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                    ) {
                        Text("전체 삭제", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color.White)
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
            // 연결선 그리기 (순차 연결)
            Canvas(modifier = Modifier.fillMaxSize()) {
                for (i in 0 until nodes.size - 1) {
                    val from = nodes[i]
                    val to = nodes[i + 1]

                    val startOffset = if (direction == "TD") {
                        Offset(from.x + from.width / 2, from.y + from.height)
                    } else {
                        Offset(from.x + from.width, from.y + from.height / 2)
                    }

                    val endOffset = if (direction == "TD") {
                        Offset(to.x + to.width / 2, to.y)
                    } else {
                        Offset(to.x, to.y + to.height / 2)
                    }

                    // 직각 꺾임선 패스
                    val path = Path().apply {
                        moveTo(startOffset.x, startOffset.y)
                        if (direction == "TD") {
                            val midY = (startOffset.y + endOffset.y) / 2
                            lineTo(startOffset.x, midY)
                            lineTo(endOffset.x, midY)
                            lineTo(endOffset.x, endOffset.y)
                        } else {
                            val midX = (startOffset.x + endOffset.x) / 2
                            lineTo(midX, startOffset.y)
                            lineTo(midX, endOffset.y)
                            lineTo(endOffset.x, endOffset.y)
                        }
                    }

                    drawPath(
                        path = path,
                        color = Color(0xFF60A5FA),
                        style = Stroke(width = 4f)
                    )
                }
            }

            // 노드 렌더링
            nodes.forEach { node ->
                key(node.id) {
                    NodeView(
                        node = node,
                        onPositionChanged = { dx, dy ->
                            node.x += dx
                            node.y += dy
                        },
                        onNodeClick = {
                            selectedNodeForEdit = node
                        }
                    )
                }
            }
        }
    }

    // 1. 노드 텍스트 수정 다이얼로그
    selectedNodeForEdit?.let { node ->
        var editText by remember { mutableStateOf(node.text) }
        AlertDialog(
            onDismissRequest = { selectedNodeForEdit = null },
            title = { Text("노드 텍스트 편집", fontWeight = FontWeight.Bold) },
            text = {
                OutlinedTextField(
                    value = editText,
                    onValueChange = { editText = it },
                    label = { Text("표시할 내용") },
                    modifier = Modifier.fillMaxWidth()
                )
            },
            confirmButton = {
                Button(onClick = {
                    node.text = editText
                    selectedNodeForEdit = null
                }) {
                    Text("확인")
                }
            },
            dismissButton = {
                TextButton(onClick = { selectedNodeForEdit = null }) {
                    Text("취소")
                }
            }
        )
    }

    // 2. PC 전송 다이얼로그
    if (showSendDialog) {
        AlertDialog(
            onDismissRequest = { showSendDialog = false },
            title = { Text("PC 매뉴얼 스튜디오로 전송", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("PC 화면의 QR 코드 또는 IP/PIN 번호를 입력하세요.", fontSize = 13.sp, color = Color.Gray)
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
                            val success = sendDiagramToPc(pcIp, pcPin, nodes, direction)
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

    // 3. 사진 전송 다이얼로그
    if (showPhotoDialog && lastCapturedBitmap != null) {
        AlertDialog(
            onDismissRequest = { showPhotoDialog = false },
            title = { Text("📷 손그림 사진 PC 전송", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("촬영한 손그림/화이트보드 사진을 PC로 즉시 전송하시겠습니까?", fontSize = 13.sp)
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

@Composable
fun NodeView(
    node: FlowNode,
    onPositionChanged: (Float, Float) -> Unit,
    onNodeClick: () -> Unit
) {
    var offsetX by remember { mutableStateOf(node.x) }
    var offsetY by remember { mutableStateOf(node.y) }

    val shapeCorner = when (node.shape) {
        NodeShape.TERMINAL -> 14.dp
        NodeShape.DECISION -> 2.dp
        else -> 4.dp
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
            .clip(RoundedCornerShape(shapeCorner))
            .background(node.shape.bgColor)
            .border(1.5.dp, node.shape.borderColor, RoundedCornerShape(shapeCorner))
            .clickable { onNodeClick() }
            .padding(3.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = node.text,
            fontSize = 8.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF1E293B),
            textAlign = TextAlign.Center,
            maxLines = 2
        )
    }
}

fun autoAlignNodes(nodes: List<FlowNode>, direction: String): List<FlowNode> {
    val startX = 40f
    val startY = 40f
    val gap = if (direction == "TD") 45f else 90f

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

suspend fun sendDiagramToPc(ip: String, pin: String, nodes: List<FlowNode>, direction: String): Boolean {
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
                nodes.forEach { n ->
                    val itemObj = JSONObject().apply {
                        put("type", "FlowchartNodeItem")
                        put("text", n.text)
                        put("x", n.x.toDouble())
                        put("y", n.y.toDouble())
                        put("w", n.width.toDouble())
                        put("h", n.height.toDouble())
                        put("shape_type", n.shape.name.lowercase())
                        put("style", JSONObject().apply {
                            put("bg_color", when (n.shape) {
                                NodeShape.TERMINAL -> "#ECFDF5"
                                NodeShape.DECISION -> "#FFFBEB"
                                NodeShape.DATABASE -> "#FAF5FF"
                                else -> "#EFF6FF"
                            })
                            put("border_color", when (n.shape) {
                                NodeShape.TERMINAL -> "#059669"
                                NodeShape.DECISION -> "#D97706"
                                NodeShape.DATABASE -> "#7C3AED"
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
