import ctypes
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, ttk

try:
    from hotkey_service import label as hotkey_label
except Exception:
    def hotkey_label(combo):
        return str(combo)

from detector import start_hud_evidence


PALETTE_KEYS = (
    "BG", "CARD", "CARD2", "BORDER", "TEXT", "MUTED",
    "ACCENT", "GREEN", "RED", "AMBER", "BUTTON", "BUTTON_HOVER", "INPUT",
)

PALETTES = {
    "purple": {
        "BG": "#18181C", "CARD": "#202027", "CARD2": "#26262E",
        "BORDER": "#303038", "TEXT": "#F4F1FC", "MUTED": "#9A9AA8",
        "ACCENT": "#A78BFA", "GREEN": "#4ADE80", "RED": "#F87171",
        "AMBER": "#FBBF24", "BUTTON": "#34343C", "BUTTON_HOVER": "#4A4A54",
        "INPUT": "#2A2A32",
    },
    "red": {
        "BG": "#1A1113", "CARD": "#24171A", "CARD2": "#2C1C20",
        "BORDER": "#44282D", "TEXT": "#FDF1F2", "MUTED": "#C0A0A6",
        "ACCENT": "#EF4444", "GREEN": "#4ADE80", "RED": "#F87171",
        "AMBER": "#FBBF24", "BUTTON": "#3C2529", "BUTTON_HOVER": "#553237",
        "INPUT": "#2F1D21",
    },
    "killer": {
        "BG": "#160F1D", "CARD": "#21152B", "CARD2": "#2A1B36",
        "BORDER": "#432A52", "TEXT": "#FFF1F8", "MUTED": "#C2A5CA",
        "ACCENT": "#F06EAE", "GREEN": "#7DE3B4", "RED": "#FF6B7A",
        "AMBER": "#F6C85F", "BUTTON": "#372145", "BUTTON_HOVER": "#4E2F5E",
        "INPUT": "#2A1936",
    },
}

PROFILES = {
    "486回归音效": {
        "name": "从零开始的塔科夫生活",
        "palette": "purple",
        "icon": "first_icon.ico",
    },
    "杀手皇后第三炸弹败者食尘": {
        "name": "Another One Bites the Dust",
        "palette": "killer",
        "icon": "killer_queen.ico",
    },
    "宇智波鼬 · 幻术": {
        "name": "月読",
        "palette": "red",
        "icon": "itachi_mangekyo.ico",
    },
}
DEFAULT_PROFILE = "486回归音效"

# Game-interface designations use an alternate TKF-style series. The letter
# keeps the mapping to the interface document, while the numeric prefix makes
# the header read like a task-force designation.
IFACE_TKF = {
    "A": "TKF-7314-A",
    "B": "TKF-7314-B",
    "C": "TKF-7314-C",
    "D": "TKF-7314-D",
    "E": "TKF-7314-E",
    "F": "TKF-7314-F",
    "G": "TKF-7314-G",
    "O": "TKF-7314-O",
    "P": "TKF-7314-P",
    "Q": "TKF-7314-Q",
    "N": "TKF-7314-N",
    "S": "TKF-7314-S",
    "K": "TKF-7314-K",
    "H": "TKF-7314-H",
    "X": "TKF-7314-X",
    "0": "TKF-7314-0",
}
IFACE_NAMES = {
    "A": ("无武装战局", "Unarmed raid HUD"),
    "B": ("装备 / 背包", "Gear / inventory"),
    "C": ("总览", "Overview"),
    "D": ("健康", "Health"),
    "E": ("技能", "Skills"),
    "F": ("地图", "Map"),
    "G": ("任务", "Quests"),
    "O": ("成就", "Achievements"),
    "P": ("控制台", "Console"),
    "Q": ("游戏主页", "Game home"),
    "N": ("撤离点", "Extraction"),
    "S": ("设置", "Settings"),
    "K": ("确认", "Confirmation"),
    "H": ("转生 / 未识别页签", "Prestige / unlisted tab"),
    "X": ("战斗 HUD", "Combat HUD"),
    "0": ("未识别", "Unrecognized"),
}
IFACE_SAFE = frozenset("ABCDEFGOPQSKH")

_VK = {"space": 32, "tab": 9, "Return": 13, "BackSpace": 8}
_LABELS = {"space": "Space", "Return": "Enter", "BackSpace": "Backspace"}


def _vk_for(keysym):
    if len(keysym) == 1 and keysym.isalnum():
        return ord(keysym.upper())
    if keysym.startswith("F") and keysym[1:].isdigit():
        number = int(keysym[1:])
        return 111 + number if 1 <= number <= 12 else None
    return _VK.get(keysym)


def _label_for(keysym):
    return _LABELS.get(keysym) or (keysym.upper() if len(keysym) == 1 else keysym)


def _game_foreground():
    target = getattr(sys.modules.get("__main__"), "target", None)
    try:
        return bool(target and target())
    except Exception:
        return False


def _send_key(vk, up):
    main = sys.modules.get("__main__")
    user32 = getattr(main, "U", None)
    input_type = getattr(main, "INPUT", None)
    if user32 is None or input_type is None:
        return False
    try:
        event = input_type()
        event.type = 1
        key = event.u.ki
        key.wVk = vk
        key.wScan = 0
        key.dwFlags = 2 if up else 0
        key.time = 0
        key.dwExtraInfo = 0
        return user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(input_type)) == 1
    except Exception:
        return False


def _modifiers_down():
    user32 = getattr(sys.modules.get("__main__"), "U", None)
    if user32 is None:
        return True
    try:
        return any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in (16, 17, 18, 91, 92))
    except Exception:
        return True


def _set_palette_globals(name):
    global BG, CARD, CARD2, BORDER, TEXT, MUTED
    global ACCENT, GREEN, RED, AMBER, BUTTON, BUTTON_HOVER, INPUT
    palette = PALETTES[name]
    BG = palette["BG"]
    CARD = palette["CARD"]
    CARD2 = palette["CARD2"]
    BORDER = palette["BORDER"]
    TEXT = palette["TEXT"]
    MUTED = palette["MUTED"]
    ACCENT = palette["ACCENT"]
    GREEN = palette["GREEN"]
    RED = palette["RED"]
    AMBER = palette["AMBER"]
    BUTTON = palette["BUTTON"]
    BUTTON_HOVER = palette["BUTTON_HOVER"]
    INPUT = palette["INPUT"]


_set_palette_globals("purple")
FONT = "Microsoft YaHei UI"
RELEASE_LANGUAGE_DEFAULT = "zh"
RELEASE_NAME = "正式版"
RELEASE_NAME_EN = "Official Release"

