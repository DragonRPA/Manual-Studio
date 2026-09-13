"""
================================================================================
DragonRPA Manual Studio - Model Context Protocol (MCP) Server
================================================================================
Standard stdio JSON-RPC 2.0 MCP Server adhering to Anthropic MCP (2024-11-05).
Enables Claude Desktop, Claude Cowork, Cursor, and AI Agents to inspect and
automate Manual Studio workflows directly via natural language tool calls.
================================================================================
"""

import sys
import os
import json
import traceback

# CLI 엔진 함수들 임포트
from manual_cli import (
    cli_status, cli_capture, cli_annotate, cli_render_project, cli_export,
    cli_batch, cli_export_doc
)

SERVER_NAME = "manual-studio"
SERVER_VERSION = "1.5.0"
PROTOCOL_VERSION = "2024-11-05"

TOOLS_SPEC = [
    {
        "name": "manual_studio_status",
        "description": "Query Manual Studio application status, version, monitor geometries, and active configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "manual_studio_capture_screen",
        "description": "Capture the primary or secondary display or a specific rectangle (x,y,w,h) to a PNG file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rect": {"type": "string", "description": "Screen bounding box in 'x,y,w,h' format (e.g. '100,100,960,540')"},
                "monitor": {"type": "integer", "description": "Monitor index (0=Primary display)"},
                "fixed": {"type": "boolean", "description": "Use predefined fixed capture rectangle from config.json"},
                "output_path": {"type": "string", "description": "Optional destination file path for PNG"}
            }
        }
    },
    {
        "name": "manual_studio_add_annotations",
        "description": "Apply visual annotations (numbered stamps, highlight boxes, arrows, callouts, text labels) onto an image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Source image path to annotate"},
                "output_path": {"type": "string", "description": "Optional destination path for annotated image"},
                "stamps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stamps in format 'index:x,y[:color:size]' (e.g. '1:150,220')"
                },
                "boxes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of boxes in format 'x,y,w,h[:color:width:fill]' (e.g. '100,180,300,120:#E53935:3:fill')"
                },
                "arrows": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of arrows in format 'x1,y1,x2,y2[:color:width]' (e.g. '120,100,150,200')"
                },
                "elbows": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of right-angle elbow arrows in format 'x1,y1,x2,y2[:color:width:route_mode]' where route_mode is 'HV'/'VH' or preset 'tr'/'br'/'bl'/'tl'"
                },
                "callouts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of callouts in format 'text:bx,by,bw,bh:tx,ty' (e.g. 'Click:200,100,150,50:180,160')"
                },
                "texts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of texts in format 'text:x,y[:color:size:bg]'"
                },
                "raw_items": {
                    "type": "array",
                    "description": "List of raw item dictionaries adhering to Manual Studio schema"
                }
            },
            "required": ["input_path"]
        }
    },
    {
        "name": "manual_studio_render_project",
        "description": "Render a Manual Studio project file (.mcs.json) into a final composite PNG image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to .mcs.json project file"},
                "output_path": {"type": "string", "description": "Destination PNG path"},
                "export_ppt": {"type": "boolean", "description": "Immediately push to active PowerPoint presentation"},
                "export_slides": {"type": "boolean", "description": "Immediately push to active Google Slides in browser"}
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "manual_studio_export_presentation",
        "description": "Export an image into Microsoft PowerPoint or Google Slides.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to image to export"},
                "target": {
                    "type": "string",
                    "enum": ["powerpoint", "google_slides", "clipboard"],
                    "description": "Export destination"
                },
                "title": {"type": "string", "description": "Optional step title to insert onto the slide"},
                "template": {"type": "string", "description": "Optional .pptx template path for new presentations"}
            },
            "required": ["input_path"]
        }
    },
    {
        "name": "manual_studio_create_step",
        "description": "High-level all-in-one action: captures screen region, overlays annotations, and exports to presentation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rect": {"type": "string", "description": "Screen bounding box 'x,y,w,h' or 'fixed'"},
                "monitor": {"type": "integer", "description": "Monitor index (0=Primary)"},
                "annotations": {
                    "type": "object",
                    "properties": {
                        "stamps": {"type": "array", "items": {"type": "string"}},
                        "boxes": {"type": "array", "items": {"type": "string"}},
                        "arrows": {"type": "array", "items": {"type": "string"}},
                        "elbows": {"type": "array", "items": {"type": "string"}},
                        "callouts": {"type": "array", "items": {"type": "string"}},
                        "texts": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "export_target": {
                    "type": "string",
                    "enum": ["powerpoint", "google_slides", "clipboard", "none"],
                    "description": "Destination presentation"
                },
                "step_title": {"type": "string", "description": "Step title in presentation"}
            }
        }
    },
    {
        "name": "manual_studio_batch_pipeline",
        "description": "Execute a declarative multi-step manual workflow JSON, generating screenshots, annotations, and Markdown/HTML documentation in a single call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_path": {"type": "string", "description": "File path to workflow JSON"},
                "workflow_data": {"type": "object", "description": "Direct workflow JSON object with title and steps"},
                "output_dir": {"type": "string", "description": "Output directory for generated screenshots and documentation"},
                "format": {"type": "string", "enum": ["all", "md", "html", "markdown"], "description": "Output document format (default: all)"},
                "title": {"type": "string", "description": "Manual title"}
            }
        }
    },
    {
        "name": "manual_studio_add_spotlight",
        "description": "Apply a spotlight focus mask that darkens the background while highlighting a specific UI bounding box.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Source image path"},
                "rect": {"type": "string", "description": "Bounding box to highlight in 'x,y,w,h' format"},
                "border_color": {"type": "string", "description": "Highlight border color (default #007AFF)"},
                "dim_opacity": {"type": "integer", "description": "Background dimming opacity 0-255 (default 160)"},
                "output_path": {"type": "string", "description": "Destination PNG path"}
            },
            "required": ["input_path", "rect"]
        }
    },
    {
        "name": "manual_studio_export_document",
        "description": "Export step images and descriptions into a clean Markdown or standalone interactive HTML manual.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "image_file": {"type": "string"}
                        },
                        "required": ["title", "image_file"]
                    },
                    "description": "List of manual steps"
                },
                "output_path": {"type": "string", "description": "Target file path (.md or .html)"},
                "format": {"type": "string", "enum": ["md", "html", "markdown"], "description": "Document format"},
                "title": {"type": "string", "description": "Manual title"}
            },
            "required": ["steps", "output_path"]
        }
    }
]


