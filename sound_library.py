"""Persistent audio choices; decode only at import, never on the capture path."""
from pathlib import Path
import hashlib
import json
import os
import wave

PRESETS = {
    "486回归音效": "return_by_death.wav",
    "轻提示 · 开启": "enabled.wav",
    "轻提示 · 关闭": "disabled.wav",
    "杀手皇后第三炸弹败者食尘": "killer_queen.wav",
    "宇智波鼬 · 幻术": "duckov_extract.wav",
}
DEFAULTS = {
    "enabled": "轻提示 · 开启",
    "disabled": "轻提示 · 关闭",
    "exit": "486回归音效",
}
EXIT_PRESETS = ("486回归音效", "杀手皇后第三炸弹败者食尘", "宇智波鼬 · 幻术")


class SoundLibrary:
    def __init__(self, base, assets):
        self.base = Path(base)
        self.assets = Path(assets)
        self.folder = self.base / "user_audio"
        self.config = self.base / "sound_settings.json"
        self.deleted = []
        self.custom = {}
        self.selected = dict(DEFAULTS)
        self.enabled = {key: True for key in DEFAULTS}
        self.muted = False
        try:
            data = json.loads(self.config.read_text(encoding="utf-8"))
            self.muted = data.get("muted", False) is True
            for key in DEFAULTS:
                self.enabled[key] = data.get("enabled", {}).get(key, True) is not False
            for label, name in data.get("custom", {}).items():
                if (
                    isinstance(label, str)
                    and isinstance(name, str)
                    and Path(name).name == name
                    and name.endswith(".wav")
                ):
                    self.custom[label] = name
            self.deleted = self._valid_deleted(data.get("deleted", []))
            for key in DEFAULTS:
                choice = data.get("selected", {}).get(key)
                if choice in self.choices() or (key == "exit" and choice is None):
                    self.selected[key] = choice
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def _valid_deleted(self, values):
        choices = set(self.choices())
        return [value for value in values if isinstance(value, str) and value in choices]

    def choices(self):
        return list(PRESETS) + list(self.custom)

    def exit_choices(self):
        return [choice for choice in EXIT_PRESETS + tuple(self.custom)
                if choice not in self.deleted]

    def remove_exit(self, choice):
        if choice not in self.deleted:
            self.deleted.append(choice)
        if self.selected["exit"] == choice:
            self.selected["exit"] = next(iter(self.exit_choices()), None)

    def resolve(self, key):
        choice = self.selected[key]
        if choice is None:
            return None
        path = (self.assets / PRESETS[choice] if choice in PRESETS
                else self.folder / self.custom.get(choice, "missing"))
        return path if path.is_file() else self.assets / PRESETS[DEFAULTS[key]]

    def choose(self, key, choice, persist=False):
        if key not in DEFAULTS or choice not in self.choices():
            raise ValueError("无效音效选项")
        old = self.selected[key]
        self.selected[key] = choice
        try:
            if persist:
                self.save()
        except OSError:
            self.selected[key] = old
            raise

    def save(self):
        self.base.mkdir(parents=True, exist_ok=True)
        temp = self.config.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                dict(selected=self.selected, custom=self.custom,
                     enabled=self.enabled, muted=self.muted,
                     deleted=list(self.deleted)),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temp, self.config)

    def profile(self):
        return dict(selected=dict(self.selected), custom=dict(self.custom),
                    enabled=dict(self.enabled), muted=self.muted,
                    deleted=list(self.deleted))

    def load_profile(self, data):
        if not isinstance(data, dict):
            return
        custom = data.get("custom", {})
        if isinstance(custom, dict):
            for label, name in custom.items():
                if (
                    isinstance(label, str)
                    and isinstance(name, str)
                    and Path(name).name == name
                    and name.endswith(".wav")
                ):
                    self.custom[label] = name
        self.deleted = self._valid_deleted(data.get("deleted", []))
        for key in DEFAULTS:
            choice = data.get("selected", {}).get(key)
            if choice in self.choices() or (key == "exit" and choice is None):
                self.selected[key] = choice
            else:
                self.selected[key] = DEFAULTS[key]
            self.enabled[key] = data.get("enabled", {}).get(key, True) is not False
        self.muted = data.get("muted", False) is True

    def prepare_import(self, source):
        import miniaudio
        path = Path(source)
        if path.suffix.lower() not in (".wav", ".mp3", ".flac", ".ogg"):
            raise ValueError("支持 WAV / MP3 / FLAC / OGG 音频")
        if not path.is_file() or not 0 < path.stat().st_size <= 50 * 1024 * 1024:
            raise ValueError("请选择不超过 50MB 的非空音频文件")
        self.folder.mkdir(parents=True, exist_ok=True)
        temp = self.folder / "importing.tmp"
        stream = None
        frames = 0
        digest = hashlib.sha256()
        try:
            stream = miniaudio.stream_memory(
                path.read_bytes(), nchannels=1, sample_rate=44100,
                frames_to_read=4096,
            )
            with wave.open(str(temp), "wb") as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(44100)
                for chunk in stream:
                    frames += len(chunk)
                    if frames > 60 * 44100:
                        raise ValueError("音频超过 60 秒，请先截取需要的片段")
                    raw = chunk.tobytes()
                    digest.update(raw)
                    out.writeframesraw(raw)
            if frames == 0:
                raise ValueError("音频没有可播放内容")
            name = "custom_" + digest.hexdigest()[:20] + ".wav"
            os.replace(temp, self.folder / name)
            return ("自定义 · " + path.stem[:24] + " · " + digest.hexdigest()[:6], name)
        except (ValueError, OSError):
            raise
        except Exception as exc:
            raise ValueError("无法解码音频，请确认文件未损坏且格式受支持") from exc
        finally:
            if stream is not None:
                stream.close()
            temp.unlink(missing_ok=True)

    def register(self, key, label, name):
        old = dict(self.custom)
        self.custom[label] = name
        if label in self.deleted:
            self.deleted.remove(label)
        try:
            self.choose(key, label)
        except OSError:
            self.custom = old
            raise