TEXTS = {
    "zh": {
        "lang_button": "EN",
        "release_suffix": f" · {RELEASE_NAME}",
        "about_version": "",
        "tab_prep": "战前准备",
        "tab_advanced": "进阶设置",
        "tab_diag": "日志诊断",
        "sound": "音效",
        "preview": "试听",
        "import": "导入",
        "hotkey": "快捷键",
        "check": "检测",
        "test_mode": "测试模式（只记录，不发送 Alt+F4）",
        "test_mode_short": "测试",
        "normal_mode_short": "正常",
        "ready": "就绪",
        "standby_badge": "待机",
        "start_monitor": "开始监控",
        "stop_monitor": "停止监控",
        "log": "日志",
        "test_warning": "只记录候选，不发送按键",
        "normal_warning": "正常模式：满足条件后将自动发送 Alt+F4",
        "choose_sound": "选择音效",
        "audio_files": "音频文件",
        "all_files": "所有文件",
        "sound_toggles": "音效开关",
        "start_sound": "启动音",
        "stop_sound": "关闭音",
        "exit_sound": "音效",
        "mute_all": "全部静音",
        "detection": "检测参数",
        "delay_ms": "延时(ms)",
        "sampling": "采样",
        "resolution": "分辨率",
        "detection_hint": "延时 50–2000ms · 采样 15/30/60Hz · 分辨率留空=自动",
        "auto_key": "自动按键",
        "enabled": "启用",
        "interval": "间隔",
        "seconds": "秒",
        "key": "按键",
        "auto_hint": "游戏前台且 HUD 就绪时生效；就绪后立即按一次，\n之后按间隔重复；修饰键按住时跳过",
        "diag_capture": "诊断采集",
        "save_shots": "保存顶部截图（仅候选附近，最多 2 组）",
        "collect_logs": "收集进程日志（含详细分数）",
        "save_settings": "保存设置",
        "runtime_status": "运行状态",
        "open_log": "打开日志",
        "refresh": "刷新",
        "recent_events": "最近事件",
        "about": "关于",
        "about_hint": "仅本地 PvE · 视觉识别 · 不注入内存",
        "no_events": "暂无事件",
        "admin_title": "管理员权限",
        "admin_message": "Alt+F4 和自动按键需要管理员权限，否则可能被 Windows 拦截。\n\n是否以管理员身份重新启动？",
        "admin_denied": "未获得管理员权限，已继续以普通权限运行",
        "admin_restart_failed": "无法自动重启，请右键以管理员身份运行",
        "auto_feedback_on_initial": "已启用 · HUD 就绪后立即按一次",
        "auto_feedback_off_initial": "未启用 · 默认关闭",
        "auto_recording": "按任意键…",
        "auto_interval_error": "间隔需在 1–3600 秒",
        "auto_enabled_feedback": "已启用 · HUD 就绪后立即按 {key}，之后每 {seconds} 秒",
        "auto_disabled_feedback": "未启用",
        "save_failed": "保存失败：{exc}",
        "auto_record_prompt": "请按一个普通按键，Esc 取消",
        "auto_record_canceled": "已取消按键录制",
        "auto_record_unsupported": "不支持该键，请选择普通按键",
        "auto_record_f12": "F12 保留给诊断截图，请换一个",
        "auto_record_same_hotkey": "与监控快捷键相同，请换一个",
        "auto_record_selected": "已选择 {key}；HUD 就绪后生效",
        "auto_foreground_paused": "游戏未前台 · 已暂停",
        "auto_hud_wait": "等待 HUD/血量人形/快捷栏就绪 · 已暂停",
        "auto_hud_ready": "HUD 就绪 · 每 {seconds} 秒按 {key}",
        "auto_running": "运行中 · 已按 {key} {count} 次",
        "auto_send_failed": "按键发送失败",
        "auto_interval_save_error": "自动按键间隔需在 1–3600 秒",
        "invalid_delay_sampling": "延时或采样设置无效，请检查",
        "invalid_resolution": "分辨率格式应为 宽x高，如 2560x1600",
        "settings_saved": "设置已保存",
        "hotkey_change_failed": "快捷键修改失败：{exc}",
        "hotkey_in_use_unchanged": "该快捷键已被占用，未修改",
        "hotkey_return_hint": "回到游戏后按 {key} 开启，再按一次停止",
        "hotkey_changed_save_failed": "快捷键已切换，但保存失败：{exc}",
        "hotkey_in_use_current": "{key} 正在使用中",
        "hotkey_check_failed": "检测失败：{exc}",
        "hotkey_available": "{key} 可用",
        "hotkey_occupied": "{key} 已被其他程序占用",
        "notice_tip": "{key} 开启/关闭",
    },
    "en": {
        "lang_button": "中",
        "release_suffix": f" · {RELEASE_NAME_EN}",
        "about_version": "",
        "tab_prep": "Prep",
        "tab_advanced": "Advanced",
        "tab_diag": "Diagnostics",
        "sound": "Sound",
        "preview": "Preview",
        "import": "Import",
        "hotkey": "Hotkey",
        "check": "Check",
        "test_mode": "Test mode (record only, no Alt+F4)",
        "test_mode_short": "TEST",
        "normal_mode_short": "LIVE",
        "ready": "READY",
        "standby_badge": "IDLE",
        "start_monitor": "Start monitoring",
        "stop_monitor": "Stop monitoring",
        "log": "Log",
        "test_warning": "Records candidates only; no keys are sent",
        "normal_warning": "Normal mode: Alt+F4 will be sent when conditions are met",
        "choose_sound": "Select sound",
        "audio_files": "Audio files",
        "all_files": "All files",
        "sound_toggles": "Sound toggles",
        "start_sound": "Start sound",
        "stop_sound": "Stop sound",
        "exit_sound": "Exit sound",
        "mute_all": "Mute all",
        "detection": "Detection",
        "delay_ms": "Delay (ms)",
        "sampling": "Sampling",
        "resolution": "Resolution",
        "detection_hint": "Delay 50–2000 ms · Sampling 15/30/60 Hz · Blank resolution = auto",
        "auto_key": "Auto key",
        "enabled": "Enabled",
        "interval": "Interval",
        "seconds": "sec",
        "key": "Key",
        "auto_hint": "Active only when the game is focused and the HUD is ready. Presses once immediately, then at each interval; skipped while modifiers are held.",
        "diag_capture": "Diagnostics capture",
        "save_shots": "Save HUD screenshots (max 2 near candidates)",
        "collect_logs": "Collect process logs (with detailed scores)",
        "save_settings": "Save settings",
        "runtime_status": "Status",
        "open_log": "Open log",
        "refresh": "Refresh",
        "recent_events": "Recent events",
        "about": "About",
        "about_hint": "Local PvE only · Visual detection · No memory injection",
        "no_events": "No events yet",
        "admin_title": "Administrator permission",
        "admin_message": "Alt+F4 and auto keys need administrator permission, otherwise Windows may block them.\n\nRestart as administrator?",
        "admin_denied": "Administrator permission was not granted; continuing without elevation",
        "admin_restart_failed": "Could not restart automatically; right-click and run as administrator",
        "auto_feedback_on_initial": "Enabled · presses once when the HUD becomes ready",
        "auto_feedback_off_initial": "Disabled · off by default",
        "auto_recording": "Press any key…",
        "auto_interval_error": "Interval must be 1–3600 seconds",
        "auto_enabled_feedback": "Enabled · press {key} when the HUD is ready, then every {seconds} s",
        "auto_disabled_feedback": "Disabled",
        "save_failed": "Save failed: {exc}",
        "auto_record_prompt": "Press a normal key; Esc to cancel",
        "auto_record_canceled": "Key recording canceled",
        "auto_record_unsupported": "That key is not supported; choose a normal key",
        "auto_record_f12": "F12 is reserved for diagnostic screenshots; choose another",
        "auto_record_same_hotkey": "Same as the monitoring hotkey; choose another",
        "auto_record_selected": "{key} selected; active when the HUD is ready",
        "auto_foreground_paused": "Game not focused · paused",
        "auto_hud_wait": "Waiting for HUD/body/hotbar · paused",
        "auto_hud_ready": "HUD ready · pressing {key} every {seconds} s",
        "auto_running": "Running · pressed {key} {count} times",
        "auto_send_failed": "Key send failed",
        "auto_interval_save_error": "Auto-key interval must be 1–3600 seconds",
        "invalid_delay_sampling": "Invalid delay or sampling; check the values",
        "invalid_resolution": "Resolution must be WIDTHxHEIGHT, e.g. 2560x1600",
        "settings_saved": "Settings saved",
        "hotkey_change_failed": "Hotkey change failed: {exc}",
        "hotkey_in_use_unchanged": "Hotkey is already in use; unchanged",
        "hotkey_return_hint": "Press {key} after returning to the game to start; press again to stop",
        "hotkey_changed_save_failed": "Hotkey changed, but saving failed: {exc}",
        "hotkey_in_use_current": "{key} is already active",
        "hotkey_check_failed": "Check failed: {exc}",
        "hotkey_available": "{key} is available",
        "hotkey_occupied": "{key} is used by another program",
        "notice_tip": "{key} on/off",
    },
}

PROFILE_NAMES_EN = {
    "486回归音效": "From Zero to Tarkov Life",
    "杀手皇后第三炸弹败者食尘": "Another One Bites the Dust",
    "宇智波鼬 · 幻术": "Tsukuyomi",
}

SOUND_NAMES_EN = {
    "486回归音效": "486 Return Sound",
    "轻提示 · 开启": "Soft cue · On",
    "轻提示 · 关闭": "Soft cue · Off",
    "电子回溯": "Electronic Rewind",
    "杀手皇后第三炸弹败者食尘": "Killer Queen · Bites the Dust",
    "塔科夫任务完成电音": "Tarkov Quest Complete",
    "宇智波鼬 · 幻术": "Itachi · Illusion",
}

EVENT_NAMES_ZH = {
    "status": "状态",
    "scores": "分数",
    "armed": "已开启",
    "disarmed": "已停止",
    "startup": "启动",
    "focus_paused": "失焦暂停",
    "focus_resumed": "恢复前台",
    "candidate_trigger": "候选触发",
    "extraction_transition": "撤离过渡",
    "absence_reset": "HUD 恢复",
    "diagnostic_saved": "诊断已保存",
    "status_feedback": "状态",
    "sound_imported": "音效导入",
    "hotkey": "快捷键",
}

EVENT_NAMES_EN = {
    "status": "Status",
    "scores": "Scores",
    "armed": "Armed",
    "disarmed": "Stopped",
    "startup": "Startup",
    "focus_paused": "Focus lost",
    "focus_resumed": "Focus back",
    "candidate_trigger": "Candidate",
    "extraction_transition": "Extraction",
    "absence_reset": "HUD recovered",
    "diagnostic_saved": "Diagnostics",
    "status_feedback": "Status",
    "sound_imported": "Sound",
    "hotkey": "Hotkey",
}

