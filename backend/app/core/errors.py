"""Domain error hierarchy + API error envelope.

Registry of codes: docs/ERROR_HANDLING.md §3. Published codes never change.
"""
from typing import Any


class AppError(Exception):
    status_code: int = 500
    code: str = "KD-SYS-002"
    message_en: str = "Something went wrong. Please try again."
    message_ur: str = "کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔"

    def __init__(
        self,
        message_en: str | None = None,
        message_ur: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if message_en is not None:
            self.message_en = message_en
        if message_ur is not None:
            self.message_ur = message_ur
        self.details = details
        super().__init__(self.message_en)


# ---- AUTH ----
class OtpInvalid(AppError):
    status_code = 401
    code = "KD-AUTH-001"
    message_en = "The code you entered is incorrect or has expired."
    message_ur = "آپ کا درج کردہ کوڈ غلط ہے یا مدت ختم ہو چکی ہے۔"


class OtpRateLimited(AppError):
    status_code = 429
    code = "KD-AUTH-002"
    message_en = "Too many attempts. Please try again later."
    message_ur = "بہت زیادہ کوششیں۔ کچھ دیر بعد دوبارہ کوشش کریں۔"


class TokenExpired(AppError):
    status_code = 401
    code = "KD-AUTH-003"
    message_en = "Your session has expired. Please sign in again."
    message_ur = "آپ کا سیشن ختم ہو گیا ہے۔ دوبارہ لاگ ان کریں۔"


class TokenInvalid(AppError):
    status_code = 401
    code = "KD-AUTH-004"
    message_en = "Invalid session. Please sign in again."
    message_ur = "سیشن غلط ہے۔ دوبارہ لاگ ان کریں۔"


# ---- FARM / AOI ----
class InvalidFarmArea(AppError):
    status_code = 422
    code = "KD-FARM-001"
    message_en = "Farm area must be between 0.1 and 2000 hectares."
    message_ur = "زمین کا رقبہ ۰٫۱ اور ۲۰۰۰ ہیکٹر کے درمیان ہونا چاہیے۔"


class InvalidPolygon(AppError):
    status_code = 422
    code = "KD-FARM-002"
    message_en = "Farm boundary is invalid. Please draw the outline again without crossing lines."
    message_ur = "زمین کی سرحد غلط ہے۔ براہِ کرم لکیریں آپس میں ملاتے بغیر دوبارہ بنائیں۔"


class FarmNotFound(AppError):
    status_code = 404
    code = "KD-FARM-003"
    message_en = "Farm not found."
    message_ur = "زمین نہیں ملی۔"


# ---- SATELLITE (GEE) ----
class AnalysisFailed(AppError):
    status_code = 503
    code = "KD-GEE-001"
    message_en = "Crop analysis is delayed. We are showing the latest available result."
    message_ur = "فصل کا تجزیہ تاخیر کا شکار ہے۔ ہم تازہ دستیاب نتیجہ دکھا رہے ہیں۔"


class NoClearScene(AppError):
    status_code = 200  # informational — surfaced as a status, not a hard error
    code = "KD-GEE-002"
    message_en = "No clear satellite image available due to clouds."
    message_ur = "بادلوں کی وجہ سے صاف سیٹلائٹ تصویر دستیاب نہیں۔"


# ---- EXTERNAL FEEDS ----
class WeatherUnavailable(AppError):
    status_code = 502
    code = "KD-WX-001"
    message_en = "Weather update is temporarily unavailable. Showing the last update."
    message_ur = "موسم کی تازہ معلومات عارضی طور پر دستیاب نہیں۔ آخری اپڈیٹ دکھائی جا رہی ہے۔"


class PriceUnavailable(AppError):
    status_code = 502
    code = "KD-PRICE-001"
    message_en = "Market rates are temporarily unavailable. Showing the last rates."
    message_ur = "منڈی کی قیمتیں عارضی طور پر دستیاب نہیں۔ آخری قیمتیں دکھائی جا رہی ہیں۔"


# ---- SYSTEM ----
class RateLimited(AppError):
    status_code = 429
    code = "KD-SYS-001"
    message_en = "Too many requests. Please slow down."
    message_ur = "بہت زیادہ درخواستیں۔ ذرا آرام سے کریں۔"


def error_envelope(exc: AppError, request_id: str | None = None) -> dict[str, Any]:
    """Build the single error contract used by every client (ERROR_HANDLING.md §2)."""
    err: dict[str, Any] = {
        "code": exc.code,
        "message": exc.message_en,
        "messageUr": exc.message_ur,
    }
    if exc.details:
        err["details"] = exc.details
    if request_id:
        err["requestId"] = request_id
    return {"success": False, "error": err}