class MCPServer:
    """단일 프로세스 stdio JSON-RPC 2.0 MCP 프로토콜 핸들러"""

    def __init__(self):
        self.running = True

    def log(self, msg: str):
        sys.stderr.write(f"[ManualStudio-MCP] {msg}\n")
        sys.stderr.flush()

    def send_response(self, resp: dict):
        line = json.dumps(resp, ensure_ascii=False)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def handle_request(self, req: dict):
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION
                    }
                }
            })
            return

        elif method == "notifications/initialized":
            # 클라이언트 초기화 완료 통지
            return

        elif method == "ping":
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            })
            return

        elif method == "tools/list":
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS_SPEC
                }
            })
            return

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                res_data = self.execute_tool(tool_name, tool_args)
                self.send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(res_data, indent=2, ensure_ascii=False)
                            }
                        ],
                        "isError": res_data.get("status") == "error"
                    }
                })
            except Exception as e:
                self.log(f"Error executing tool {tool_name}: {traceback.format_exc()}")
                self.send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
                })
            return

        else:
            # 알 수 없는 메서드
            if req_id is not None:
                self.send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })

    def execute_tool(self, name: str, args: dict) -> dict:
        if name == "manual_studio_status":
            return cli_status()

        elif name == "manual_studio_capture_screen":
            rect = args.get("rect")
            monitor = int(args.get("monitor", 0))
            fixed = bool(args.get("fixed", False))
            out = args.get("output_path")
            return cli_capture(rect=rect, monitor=monitor, fixed=fixed, output=out)

        elif name == "manual_studio_add_annotations":
            return cli_annotate(
                input_path=args.get("input_path"),
                output_path=args.get("output_path"),
                stamps=args.get("stamps"),
                boxes=args.get("boxes"),
                arrows=args.get("arrows"),
                elbows=args.get("elbows"),
                callouts=args.get("callouts"),
                texts=args.get("texts"),
                raw_items=args.get("raw_items")
            )

        elif name == "manual_studio_render_project":
            return cli_render_project(
                project_path=args.get("project_path"),
                output_path=args.get("output_path"),
                export_ppt=bool(args.get("export_ppt", False)),
                export_slides=bool(args.get("export_slides", False))
            )

        elif name == "manual_studio_export_presentation":
            return cli_export(
                input_path=args.get("input_path"),
                target=args.get("target", "powerpoint"),
                title=args.get("title"),
                template=args.get("template")
            )

        elif name == "manual_studio_batch_pipeline":
            wf_path = args.get("workflow_path")
            wf_data = args.get("workflow_data")
            out_dir = args.get("output_dir")
            fmt = args.get("format", "all")
            title = args.get("title")

            if wf_data and not wf_path:
                import tempfile
                with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
                    json.dump(wf_data, tf)
                    wf_path = tf.name

            if not wf_path or not os.path.exists(wf_path):
                return {"status": "error", "message": "Valid workflow_path or workflow_data is required"}

            return cli_batch(workflow_path=wf_path, output_dir=out_dir, doc_format=fmt, title=title)

        elif name == "manual_studio_add_spotlight":
            in_p = args.get("input_path")
            r = args.get("rect")
            b_col = args.get("border_color", "#007AFF")
            op = args.get("dim_opacity", 160)
            out_p = args.get("output_path")
            sp_spec = f"{r}:{b_col}:{op}:2"
            return cli_annotate(input_path=in_p, output_path=out_p, spotlights=[sp_spec])

        elif name == "manual_studio_export_document":
            from manual_capture_studio import ExportEngine
            steps_list = args.get("steps", [])
            out_p = args.get("output_path")
            fmt = args.get("format", "md").lower()
            doc_title = args.get("title", "Manual Guide")
            if fmt in ("md", "markdown"):
                res_path = ExportEngine.export_to_markdown(steps_list, out_p, title=doc_title)
            else:
                res_path = ExportEngine.export_to_html(steps_list, out_p, title=doc_title)
            return {"status": "ok", "output_file": os.path.abspath(res_path), "total_steps": len(steps_list)}

        elif name == "manual_studio_create_step":
            # 올인원 복합 액션: 캡처 -> 주석 -> 내보내기
            rect_arg = args.get("rect", "fixed")
            is_fixed = (rect_arg == "fixed")
            rect_val = None if is_fixed else rect_arg
            mon = int(args.get("monitor", 0))

            cap_res = cli_capture(rect=rect_val, monitor=mon, fixed=is_fixed)
            if cap_res.get("status") != "ok":
                return cap_res

            raw_file = cap_res["output_file"]
            ann_spec = args.get("annotations", {})

            ann_res = cli_annotate(
                input_path=raw_file,
                stamps=ann_spec.get("stamps"),
                boxes=ann_spec.get("boxes"),
                arrows=ann_spec.get("arrows"),
                elbows=ann_spec.get("elbows"),
                callouts=ann_spec.get("callouts"),
                texts=ann_spec.get("texts")
            )
            if ann_res.get("status") != "ok":
                return ann_res

            final_file = ann_res["output_file"]
            export_target = args.get("export_target", "none")
            step_title = args.get("step_title")

            exp_res = None
            if export_target and export_target != "none":
                exp_res = cli_export(input_path=final_file, target=export_target, title=step_title)

            return {
                "status": "ok",
                "raw_capture": raw_file,
                "annotated_image": final_file,
                "items_applied": ann_res.get("items_applied", 0),
                "export_result": exp_res
            }

        else:
            return {"status": "error", "message": f"Unknown tool: {name}"}

    def run(self):
        self.log(f"Starting {SERVER_NAME} v{SERVER_VERSION} on stdio...")
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                req = json.loads(line)
                self.handle_request(req)
            except Exception as e:
                self.log(f"Unhandled loop error: {e}")


def run_mcp_server():
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    run_mcp_server()