DYNAMIC_EN = {
    "塔科夫助手 · ": "Tarkov Assistant · ",
    " 开启/关闭": " on/off",
    "监控中": "Monitoring",
    "已发送一次 Alt+F4": "Alt+F4 sent once",
    "未发送：Shift/Ctrl/Alt/Win 正被按住": "Not sent: Shift/Ctrl/Alt/Win is held",
    "未发送：游戏已失去前台": "Not sent: game lost foreground",
    "输入未完整发送（按下 ": "Input not fully sent (down ",
    "/2，松开 ": "/2, up ",
    "/2），已停止，不重试": "/2). Stopped; no retry.",
    "已发送一次 Alt+F4；是否退出/回档需自行确认": "Alt+F4 sent once; confirm the game exit/result yourself",
    "塔科夫助手": "Tarkov Assistant",
    "回到游戏后按 ": "After returning to the game, press ",
    " 开启，再按一次停止": " to start, press again to stop",
    "已关闭 · 进入战局、HUD 可见后按 ": "Stopped · Enter a raid and press ",
    "等待开启": "Waiting to start",
    "截图默认关闭；手动开启后仅候选附近保存，最多2组 / 32MB": "Screenshots are off by default; when enabled, only near candidates, max 2 sets / 32 MB",
    "快捷键 ": "Hotkey ",
    " 已被占用，请点击快捷键设置选择其他按键": " is already in use; choose another hotkey",
    "未启动": "Not started",
    "WAV / MP3 / FLAC / OGG · 50MB / 60秒以内": "WAV / MP3 / FLAC / OGG · up to 50 MB / 60 s",
    "模式已切换，请重新开启": "Mode changed; start monitoring again",
    "音效与快捷键已保存": "Sound and hotkey saved",
    "保存失败，请检查设置或目录写入权限": "Save failed; check settings or folder write permission",
    "进阶自定义设置已保存": "Advanced settings saved",
    "保存失败：延时需为50–2000毫秒，采样为15/30/60 Hz": "Save failed: delay must be 50–2000 ms; sampling 15/30/60 Hz",
    "延时设置": "Delay",
    "持续缺失多少毫秒后触发（50–2000）": "Trigger after HUD is missing for this many ms (50–2000)",
    "尚未保存": "Not saved",
    "音效设置 · 二级界面待定": "Sound settings · secondary page pending",
    "当前保留现有功能入口，二级布局待确认": "Current controls are kept; secondary layout is pending",
    "试听": "Preview",
    "导入": "Import",
    "停止试听": "Stop preview",
    "静音模式已开启，请关闭静音并保存后再试听": "Mute is on; turn it off and save before previewing",
    "播放失败，请重新选择或导入音效": "Playback failed; choose or import another sound",
    "音效已即时生效 · 保存后下次保留": "Sound applied · save to keep it next time",
    "保存失败，请检查程序目录写入权限": "Save failed; check write permission for the program folder",
    "快捷键设置中，保存后需重新开启": "Hotkey changed; restart monitoring after saving",
    "监控开启 / 关闭快捷键": "Monitoring start/stop hotkey",
    "灰色删除线：当前无法注册；保存前再次检查": "Gray strikethrough: unavailable now; check again before saving",
    "预设快捷键": "Preset hotkeys",
    "录制自定义快捷键": "Record custom hotkey",
    "尚未录制": "Not recorded",
    "仅检测 Windows 系统热键占用，无法检测游戏内按键绑定。\n单键支持功能键/导航键；字母数字请搭配 Ctrl、Alt 或 Shift。\n录制时按 Esc 取消；F12 保留用于截图。": "Only Windows global hotkey conflicts are checked; in-game binds are not detected.\nSingle keys support function/navigation keys; combine letters/digits with Ctrl, Alt or Shift.\nPress Esc to cancel recording; F12 is reserved for screenshots.",
    "保存快捷键": "Save hotkey",
    "请按下一个按键或组合键（Esc 取消）": "Press a key or combo (Esc to cancel)",
    "已取消录制": "Recording canceled",
    "不支持 Windows 键组合，请重新录制": "Windows-key combos are not supported; record again",
    "已录制 ": "Recorded ",
    "，保存后生效": "; takes effect after saving",
    "系统热键检查超时，请关闭设置后重试": "System hotkey check timed out; close settings and retry",
    "该快捷键已被占用，未修改原快捷键": "Hotkey is in use; original hotkey unchanged",
    "已关闭 · 快捷键已设为 ": "Stopped · Hotkey set to ",
    "，请回到游戏后开启": "; start again after returning to the game",
    "选择音效（最多60秒 / 50MB）": "Select sound (max 60 s / 50 MB)",
    "每次请拖入一个音频文件": "Drop one audio file at a time",
    "正在导入，请稍候": "Importing; please wait",
    "请先按快捷键停止监控，再导入音频": "Stop monitoring with the hotkey before importing audio",
    "正在转换音频，完成后自动保存…": "Converting audio; it will be saved automatically…",
    "已即时生效，保存后下次保留": "Applied now; save to keep it next time",
    "延时或采样值无效": "Invalid delay or sampling value",
    "已关闭 · ": "Stopped · ",
    "音频转换完成后即可开启监控": "Monitoring can start when audio conversion finishes",
    " 关闭": " off",
    "前台进程/窗口检查未通过": "Foreground process/window check failed",
    "采集暂时没有画面，请保持游戏前台，稍后重新按快捷键": "No frames captured; keep the game in the foreground and press the hotkey again",
    "首次开启需要稳定战斗HUD，菜单不能单独开启": "First start requires a stable combat HUD; the menu alone cannot start it",
    "未观察到稳定战斗HUD，请在血量人形与快捷栏可见时开启": "No stable combat HUD found; start when the body figure and hotbar are visible",
    "监控中 · ": "Monitoring · ",
    "只记录，不退出": "record only, no exit",
    "战斗 HUD 和菜单均消失并超过设定延时才退出": "exit only after both combat HUD and menu are gone past the delay",
    "超过 0.75 秒无新画面": "No new frames for over 0.75 s",
    "采集区域尺寸改变": "Capture region size changed",
    "战局特征 ": "Raid cues ",
    " · 人形轮廓 ": " · Body ",
    " · 快捷栏 ": " · Hotbar ",
    " · 菜单 ": " · Menu ",
    "识别到撤离结束过渡，停止监控（未发送 Alt+F4）": "Extraction-end transition detected; monitoring stopped (Alt+F4 not sent)",
    "只记录：已检测到 UI 消失，未发送按键": "Record only: UI absence detected; no key sent",
    "采集/检测错误：": "Capture/detection error: ",
    "退出确认中 · 3 秒后进程仍在运行，继续观察至 30 秒": "Confirming exit · process still running after 3 s; watching up to 30 s",
    "已确认游戏进程退出 · 回档结果需自行确认": "Game process exit confirmed · confirm the raid result yourself",
    "退出未确认 · 发送后 30 秒游戏进程仍在运行": "Exit unconfirmed · game process still running 30 s after sending",
    "无法确认游戏退出 · 进程观察不可用": "Cannot confirm game exit · process observation unavailable",
    "已导入副本并即时生效 · 保存后下次保留": "Imported copy applied · save to keep it next time",
    "音效设置保存失败，请检查目录写入权限": "Failed to save sound settings; check folder write permission",
    "导入失败：": "Import failed: ",
    "本轮停止 · ": "Round ended · ",
    "已确认": "confirmed",
    "游戏已退出": "game exited",
    "请检查退出结果": "check the exit result",
    "诊断已保存：": "Diagnostics saved: ",
    "暂停": "Paused",
    "已暂停 · 等待回到游戏": "Paused · waiting to return to game",
    "守护中 · ": "Watching · ",
    " 可停止": " to stop",
    "正在检查": "Checking",
    "正在连接战局…": "Connecting to raid…",
    "只记录：已检测到": "Record only: detected",
    "候选已记录 · 本轮停止": "Candidate recorded · round ended",
    "已发送退出 · 本轮停止": "Exit sent · round ended",
    "未开启": "Not started",
    "失败": "Failed",
    "错误": "Error",
    "未连接 · 请检查提示": "Not connected · check the message above",
    "待命 · 新的一轮": "Standby · new round",
    "已暂停 · 切回游戏后继续": "Paused · resume after switching back",
    "已开启 · ": "Active · ",
    " 可关闭": " to stop",
    "正在检查界面": "Checking UI",
    "退出按键已发送 · 正在确认游戏退出": "Exit key sent · confirming game exit",
    "演练候选已记录 · 未发送按键": "Test candidate recorded · no key sent",
    "撤离结束过渡": "Extraction-end transition",
    "撤离过渡已识别 · 监控停止": "Extraction transition detected · monitoring stopped",
    "未开启 · 请查看上方提示": "Not started · see the message above",
    "已关闭 · 等待开启": "Stopped · waiting to start",
    "程序退出": "Program exit",
    "工具已经运行，请勿重复启动。": "The tool is already running; do not start it again.",
    "HUD 监控": "HUD Monitor",
    "HUD 监控启动失败": "HUD monitor failed to start",
    "监控中 · 已切出游戏，暂停判断；切回自动继续": "Monitoring · game unfocused; paused until you return",
    "监控中 · 已回到游戏，继续判断": "Monitoring · back in game; resuming checks",
    "监控中 · 只记录，不退出": "Monitoring · record only, no exit",
    "监控中 · 战斗 HUD 和菜单均消失并超过设定延时才退出": "Monitoring · exits only after both combat HUD and menu are gone past the delay",
    "本轮停止 · 游戏已退出": "Round ended · game exited",
    "本轮停止 · 请检查退出结果": "Round ended · check the exit result",
    "自动按键间隔需在 1–3600 秒": "Auto-key interval must be 1–3600 seconds",
    "延时或采样设置无效，请检查": "Invalid delay or sampling; check the values",
    "分辨率格式应为 宽x高，如 2560x1600": "Resolution must be WIDTHxHEIGHT, e.g. 2560x1600",
    "设置已保存": "Settings saved",
    "该快捷键已被占用，未修改": "Hotkey is already in use; unchanged",
    "游戏未前台 · 已暂停": "Game not focused · paused",
    "等待 HUD/血量人形/快捷栏就绪 · 已暂停": "Waiting for HUD/body/hotbar · paused",
    "按键发送失败": "Key send failed",
    "未启用": "Disabled",
    "未启用 · 默认关闭": "Disabled · off by default",
    "已启用 · HUD 就绪后立即按一次": "Enabled · presses once when the HUD becomes ready",
    "间隔需在 1–3600 秒": "Interval must be 1–3600 seconds",
    "按任意键…": "Press any key…",
    "请按一个普通按键，Esc 取消": "Press a normal key; Esc to cancel",
    "已取消按键录制": "Key recording canceled",
    "不支持该键，请选择普通按键": "That key is not supported; choose a normal key",
    "F12 保留给诊断截图，请换一个": "F12 is reserved for diagnostic screenshots; choose another",
    "与监控快捷键相同，请换一个": "Same as the monitoring hotkey; choose another",
}


