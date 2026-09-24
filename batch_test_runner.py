import sys
import time
import os
import test_core_engine

TEST_FUNCTIONS = [
    # Group 1: Core config & base items
    "test_config_loader",
    "test_circle_char",
    "test_resize_logic",
    "test_dib_generation",
    "test_backup_file_creation",
    "test_fixed_rect_config",
    "test_text_label_rendering",
    "test_toolbar_settings_and_selection_sync",
    "test_ppt_layout_and_fit",
    "test_arrow_item_and_sync",
    "test_five_recommended_annotation_items",
    "test_ribbon_menu_and_quick_strip",
    "test_annotation_serialization",
    "test_project_manager_save_and_load",
    "test_auto_backup_step_bundle_and_delete",
    "test_image_overlay_item_and_sub_capture",
    "test_draft_stamp_item",
    "test_powerpoint_step_renumbering",
    "test_dragon_rpa_branding_and_about_dialog",
    "test_license_validator",

    # Group 2: Font, Monitor, License, Watermark, Dynamic UI
    "test_custom_font_manager",
    "test_multi_monitor_manager",
    "test_elbow_arrow_four_directions_and_toggle",
    "test_wordart_item_and_presets",
    "test_global_i18n_manager",
    "test_license_engine_and_verification",
    "test_watermark_in_composed_image",
    "test_custom_watermark_configuration_and_rendering",
    "test_licensed_info_display_and_masking",
    "test_instant_capture_mouse_release",
    "test_autosave_and_recovery",
    "test_version_comparator",
    "test_version_json_schema",
    "test_patcher_script_generation",
    "test_dynamic_language_retranslation",
    "test_compact_ui_button_labels",
    "test_multilingual_tooltips_completeness",
    "test_multilingual_eula_manager",
    "test_ribbon_overhaul_and_slim_layout",
    "test_autosave_toggle_and_ribbon_integration",
    "test_ribbon_display_mode_toggle_and_icon_provider",
    "test_all_shortcuts_and_alt_keytips",
    "test_dialog_multilingual_localization",
    "test_google_slides_integration",
    "test_ui_theme_styles_windows_and_macos",
    "test_ai_agent_cli_and_mcp_server",
    "test_ai_agent_advanced_annotations_batch_and_doc_export",

    # Group 3: Offline licensing, OCR, Dimension, Phase 1~8
    "test_cache_token_save_load",
    "test_grace_period_logic",
    "test_offline_lic_file_verify",
    "test_hybrid_license_flow_offline",
    "test_ocr_i18n_keys",
    "test_dimension_line_item",
    "test_stamp_item_rounded_rect_shape",
    "test_item_properties_dialog_and_sync",
    "test_dimension_and_properties_i18n_keys",
    "test_box_dimension_and_ocr_labels_and_ghost_fix",
    "test_ocr_smart_preprocessing",
    "test_phase1_window_frame_and_shadow",
    "test_phase1_hwp_com_and_hotkey",
    "test_phase1_filmstrip_storyboard_and_i18n",
    "test_phase2_animated_gif_export",
    "test_phase2_webbook_export_and_i18n",
    "test_phase3_pii_patterns_and_detection",
    "test_phase3_smart_cleanup_and_undo",
    "test_phase3_canvas_auto_pii_and_window_buttons",
    "test_phase4_magnetic_snap_engine",
    "test_phase4_scroll_stitch_engine",
    "test_phase4_action_recorder_and_i18n",
    "test_phase5_export_menu_storyboard_and_pii_custom_rules",
    "test_phase6_multi_selection_and_f10_slide",
    "test_phase7_pii_synthesizer_and_storyboard_toolbar_overhaul",
    "test_phase8_project_level_architecture_and_exports",

    # Group 4: Phase 9~18
    "test_phase9_release_notes_ribbon_icons_function_keys_and_updater",
    "test_phase10_full_audit_all_items_and_canvas_sync",
    "test_phase11_flowchart_magnet_mermaid_and_markitdown_dock",
    "test_phase12_enterprise_exports_and_transparent_canvas",
    "test_phase13_sticky_tools_f8_standalone_and_flowchart_manual_shapes",
    "test_phase14_action_recorder_deprecated_and_flowchart_connectors_and_db_shape",
    "test_phase15_lucide_vector_icons_and_emoji_purge",
    "test_phase16_multi_monitor_virtual_desktop_capture",
    "test_phase17_flowchart_intelligent_auto_align",
    "test_phase18_flowchart_intelligent_obstacle_avoidance_routing",
]

def run_group(start_idx, end_idx):
    subset = TEST_FUNCTIONS[start_idx:end_idx]
    total = len(subset)
    print(f"\n=== Running Tests [{start_idx+1}..{min(end_idx, len(TEST_FUNCTIONS))}] ({total} tests) ===", flush=True)

    passed = 0
    failed = 0

    for i, fn_name in enumerate(subset, start=start_idx+1):
        fn = getattr(test_core_engine, fn_name, None)
        if not fn:
            print(f"[{i}/{len(TEST_FUNCTIONS)}] [SKIP] {fn_name}: not found in module", flush=True)
            continue

        t0 = time.time()
        print(f"[{i}/{len(TEST_FUNCTIONS)}] RUNNING {fn_name}...", end="", flush=True)
        try:
            fn()
            dt = time.time() - t0
            print(f" -> [PASS] ({dt:.2f}s)", flush=True)
            passed += 1
        except Exception as e:
            dt = time.time() - t0
            print(f" -> [FAIL] ({dt:.2f}s): {e}", flush=True)
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nGroup Result: {passed} passed, {failed} failed (out of {total})\n", flush=True)
    return failed == 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", type=int, choices=[1, 2, 3, 4], help="Run specific group (1-4)")
    parser.add_argument("--range", type=str, help="Run index range, e.g. 0:20")
    parser.add_argument("--name", type=str, help="Run single test by name")
    args = parser.parse_args()

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    if args.name:
        fn = getattr(test_core_engine, args.name, None)
        if fn:
            print(f"Running single test: {args.name}", flush=True)
            fn()
            print("PASS", flush=True)
        else:
            print(f"Test {args.name} not found", flush=True)
        os._exit(0)

    groups = {
        1: (0, 20),
        2: (20, 47),
        3: (47, 72),
        4: (72, len(TEST_FUNCTIONS))
    }

    if args.group:
        s, e = groups[args.group]
        ok = run_group(s, e)
        os._exit(0 if ok else 1)
    elif args.range:
        parts = args.range.split(":")
        s, e = int(parts[0]), int(parts[1])
        ok = run_group(s, e)
        os._exit(0 if ok else 1)
    else:
        all_ok = True
        for g in [1, 2, 3, 4]:
            s, e = groups[g]
            ok = run_group(s, e)
            if not ok:
                all_ok = False
        os._exit(0 if all_ok else 1)
