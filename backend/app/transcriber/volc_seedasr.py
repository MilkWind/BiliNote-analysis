import base64
import os
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.decorators.timeit import timeit
from app.models.transcriber_model import TranscriptSegment, TranscriptResult
from app.transcriber.base import Transcriber
from app.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

STATUS_SUCCESS = "20000000"
STATUS_PROCESSING = "20000001"


class VolcSeedAsrTranscriber(Transcriber):
    """火山引擎 豆包大模型录音文件识别 (volc.bigasr.auc)"""

    SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
    QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
    RESOURCE_ID = os.getenv("VOLC_SEEDASR_RESOURCE_ID", "volc.bigasr.auc")

    def __init__(self):
        self.api_key = os.getenv("VOLC_SEEDASR_API_KEY")
        if not self.api_key:
            raise ValueError("VOLC_SEEDASR_API_KEY 未配置，请在 .env 中填写后重启后端")

    def _headers(self, request_id: str, include_sequence: bool = False) -> dict:
        headers = {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": self.RESOURCE_ID,
            "X-Api-Request-Id": request_id,
        }
        if include_sequence:
            headers["X-Api-Sequence"] = "-1"
        return headers

    def _submit(self, file_path: str) -> str:
        path = Path(file_path)
        audio_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        fmt = path.suffix.lstrip(".").lower() or "mp3"

        request_id = str(uuid.uuid4())
        body = {
            "audio": {"data": audio_b64, "format": fmt},
            "request": {
                "enable_punc": True,
                "enable_itn": True,
                "enable_ddc": True,
            },
        }
        logger.info(f"提交 SeedASR 任务: {path.name} ({fmt}, {path.stat().st_size} bytes)")
        resp = requests.post(
            self.SUBMIT_URL, json=body, headers=self._headers(request_id, include_sequence=True), timeout=300
        )
        status = resp.headers.get("X-Api-Status-Code", "")
        if status != STATUS_SUCCESS:
            raise Exception(
                f"SeedASR 提交失败: code={status}, msg={resp.headers.get('X-Api-Message', '')}, "
                f"body={resp.text[:500]}, logid={resp.headers.get('X-Tt-Logid', '')}"
            )
        logger.info(f"SeedASR 提交成功: request_id={request_id}, logid={resp.headers.get('X-Tt-Logid', '')}")
        return request_id

    def _query(self, request_id: str, timeout_s: float = 1200.0, interval_s: float = 5.0) -> dict:
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            resp = requests.post(self.QUERY_URL, json={}, headers=self._headers(request_id), timeout=60)
            status = resp.headers.get("X-Api-Status-Code", "")
            if status == STATUS_SUCCESS:
                logger.info(f"SeedASR 识别完成: request_id={request_id}")
                return resp.json()
            if status == STATUS_PROCESSING:
                logger.info(f"SeedASR 处理中... ({int(time.time() - t0)}s)")
                time.sleep(interval_s)
                continue
            raise Exception(
                f"SeedASR 查询失败: code={status}, msg={resp.headers.get('X-Api-Message', '')}, "
                f"body={resp.text[:500]}"
            )
        raise Exception(f"SeedASR 轮询超时 ({int(timeout_s)}s): request_id={request_id}")

    @staticmethod
    def _detect_language(text: str) -> str:
        if not text:
            return "zh"
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return "en" if ascii_chars / len(text) > 0.6 else "zh"

    @timeit
    def transcript(self, file_path: str) -> TranscriptResult:
        try:
            logger.info(f"开始处理文件: {file_path}")
            request_id = self._submit(file_path)
            result_data = self._query(request_id)

            utterances = (result_data.get("result") or {}).get("utterances") or []
            if not utterances:
                raise Exception(f"SeedASR 返回结果为空: {str(result_data)[:500]}")

            segments = []
            full_text = ""
            for u in utterances:
                text = u.get("text", "").strip()
                if not text:
                    continue
                full_text += text + " "
                segments.append(
                    TranscriptSegment(
                        start=float(u.get("start_time", 0)) / 1000.0,
                        end=float(u.get("end_time", 0)) / 1000.0,
                        text=text,
                    )
                )

            duration = ((result_data.get("audio_info") or {}).get("duration")) or 0
            logger.info(f"SeedASR 解析完成: {len(segments)} 段, 音频时长 {duration}ms")

            return TranscriptResult(
                language=self._detect_language(full_text),
                full_text=full_text.strip(),
                segments=segments,
                raw=result_data,
            )
        except Exception as e:
            logger.error(f"SeedASR 处理失败: {e}")
            raise

    def on_finish(self, video_path: str, result: TranscriptResult) -> None:
        logger.info(f"SeedASR 转写完成: {video_path}")