def translate_dynamic_en(text):
    if not text:
        return text
    text = str(text)
    if text in DYNAMIC_EN:
        return DYNAMIC_EN[text]

    for marker, english in (
        ("监控中 · ", "Monitoring · "),
        ("本轮停止 · ", "Round ended · "),
        ("已关闭 · ", "Stopped · "),
    ):
        if text.startswith(marker):
            return english + translate_dynamic_en(text[len(marker):])

    match = re.fullmatch(r"守护中 · (.+?) 可停止", text)
    if match:
        return f"Watching · {match.group(1)} to stop"
    match = re.fullmatch(r"已开启 · (.+?) 可关闭", text)
    if match:
        return f"Active · {match.group(1)} to stop"
    match = re.fullmatch(r"回到游戏后按 (.+?) 开启，再按一次停止", text)
    if match:
        return (
            f"press {match.group(1)} after returning to the game to start; "
            "press again to stop"
        )
    match = re.fullmatch(r"进入战局、HUD 可见后按 (.+?)(?: 开启)?", text)
    if match:
        return f"enter a raid and press {match.group(1)} when the HUD is visible"
    match = re.fullmatch(r"快捷键已设为 (.+?)，请回到游戏后开启", text)
    if match:
        return f"hotkey set to {match.group(1)}; start again after returning to the game"
    match = re.fullmatch(r"快捷键 (.+?) 已被占用，请点击快捷键设置选择其他按键", text)
    if match:
        return f"Hotkey {match.group(1)} is already in use; choose another hotkey"
    match = re.fullmatch(r"(\d+) 秒后进程仍在运行", text)
    if match:
        return f"process still running after {match.group(1)} s"
    match = re.fullmatch(r"导入失败：(.*)", text)
    if match:
        return "Import failed: " + match.group(1)
    match = re.fullmatch(r"保存失败：(.*)", text)
    if match:
        return "Save failed: " + match.group(1)
    match = re.fullmatch(r"检测失败：(.*)", text)
    if match:
        return "Check failed: " + match.group(1)
    match = re.fullmatch(r"快捷键修改失败：(.*)", text)
    if match:
        return "Hotkey change failed: " + match.group(1)
    match = re.fullmatch(r"快捷键已切换，但保存失败：(.*)", text)
    if match:
        return "Hotkey changed, but saving failed: " + match.group(1)
    match = re.fullmatch(r"诊断已保存：(.*)", text)
    if match:
        return "Diagnostics saved: " + match.group(1)
    match = re.fullmatch(r"采集/检测错误：(.*)", text)
    if match:
        return "Capture/detection error: " + match.group(1)
    match = re.fullmatch(r"(.+?) 正在使用中", text)
    if match:
        return f"{match.group(1)} is already active"
    match = re.fullmatch(r"(.+?) 可用", text)
    if match:
        return f"{match.group(1)} is available"
    match = re.fullmatch(r"(.+?) 已被其他程序占用", text)
    if match:
        return f"{match.group(1)} is used by another program"

    if text.startswith("战局特征 "):
        return (
            text.replace("战局特征 ", "Raid cues ")
            .replace(" · 人形轮廓 ", " · Body ")
            .replace(" · 快捷栏 ", " · Hotbar ")
            .replace(" · 菜单 ", " · Menu ")
        )

    match = re.fullmatch(r"已选择 (.+?)；HUD 就绪后生效", text)
    if match:
        return f"{match.group(1)} selected; active when the HUD is ready"
    match = re.fullmatch(r"HUD 就绪 · 每 (\d+) 秒按 (.+)", text)
    if match:
        return f"HUD ready · pressing {match.group(2)} every {match.group(1)} s"
    match = re.fullmatch(r"运行中 · 已按 (.+?) (\d+) 次", text)
    if match:
        return f"Running · pressed {match.group(1)} {match.group(2)} times"
    match = re.fullmatch(r"已启用 · HUD 就绪后立即按 (.+?)，之后每 (\d+) 秒", text)
    if match:
        return (
            f"Enabled · press {match.group(1)} when the HUD is ready, "
            f"then every {match.group(2)} s"
        )
    return text


class PrimaryUI:
    def __init__(self, app, assets):
        self.app = app
        self.root = app.root
        self.assets = Path(assets)
        self.key_recording = False
        self.key_choices = [(0, vk) for vk in range(112, 124)]
        self._tick = 0
        self._log_cache = ""
        self._last_sound = None
        self._current_tab = 0
        self.language = self._load_language()
        self._text_bindings = []
        self._bridges = []
        self._trace_callbacks = []
        self._sound_actual_cache = ()
        selected = self.app.sounds.selected.get("exit", "")
        self._profile_key = selected if selected in PROFILES else DEFAULT_PROFILE
        self._palette_name = PROFILES[self._profile_key]["palette"]
        _set_palette_globals(self._palette_name)
        self._configure_app_vars()
        self._configure_root()
        self._configure_style()
        self._build()
        self._apply_resolution()
        self._apply_profile(self._profile_key, initial=True)
        self._last_sound = self.exit_sound_var.get()
        self._refresh()
        self._refresh_log()
        self.root.after(400, self._admin_notice)
        self.root.after(150, self._loop)

    # ------------------------------------------------------------------- i18n
    def _load_language(self):
        try:
            values = json.loads(Path(self.app.config_path).read_text("utf-8"))
            value = str(values.get("language", RELEASE_LANGUAGE_DEFAULT)).lower()
        except Exception:
            value = RELEASE_LANGUAGE_DEFAULT
        return "en" if value.startswith("en") else "zh"

    def _t(self, key):
        table = TEXTS.get(self.language, TEXTS["zh"])
        return table.get(key, TEXTS["zh"].get(key, key))

    def _tr(self, text):
        return translate_dynamic_en(text) if self.language == "en" else text

    @staticmethod
    def _zh(name, **values):
        text = TEXTS["zh"].get(name, name)
        return text.format(**values) if values else text

    def _bind_text(self, widget, key, option="text"):
        widget.configure(**{option: self._t(key)})
        self._text_bindings.append((widget, option, key))
        return widget

    def _label(self, parent, key, **options):
        label = tk.Label(parent, text=self._t(key), **options)
        self._text_bindings.append((label, "text", key))
        return label

    def _configure_app_vars(self):
        for source_name, target_name in (
            ("state_head", "state_head_var"),
            ("status", "status_var"),
            ("scores", "scores_var"),
            ("bottom_status", "bottom_status_var"),
            ("sound_hint", "sound_hint_var"),
            ("key_hint", "key_hint_var"),
            ("diagnostic_status", "diagnostic_status_var"),
            ("advanced_feedback", "advanced_feedback_var"),
        ):
            source = getattr(self.app, source_name)
            target = tk.StringVar(master=self.root, value=self._tr(source.get()))
            setattr(self, target_name, target)
            self._bridges.append((source, target))

            def sync(*_args, src=source, dst=target):
                dst.set(self._tr(src.get()))

            source.trace_add("write", sync)
            self._trace_callbacks.append(sync)

    def _profile_name(self, key):
        name = PROFILES.get(key, PROFILES[DEFAULT_PROFILE])["name"]
        if self.language == "en":
            return PROFILE_NAMES_EN.get(key, name)
        return name

    def _sound_display(self, actual):
        if self.language == "en":
            return SOUND_NAMES_EN.get(actual, actual)
        return actual

    def _sound_actual(self, display):
        try:
            choices = tuple(dict.fromkeys(self.app.sounds.exit_choices()))
        except Exception:
            choices = self._sound_actual_cache
        for actual in choices:
            if self._sound_display(actual) == display:
                return actual
        return display

    def _update_sound_choices(self):
        try:
            actual = tuple(dict.fromkeys(self.app.sounds.exit_choices()))
        except Exception:
            return
        self._sound_actual_cache = actual
        try:
            self.audio_combo.configure(
                values=tuple(self._sound_display(item) for item in actual)
            )
        except Exception:
            pass

    def _toggle_language(self):
        self.language = "en" if self.language == "zh" else "zh"
        self._retranslate()
        try:
            self.app.write_preferences(language=self.language)
        except Exception:
            pass

    def _retranslate(self):
        self.lang_button.configure(text=self._t("lang_button"))
        for widget, option, key in self._text_bindings:
            try:
                widget.configure(**{option: self._t(key)})
            except Exception:
                pass
        for source, target in self._bridges:
            try:
                target.set(self._tr(source.get()))
            except Exception:
                pass
        if hasattr(self, "auto_feedback"):
            self.auto_feedback_display.set(self._tr(self.auto_feedback.get()))
        if hasattr(self, "auto_button_text"):
            self.auto_button_text.set(
                self._t("auto_recording")
                if self._auto_recording else self._auto_label_cache
            )
        if hasattr(self, "exit_sound_display_var"):
            self.exit_sound_display_var.set(
                self._sound_display(self.exit_sound_var.get())
            )
            self._update_sound_choices()
        self._apply_profile(self._profile_key, initial=True)
        self._refresh()
        self._log_cache = ""
        self._refresh_log()
        self.root.update_idletasks()
        for page in self.pages:
            page._sync()

    # ------------------------------------------------------------------ setup
    def _configure_root(self):
        self.root.title(
            f"{self._profile_name(self._profile_key)}{self._t('release_suffix')}"
        )
        self.root.configure(bg=BG)
        self.root.geometry("600x540")
        self.root.resizable(False, False)
        self.root.minsize(600, 540)
        self.root.maxsize(600, 540)

    def _configure_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Compact.TCombobox",
            fieldbackground=INPUT,
            background=BUTTON,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=3,
        )
        style.map(
            "Compact.TCombobox",
            fieldbackground=[("readonly", INPUT)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", ACCENT)],
            selectforeground=[("readonly", "#FFFFFF")],
        )
        style.configure(
            "Compact.Vertical.TScrollbar",
            background=CARD2,
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=MUTED,
            lightcolor=CARD2,
            darkcolor=CARD2,
            width=7,
        )
        self.root.option_add("*TCombobox*Listbox.background", INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

    # ------------------------------------------------------------------ helpers
    def _build(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=BG, padx=10, pady=6)
        header.pack(fill="x")
        self.header_title = tk.Label(
            header, text="", bg=BG, fg=TEXT,
            font=(FONT, 10, "bold"), anchor="w",
        )
        self.header_title.pack(side="left")
        self.mode_badge = tk.Label(
            header, text=self._t("standby_badge"), bg=BUTTON, fg=MUTED,
            font=(FONT, 8, "bold"), padx=6, pady=1,
        )
        self.mode_badge.pack(side="right")
        self.header_status = tk.Label(
            header, text="", bg=BG, fg=MUTED,
            font=(FONT, 8), anchor="e",
        )
        self.header_status.pack(side="right", padx=(0, 6))
        self.lang_button = tk.Button(
            header, text=self._t("lang_button"),
            command=self._toggle_language,
            bg=BUTTON, fg=TEXT,
            activebackground=BUTTON_HOVER, activeforeground=TEXT,
            relief="flat", bd=0, cursor="hand2",
            font=(FONT, 8, "bold"), padx=5, pady=1,
        )
        self.lang_button.pack(side="right", padx=(0, 6))

        tabbar = tk.Frame(outer, bg=BG, padx=8)
        tabbar.pack(fill="x", pady=(0, 6))
        self.tab_buttons = []
        for index, key in enumerate(("tab_prep", "tab_advanced", "tab_diag")):
            button = tk.Button(
                tabbar, text=self._t(key), relief="flat", bd=0,
                padx=4, pady=5, cursor="hand2",
                font=(FONT, 8, "bold"),
                command=lambda i=index: self._show_tab(i),
            )
            button.pack(
                side="left", fill="x", expand=True,
                padx=(0 if index == 0 else 2, 0),
            )
            self.tab_buttons.append(button)
            self._bind_text(button, key)

        content = tk.Frame(outer, bg=BG, padx=8)
        content.pack(fill="both", expand=True)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.pages = []
        for builder in (self._build_prep, self._build_advanced, self._build_diag):
            page, body = self._make_page(content)
            builder(body)
            self.pages.append(page)
        self._show_tab(0)
        self.root.update_idletasks()
        self.root.geometry("600x540")

    def _make_page(self, parent):
        page = tk.Frame(parent, bg=BG)
        canvas = tk.Canvas(page, bg=BG, highlightthickness=0, bd=0, width=1, height=1)
        scroll = ttk.Scrollbar(
            page, orient="vertical", command=canvas.yview,
            style="Compact.Vertical.TScrollbar",
        )
        inner = tk.Frame(canvas, bg=BG)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def sync_scroll(event=None):
            canvas.update_idletasks()
            need = inner.winfo_reqheight() > canvas.winfo_height() + 1
            managed = bool(scroll.winfo_manager())
            if need and not managed:
                scroll.pack(side="right", fill="y")
            elif not need and managed:
                scroll.pack_forget()
            if not need:
                canvas.yview_moveto(0)
            canvas.configure(
                scrollregion=(0, 0, canvas.winfo_width(), inner.winfo_reqheight())
            )

        inner.bind("<Configure>", lambda e: sync_scroll())
        canvas.bind(
            "<Configure>",
            lambda e: (canvas.itemconfigure(window, width=e.width), sync_scroll()),
        )
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        canvas.after(80, sync_scroll)

        def wheel(event):
            if not scroll.winfo_manager():
                return
            if inner.winfo_reqheight() <= canvas.winfo_height() + 1:
                return
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        body = tk.Frame(inner, bg=BG, padx=1, pady=4)
        body.pack(fill="both", expand=True)
        page._canvas = canvas
        page._inner = inner
        page._scroll = scroll
        page._window = window
        page._sync = sync_scroll
        return page, body

    def _show_tab(self, index):
        self._current_tab = index
        for page in self.pages:
            page.grid(row=0, column=0, sticky="nsew")
        page = self.pages[index]
        page.tkraise()
        self.root.update_idletasks()
        page._canvas.itemconfigure(page._window, width=page._canvas.winfo_width())
        page._sync()
        for i, button in enumerate(self.tab_buttons):
            active = i == index
            button.configure(
                bg=ACCENT if active else CARD,
                fg=BG if active else MUTED,
                activebackground=ACCENT if active else BUTTON_HOVER,
                activeforeground=BG if active else TEXT,
            )

    # ----------------------------------------------------------- app identity
    def _exit_sound_changed(self, event=None):
        value = self._sound_actual(self.exit_sound_display_var.get())
        self.exit_sound_var.set(value)
        self.app.select_sound("exit")
        value = self.exit_sound_var.get()
        self._last_sound = value
        if value in PROFILES:
            self._apply_profile(value)

    def _header_font_size(self, name):
        size = 10 if self.language == "zh" else 9
        while size > 7:
            measure = tkfont.Font(
                root=self.root, family=FONT, size=size, weight="bold"
            ).measure(name)
            if measure <= 250:
                break
            size -= 1
        return size

    def _apply_profile(self, key, initial=False):
        profile = PROFILES.get(key)
        if profile is None:
            return
        self._profile_key = key
        palette_name = profile["palette"]
        old_palette = self._palette_name
        if palette_name != old_palette:
            old = PALETTES.get(old_palette, PALETTES["purple"])
            new = PALETTES[palette_name]
            mapping = {}
            for slot in PALETTE_KEYS:
                mapping.setdefault(old[slot].upper(), new[slot])
            self._palette_name = palette_name
            _set_palette_globals(palette_name)
            self.root.configure(bg=BG)
            self._configure_style()
            self._retint(mapping)
            self._show_tab(self._current_tab)

        name = self._profile_name(key)
        self.root.title(f"{name}{self._t('release_suffix')}")
        self.header_title.configure(
            text=name,
            font=(FONT, self._header_font_size(name), "bold"),
        )
        self.about_name.configure(text=f"{name}{self._t('about_version')}")
        self._apply_icon(profile["icon"])
        self._apply_notice_tip(name)

    def _icon_root(self):
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / "icons"
        return Path(__file__).resolve().parent / "icons"

    def _apply_icon(self, filename):
        candidates = (
            self._icon_root() / filename,
            self.assets / filename,
            self.assets / "subaru_clean.ico",
        )
        for path in candidates:
            if not path.exists():
                continue
            try:
                self.root.iconbitmap(default=str(path))
                self.root.iconbitmap(str(path))
                return
            except Exception:
                continue

    def _apply_notice_tip(self, name):
        notice = getattr(self.app, "notice", None)
        data = getattr(notice, "data", None)
        shell = getattr(notice, "shell", None)
        if data is None or shell is None:
            return
        try:
            key = getattr(self.app, "key_name", "")
            data.szTip = f"{name} · {self._t('notice_tip').format(key=key)}"
            data.uFlags = 4
            shell.Shell_NotifyIconW(1, ctypes.byref(data))
        except Exception:
            pass

    def _admin_notice(self):
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return
        except Exception:
            pass
        try:
            values = json.loads(Path(self.app.config_path).read_text("utf-8"))
        except Exception:
            values = {}
        if values.get("admin_prompt_shown"):
            return
        answer = messagebox.askyesno(
            self._t("admin_title"),
            self._t("admin_message"),
            parent=self.root,
        )
        try:
            self.app.write_preferences(admin_prompt_shown=True)
        except Exception:
            pass
        if not answer:
            return
        try:
            shell = ctypes.windll.shell32
            shell.ShellExecuteW.argtypes = [
                ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int,
            ]
            shell.ShellExecuteW.restype = ctypes.c_void_p
            result = shell.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
            if result and result > 32:
                self._release_instance_mutex()
                self.root.after(300, self.root.destroy)
            else:
                self.app.status.set(self._zh("admin_denied"))
        except Exception:
            self.app.status.set(self._zh("admin_restart_failed"))

    def _release_instance_mutex(self):
        try:
            import __main__

            handle = getattr(__main__, "mutex", None)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                __main__.mutex = None
        except Exception:
            pass

    def _retint(self, mapping):
        options = (
            "background", "foreground", "activebackground", "activeforeground",
            "highlightbackground", "highlightcolor", "selectbackground",
            "selectforeground", "insertbackground", "selectcolor",
            "troughcolor", "disabledforeground",
        )

        def walk(widget):
            for option in options:
                try:
                    current = widget.cget(option)
                except Exception:
                    continue
                if not isinstance(current, str):
                    current = str(current)
                new = mapping.get(current.strip().upper())
                if new:
                    try:
                        widget.configure(**{option: new})
                    except Exception:
                        pass
            for child in widget.winfo_children():
                walk(child)

        walk(self.root)
        for combo in (self.audio_combo, self.hotkey_combo, self.hz_combo):
            self._retint_popdown(combo)

    def _retint_popdown(self, combo):
        try:
            popdown = str(
                self.root.tk.call("ttk::combobox::PopdownWindow", str(combo))
            )
            listbox = f"{popdown}.f.l"
            self.root.tk.call(
                listbox, "configure",
                "-background", INPUT, "-foreground", TEXT,
                "-selectbackground", ACCENT, "-selectforeground", "#FFFFFF",
            )
        except Exception:
            pass

    def _page_title(self, parent, title, subtitle):
        tk.Label(
            parent, text=title, bg=BG, fg=TEXT,
            font=(FONT, 10, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            parent, text=subtitle, bg=BG, fg=MUTED,
            font=(FONT, 8), anchor="w",
        ).pack(fill="x", pady=(0, 6))

    def _card(self, parent):
        card = tk.Frame(
            parent, bg=CARD, highlightbackground=BORDER,
            highlightthickness=1, padx=8, pady=5,
        )
        card.pack(fill="x", pady=(0, 6))
        return card

    def _separator(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=5)

    def _button(self, parent, text, command, primary=False, small=False,
                text_key=None):
        bg = ACCENT if primary else BUTTON
        fg = BG if primary else TEXT
        button = tk.Button(
            parent, text=self._t(text_key) if text_key else text, command=command,
            bg=bg, fg=fg,
            activebackground=ACCENT if primary else BUTTON_HOVER,
            activeforeground=fg,
            relief="flat", bd=0, cursor="hand2",
            font=(FONT, 8, "bold" if primary else "normal"),
            padx=6 if small else 8, pady=3 if small else 5,
        )
        if text_key:
            self._text_bindings.append((button, "text", text_key))
        return button

    def _toggle(self, parent, text, variable, row, column, text_key=None):
        check = tk.Checkbutton(
            parent, text=self._t(text_key) if text_key else text,
            variable=variable,
            command=self.app.apply_runtime_settings,
            bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT,
            selectcolor=INPUT, font=(FONT, 8), anchor="w",
            bd=0, highlightthickness=0, padx=0, pady=1,
        )
        check.grid(row=row, column=column, sticky="w", padx=(0, 6))
        if text_key:
            self._text_bindings.append((check, "text", text_key))
        return check

    # ------------------------------------------------------------------ tab 1
    def _build_prep(self, parent):
        card = self._card(parent)
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        self._label(
            row, "sound", bg=CARD, fg=TEXT, font=(FONT, 8, "bold"),
        ).pack(side="left")
        exit_choices = tuple(dict.fromkeys(self.app.sounds.exit_choices()))
        current_exit = self.app.sounds.selected.get("exit", "")
        if not current_exit and exit_choices:
            current_exit = exit_choices[0]
        self.exit_sound_var = tk.StringVar(value=current_exit)
        self.exit_sound_display_var = tk.StringVar(
            master=self.root, value=self._sound_display(current_exit)
        )
        self.app.sound_vars["exit"] = self.exit_sound_var
        self._sound_actual_cache = exit_choices

        def sync_sound(*_args):
            self.exit_sound_display_var.set(
                self._sound_display(self.exit_sound_var.get())
            )

        self.exit_sound_var.trace_add("write", sync_sound)
        self._trace_callbacks.append(sync_sound)
        self.import_btn = self._button(
            row, "", self._import_sound, small=True, text_key="import",
        )
        self.import_btn.pack(side="right")
        self.play_btn = self._button(
            row, "", lambda: self.app.play_sound("exit"), small=True,
            text_key="preview",
        )
        self.play_btn.pack(side="right", padx=(0, 3))
        self.audio_combo = ttk.Combobox(
            row, textvariable=self.exit_sound_display_var,
            values=tuple(self._sound_display(item) for item in exit_choices),
            state="readonly", width=12,
            style="Compact.TCombobox", font=(FONT, 8),
        )
        self.audio_combo.pack(side="left", fill="x", expand=True, padx=(5, 3))
        self.audio_combo.bind("<<ComboboxSelected>>", self._exit_sound_changed)
        self.app.sound_boxes["exit"] = self.audio_combo
        tk.Label(
            card, textvariable=self.sound_hint_var, bg=CARD, fg=MUTED,
            font=(FONT, 7), anchor="w", justify="left", wraplength=410,
        ).pack(fill="x", pady=(4, 0))

        self._separator(card)
        hrow = tk.Frame(card, bg=CARD)
        hrow.pack(fill="x")
        self._label(
            hrow, "hotkey", bg=CARD, fg=TEXT, font=(FONT, 8, "bold"),
        ).pack(side="left")
        self._key_map = {hotkey_label(combo): combo for combo in self.key_choices}
        self.hotkey_var = tk.StringVar(
            value=hotkey_label(self.app.hotkey_service.combo)
        )
        self.hotkey_combo = ttk.Combobox(
            hrow, textvariable=self.hotkey_var,
            values=tuple(self._key_map.keys()),
            state="readonly", width=7,
            style="Compact.TCombobox", font=(FONT, 8),
        )
        self.hotkey_combo.pack(side="left", padx=(5, 3))
        self.hotkey_combo.bind("<<ComboboxSelected>>", self._change_hotkey)
        self.hotkey_check_btn = self._button(
            hrow, "", self._check_hotkey, small=True, text_key="check",
        )
        self.hotkey_check_btn.pack(side="left")
        tk.Label(
            card, textvariable=self.key_hint_var, bg=CARD, fg=MUTED,
            font=(FONT, 7), anchor="w", justify="left", wraplength=410,
        ).pack(fill="x", pady=(4, 0))

        status = self._card(parent)
        top = tk.Frame(status, bg=CARD)
        top.pack(fill="x")
        self.state_label = tk.Label(
            top, textvariable=self.state_head_var, bg=CARD, fg=TEXT,
            font=(FONT, 11, "bold"), anchor="w",
        )
        self.state_label.pack(side="left", fill="x", expand=True)
        self.mode_badge2 = tk.Label(
            top, text="", bg=GREEN, fg=BG,
            font=(FONT, 7, "bold"), padx=5, pady=1,
        )
        self.mode_badge2.pack(side="right")
        tk.Label(
            status, textvariable=self.status_var, bg=CARD, fg=MUTED,
            font=(FONT, 8), anchor="w", justify="left", wraplength=410,
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            status, textvariable=self.scores_var, bg=CARD, fg=MUTED,
            font=(FONT, 7), anchor="w", justify="left", wraplength=410,
        ).pack(fill="x", pady=(2, 0))

        self._separator(status)
        self.mode_check = tk.Checkbutton(
            status, text="",
            variable=self.app.dry, command=self._mode_changed,
            bg=CARD, fg=GREEN, activebackground=CARD, activeforeground=GREEN,
            selectcolor=INPUT, font=(FONT, 8), anchor="w",
            bd=0, highlightthickness=0, padx=0, pady=1,
        )
        self._bind_text(self.mode_check, "test_mode")
        self.mode_check.pack(fill="x")
        self.mode_warning = tk.Label(
            status, text="", bg=CARD, fg=GREEN,
            font=(FONT, 7), anchor="w", justify="left", wraplength=410,
        )
        self.mode_warning.pack(fill="x")

        actions = tk.Frame(status, bg=CARD)
        actions.pack(fill="x", pady=(6, 0))
        self.action_btn = self._button(
            actions, self._t("start_monitor"), self.app.toggle, primary=True,
        )
        self.action_btn.pack(side="left", fill="x", expand=True)
        self.log_btn = self._button(
            actions, "", self.app.open_log, small=True, text_key="log",
        )
        self.log_btn.pack(side="left", padx=(4, 0))
        tk.Label(
            status, textvariable=self.bottom_status_var, bg=CARD, fg=MUTED,
            font=(FONT, 7), anchor="w", justify="left", wraplength=410,
        ).pack(fill="x", pady=(4, 0))

    def _import_sound(self):
        path = filedialog.askopenfilename(
            parent=self.root, title=self._t("choose_sound"),
            filetypes=[
                (self._t("audio_files"), "*.wav *.mp3 *.flac *.ogg"),
                (self._t("all_files"), "*.*"),
            ],
        )
        if path:
            self.app.import_sound("exit", path)

    def _change_hotkey(self, event=None):
        label = self.hotkey_var.get()
        combo = self._key_map.get(label)
        if combo is None:
            return
        current = tuple(self.app.hotkey_service.combo)
        if tuple(combo) == current:
            return
        try:
            accepted = self.app.hotkey_service.rebind(tuple(combo))
        except Exception as exc:
            self.app.key_hint.set(self._zh("hotkey_change_failed", exc=exc))
            self.hotkey_var.set(hotkey_label(current))
            return
        if not accepted:
            self.app.key_hint.set(self._zh("hotkey_in_use_unchanged"))
            self.hotkey_var.set(hotkey_label(current))
            return
        self.app.key_name = self.app.hotkey_service.key_name
        self.app.hotkeys = self.app.hotkey_service.registered
        self.app.key_label.set(self.app.key_name)
        self.app.key_hint.set(self._zh("hotkey_return_hint", key=self.app.key_name))
        try:
            self.app.persist_session()
        except Exception as exc:
            self.app.key_hint.set(
                self._zh("hotkey_changed_save_failed", exc=exc)
            )

    def _check_hotkey(self):
        combo = self._key_map.get(self.hotkey_var.get())
        if combo is None:
            return
        if tuple(combo) == tuple(self.app.hotkey_service.combo):
            self.app.key_hint.set(
                self._zh("hotkey_in_use_current", key=hotkey_label(combo))
            )
            return
        try:
            free = self.app.hotkey_service.available(tuple(combo))
        except Exception as exc:
            self.app.key_hint.set(self._zh("hotkey_check_failed", exc=exc))
            return
        key = hotkey_label(combo)
        self.app.key_hint.set(
            self._zh("hotkey_available", key=key) if free
            else self._zh("hotkey_occupied", key=key)
        )

    def _mode_changed(self):
        if not self.app.apply_runtime_settings():
            self.app.dry.set(not self.app.dry.get())
            self.app.status.set(self._zh("invalid_delay_sampling"))

    # ------------------------------------------------------------- resolution
    def _load_resolution(self):
        try:
            values = json.loads(Path(self.app.config_path).read_text("utf-8"))
            return str(values.get("resolution", "auto"))
        except Exception:
            return "auto"

    def _resolution_size(self):
        text = self.res_text.get().strip().lower().replace("×", "x")
        if text in ("", "auto", "自动"):
            return None
        parts = text.split("x")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            width, height = int(parts[0]), int(parts[1])
            if 320 <= width <= 10000 and 240 <= height <= 10000:
                return (width, height)
        return False

    def _apply_resolution(self):
        size = self._resolution_size()
        if size is False:
            return False
        self.app.detector.custom_size = size
        return True

    # -------------------------------------------------------------- auto key
    def _load_auto(self):
        values = {}
        try:
            values = json.loads(Path(self.app.config_path).read_text("utf-8"))
        except Exception:
            pass
        config = values.get("auto_key") if isinstance(values, dict) else None
        if not isinstance(config, dict):
            config = {}
        try:
            vk = int(config.get("vk", 87))
        except (TypeError, ValueError):
            vk = 87
        if not 1 <= vk <= 254 or vk in (16, 17, 18, 91, 92):
            vk = 87
        try:
            interval = int(config.get("interval_sec", 5))
        except (TypeError, ValueError):
            interval = 5
        if not 1 <= interval <= 3600:
            interval = 5
        label = str(config.get("label") or ("W" if vk == 87 else f"VK{vk}"))
        return bool(config.get("enabled", False)), interval, vk, label

    def _auto_config(self):
        try:
            interval = int(self.auto_interval.get())
            vk = int(self.auto_vk.get())
        except (TypeError, ValueError):
            return None
        if not 1 <= interval <= 3600 or not 1 <= vk <= 254:
            return None
        return {
            "enabled": bool(self.auto_enabled.get()),
            "interval_sec": interval,
            "vk": vk,
            "label": self._auto_label_cache if self._auto_recording else self.auto_button_text.get(),
        }

    def _auto_say(self, text, color=None):
        self.auto_feedback.set(text)
        self.auto_feedback_display.set(self._tr(text))
        self.auto_feedback_label.configure(fg=color or MUTED)

    def _hud_ready(self):
        app = self.app
        if not (getattr(app, "active", False) or getattr(app, "arming", False)):
            return False
        features = getattr(getattr(app, "detector", None), "last_features", None)
        if not isinstance(features, dict) or not features:
            return False
        try:
            return bool(start_hud_evidence(features))
        except Exception:
            return False

    def _auto_changed(self):
        self._auto_prev = False
        self._auto_next = 0.0
        config = self._auto_config()
        if config is None:
            self._auto_say(self._zh("auto_interval_error"), AMBER)
            return
        if self.auto_enabled.get():
            self._auto_say(
                self._zh(
                    "auto_enabled_feedback",
                    key=config["label"],
                    seconds=config["interval_sec"],
                ),
                ACCENT,
            )
        else:
            self._auto_say(self._zh("auto_disabled_feedback"))
        try:
            self.app.write_preferences(auto_key=config)
        except Exception as exc:
            self._auto_say(self._zh("save_failed", exc=exc), RED)

    def _auto_unbind(self):
        if getattr(self, "_auto_bind_id", None):
            try:
                self.root.unbind("<KeyPress>", self._auto_bind_id)
            except Exception:
                pass
        self._auto_bind_id = None
        self._auto_recording = False

    def _auto_cancel(self):
        self._auto_unbind()
        self.auto_button_text.set(self._auto_label_cache)

    def _auto_record(self):
        if self._auto_recording:
            self._auto_cancel()
            return
        self._auto_recording = True
        self._auto_label_cache = self.auto_button_text.get()
        self.auto_button_text.set(self._t("auto_recording"))
        self._auto_bind_id = self.root.bind("<KeyPress>", self._auto_capture, add="+")
        self.root.focus_set()
        self._auto_say(self._zh("auto_record_prompt"), ACCENT)

    def _auto_capture(self, event):
        keysym = event.keysym
        if keysym == "Escape":
            self._auto_cancel()
            self._auto_say(self._zh("auto_record_canceled"))
            return "break"
        vk = _vk_for(keysym)
        if vk is None or vk in (16, 17, 18, 91, 92):
            self._auto_say(self._zh("auto_record_unsupported"), AMBER)
            self._auto_cancel()
            return "break"
        if vk == 123:
            self._auto_say(self._zh("auto_record_f12"), AMBER)
            self._auto_cancel()
            return "break"
        if tuple(self.app.hotkey_service.combo) == (0, vk):
            self._auto_say(self._zh("auto_record_same_hotkey"), AMBER)
            self._auto_cancel()
            return "break"
        label = _label_for(keysym)
        self.auto_vk.set(vk)
        self._auto_unbind()
        self.auto_button_text.set(label)
        self._auto_label_cache = label
        self._auto_prev = False
        self._auto_say(self._zh("auto_record_selected", key=label), ACCENT)
        return "break"

    def _auto_tick(self):
        if not hasattr(self, "auto_enabled"):
            return
        if not self.auto_enabled.get():
            if getattr(self, "_auto_prev", False):
                self._auto_prev = False
                self._auto_next = 0.0
                self._auto_say(self._zh("auto_disabled_feedback"))
            return
        config = self._auto_config()
        if config is None:
            self._auto_say(self._zh("auto_interval_error"), AMBER)
            return
        if not _game_foreground():
            if getattr(self, "_auto_prev", False):
                self._auto_prev = False
                self._auto_next = 0.0
                self._auto_count = 0
                self._auto_say(self._zh("auto_foreground_paused"))
            return
        if not self._hud_ready():
            if getattr(self, "_auto_prev", False):
                self._auto_prev = False
                self._auto_next = 0.0
                self._auto_count = 0
                self._auto_say(self._zh("auto_hud_wait"), AMBER)
            return
        now = time.monotonic()
        if not self._auto_prev:
            self._auto_prev = True
            self._auto_count = 0
            self._auto_next = now
            self._auto_say(
                self._zh(
                    "auto_hud_ready",
                    seconds=config["interval_sec"],
                    key=config["label"],
                )
            )
        if now < self._auto_next:
            return
        if _modifiers_down():
            self._auto_next = now + 0.5
            return
        if _send_key(config["vk"], False):
            self.root.after(50, lambda v=config["vk"]: _send_key(v, True))
            self._auto_count += 1
            self._auto_say(
                self._zh(
                    "auto_running",
                    key=config["label"],
                    count=self._auto_count,
                )
            )
        else:
            self._auto_say(self._zh("auto_send_failed"), RED)
        self._auto_next = now + config["interval_sec"]

    # ------------------------------------------------------------------ tab 2
    def _build_advanced(self, parent):
        card = self._card(parent)
        self._label(
            card, "sound_toggles", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        grid = tk.Frame(card, bg=CARD)
        grid.pack(fill="x", pady=(3, 0))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        self._toggle(
            grid, "", self.app.sound_on_var, 0, 0, text_key="start_sound",
        )
        self._toggle(
            grid, "", self.app.sound_off_var, 0, 1, text_key="stop_sound",
        )
        self._toggle(
            grid, "", self.app.return_sound, 1, 0, text_key="exit_sound",
        )
        self._toggle(
            grid, "", self.app.mute_var, 1, 1, text_key="mute_all",
        )

        card = self._card(parent)
        self._label(
            card, "detection", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(4, 0))
        self._label(
            row, "delay_ms", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="left")
        tk.Entry(
            row, textvariable=self.app.delay_text, width=5,
            bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=(FONT, 8),
        ).pack(side="left", padx=(4, 10), ipady=2)
        self._label(
            row, "sampling", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="left")
        self.hz_combo = ttk.Combobox(
            row, textvariable=self.app.hz_text,
            values=("15", "30", "60"), state="readonly", width=4,
            style="Compact.TCombobox", font=(FONT, 8),
        )
        self.hz_combo.pack(side="left", padx=(4, 0))
        rrow = tk.Frame(card, bg=CARD)
        rrow.pack(fill="x", pady=(4, 0))
        self._label(
            rrow, "resolution", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="left")
        self.res_text = tk.StringVar(value=self._load_resolution())
        tk.Entry(
            rrow, textvariable=self.res_text, width=10,
            bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=(FONT, 8),
        ).pack(side="left", padx=(4, 0), ipady=2)
        self._label(
            card, "detection_hint",
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        ).pack(fill="x", pady=(3, 0))

        enabled, interval, vk, label = self._load_auto()
        self.auto_enabled = tk.BooleanVar(value=enabled)
        self.auto_interval = tk.StringVar(value=str(interval))
        self.auto_vk = tk.IntVar(value=vk)
        self.auto_button_text = tk.StringVar(value=label)
        self._auto_label_cache = label
        self._auto_recording = False
        self._auto_bind_id = None
        self._auto_prev = False
        self._auto_next = 0.0
        self._auto_count = 0
        initial_feedback = self._zh(
            "auto_feedback_on_initial" if enabled else "auto_feedback_off_initial"
        )
        self.auto_feedback = tk.StringVar(value=initial_feedback)
        self.auto_feedback_display = tk.StringVar(
            master=self.root,
            value=self._t(
                "auto_feedback_on_initial" if enabled
                else "auto_feedback_off_initial"
            ),
        )

        card = self._card(parent)
        self._label(
            card, "auto_key", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(4, 0))
        enabled_check = tk.Checkbutton(
            row, text="", variable=self.auto_enabled,
            command=self._auto_changed,
            bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT,
            selectcolor=INPUT, font=(FONT, 8), anchor="w",
            bd=0, highlightthickness=0, padx=0, pady=1,
        )
        self._bind_text(enabled_check, "enabled")
        enabled_check.pack(side="left")
        self._label(
            row, "interval", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="left", padx=(8, 0))
        tk.Entry(
            row, textvariable=self.auto_interval, width=4,
            bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=(FONT, 8),
        ).pack(side="left", padx=(3, 2), ipady=2)
        self._label(
            row, "seconds", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="left")
        self.auto_key_btn = self._button(
            row, "", self._auto_record, small=True,
        )
        self.auto_key_btn.configure(textvariable=self.auto_button_text, width=9)
        self.auto_key_btn.pack(side="right")
        self._label(
            row, "key", bg=CARD, fg=MUTED, font=(FONT, 8),
        ).pack(side="right", padx=(0, 4))
        self._label(
            card, "auto_hint", bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        ).pack(fill="x", pady=(3, 0))
        self.auto_feedback_label = tk.Label(
            card, textvariable=self.auto_feedback_display,
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        )
        self.auto_feedback_label.pack(fill="x", pady=(2, 0))

        card = self._card(parent)
        self._label(
            card, "diag_capture", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        diag_grid = tk.Frame(card, bg=CARD)
        diag_grid.pack(fill="x", pady=(3, 0))
        self._toggle(
            diag_grid, "", self.app.collect_var, 0, 0, text_key="save_shots",
        )
        self._toggle(
            diag_grid, "", self.app.log_var, 1, 0, text_key="collect_logs",
        )
        tk.Label(
            card, textvariable=self.diagnostic_status_var,
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        ).pack(fill="x", pady=(3, 0))

        card = self._card(parent)
        self._button(
            card, "", self._save_settings, primary=True,
            text_key="save_settings",
        ).pack(fill="x")
        tk.Label(
            card, textvariable=self.advanced_feedback_var,
            bg=CARD, fg=GREEN, font=(FONT, 7), anchor="w",
        ).pack(fill="x", pady=(3, 0))

    def _save_settings(self):
        config = self._auto_config()
        if config is None:
            self.app.advanced_feedback.set(
                self._zh("auto_interval_save_error")
            )
            return
        try:
            if not self.app.apply_runtime_settings():
                self.app.advanced_feedback.set(
                    self._zh("invalid_delay_sampling")
                )
                return
            if not self._apply_resolution():
                self.app.advanced_feedback.set(
                    self._zh("invalid_resolution")
                )
                return
            self.app.persist_session()
            size = self._resolution_size()
            value = "auto" if size is None else f"{size[0]}x{size[1]}"
            self.app.write_preferences(auto_key=config, resolution=value)
            self.app.advanced_feedback.set(self._zh("settings_saved"))
        except Exception as exc:
            self.app.advanced_feedback.set(self._zh("save_failed", exc=exc))

    # ------------------------------------------------------------------ tab 3
    def _build_diag(self, parent):
        card = self._card(parent)
        self._label(
            card, "runtime_status", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            card, textvariable=self.diagnostic_status_var,
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        ).pack(fill="x", pady=(2, 0))
        self.interface_var = tk.StringVar(master=self.root, value="")
        tk.Label(
            card, textvariable=self.interface_var,
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
            justify="left", wraplength=410,
        ).pack(fill="x", pady=(2, 0))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(5, 0))
        self._button(
            row, "", self.app.open_log, small=True, text_key="open_log",
        ).pack(side="left")
        self._button(
            row, "", self._refresh_log, small=True, text_key="refresh",
        ).pack(side="left", padx=(4, 0))

        card = self._card(parent)
        self._label(
            card, "recent_events", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        self.log_text = tk.Text(
            card, width=1, height=7, bg=INPUT, fg=MUTED,
            insertbackground=TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            font=(FONT, 7), wrap="word", state="disabled",
        )
        self.log_text.pack(fill="x", pady=(4, 0))

        card = self._card(parent)
        self._label(
            card, "about", bg=CARD, fg=TEXT,
            font=(FONT, 8, "bold"), anchor="w",
        ).pack(fill="x")
        self.about_name = tk.Label(
            card, text="", bg=CARD, fg=TEXT, font=(FONT, 8), anchor="w",
        )
        self.about_name.pack(fill="x", pady=(2, 0))
        self._label(
            card, "about_hint",
            bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w",
        ).pack(fill="x")

    def _refresh_log(self):
        lines = []
        try:
            path = Path(self.app.log.name)
            if path.exists():
                with open(path, "rb") as handle:
                    handle.seek(0, 2)
                    size = handle.tell()
                    handle.seek(max(0, size - 16384))
                    raw = handle.read()
                for line in raw.decode("utf-8", "replace").splitlines()[-10:]:
                    try:
                        item = json.loads(line)
                        stamp = datetime.fromtimestamp(
                            item.get("time", 0)
                        ).strftime("%H:%M:%S")
                        event = item.get("event", "?")
                        extra = (
                            item.get("reason")
                            or item.get("status")
                            or item.get("message")
                            or ""
                        )
                        if self.language == "en":
                            event = EVENT_NAMES_EN.get(event, event)
                            extra = translate_dynamic_en(extra)
                        else:
                            event = EVENT_NAMES_ZH.get(event, event)
                        text = (
                            f"{stamp} {event} · {extra}" if extra
                            else f"{stamp} {event}"
                        ).strip()
                        lines.append(text[:88])
                    except Exception:
                        lines.append(line[:88])
        except Exception:
            lines = []
        text = "\n".join(lines) if lines else self._t("no_events")
        if text == self._log_cache:
            return
        self._log_cache = text
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", text)
        self.log_text.configure(state="disabled")

    # ------------------------------------------------------------------ refresh
    def _state_color(self, text):
        if any(word in text for word in ("监控中", "守护中", "正在确认")):
            return GREEN
        if "暂停" in text:
            return AMBER
        if any(word in text for word in ("失败", "错误", "未开启", "已发送")):
            return RED
        if any(word in text for word in ("正在", "检查")):
            return ACCENT
        return MUTED

    def _refresh(self):
        if getattr(self.app, "closed", False):
            return
        dry = bool(self.app.dry.get())
        running = bool(getattr(self.app, "active", False) or getattr(self.app, "arming", False))

        detector = getattr(self.app, "detector", None)
        iface = str(getattr(detector, "last_interface", "0") or "0") if running else "0"
        code = IFACE_TKF.get(iface, IFACE_TKF["0"])
        if iface == "N":
            badge_bg, badge_fg = RED, BG
        elif iface in IFACE_SAFE:
            badge_bg, badge_fg = GREEN, BG
        elif iface == "X":
            badge_bg, badge_fg = AMBER, BG
        else:
            badge_bg, badge_fg = BUTTON, MUTED
        self.mode_badge.configure(text=code, bg=badge_bg, fg=badge_fg)

        name = IFACE_NAMES.get(iface, IFACE_NAMES["0"])
        if hasattr(self, "interface_var"):
            if self.language == "zh":
                self.interface_var.set(f"当前界面：{code} · {name[0]}")
            else:
                self.interface_var.set(f"Current interface: {code} · {name[1]}")

        if self._hud_ready():
            self.mode_badge2.configure(text=self._t("ready"), bg=GREEN, fg=BG)
        elif running:
            self.mode_badge2.configure(
                text=self._t("standby_badge"), bg=AMBER, fg=BG
            )
        else:
            self.mode_badge2.configure(
                text=self._t("standby_badge"), bg=BUTTON, fg=MUTED
            )

        state = self.app.state_head.get()
        self.header_status.configure(text=self.state_head_var.get())
        self.state_label.configure(
            fg=self._state_color(state + " " + self.app.status.get())
        )
        self.mode_check.configure(fg=GREEN, activeforeground=GREEN)
        if dry:
            self.mode_warning.configure(text=self._t("test_warning"), fg=GREEN)
        else:
            self.mode_warning.configure(
                text=self._t("normal_warning"), fg=RED
            )
        self.action_btn.configure(
            text=self._t("stop_monitor") if running else self._t("start_monitor"),
            bg=RED if running else ACCENT,
            activebackground=RED if running else ACCENT,
            state="normal",
        )
        busy = bool(getattr(self.app, "sound_import_busy", False))
        self.import_btn.configure(state="disabled" if busy else "normal")
        self.action_btn.configure(state="disabled" if busy else "normal")

        if self.root.focus_get() is not self.hotkey_combo:
            current = hotkey_label(self.app.hotkey_service.combo)
            if self.hotkey_var.get() != current:
                self.hotkey_var.set(current)

    def _loop(self):
        if getattr(self.app, "closed", False):
            return
        value = self.exit_sound_var.get()
        if value != self._last_sound:
            self._last_sound = value
            if value in PROFILES:
                self._apply_profile(value)
        try:
            actual = tuple(dict.fromkeys(self.app.sounds.exit_choices()))
        except Exception:
            actual = self._sound_actual_cache
        if actual != self._sound_actual_cache:
            self._update_sound_choices()
        self._refresh()
        self._auto_tick()
        self._tick += 1
        if self._tick % 10 == 0:
            self._refresh_log()
        self.root.after(150, self._loop)

    def schedule(self):
        # The refresh loop runs every 150 ms; nothing needs to be forced here.
        pass

    def select_key(self, combo):
        self.key_recording = False
