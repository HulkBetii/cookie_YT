# -*- coding: utf-8 -*-
"""
CẤU HÌNH — Chỉnh sửa thông số tại đây.
Đây là file duy nhất bạn cần chỉnh khi muốn thay đổi cách script chạy.
"""

# ── GPM Login ────────────────────────────────────────────────────
GPM_API_URL     = "http://127.0.0.1:19995"
GPM_BROWSER_DIR = r"C:\GPM\GPMLogin\gpm_browser"

# ── YouTube ──────────────────────────────────────────────────────
SO_VIDEO        = 5       # Số video mặc định (tham khảo)
SO_VIDEO_MIN    = 3       # Min video mỗi session (random weighted)
SO_VIDEO_MAX    = 7       # Max video mỗi session
MIN_GIAY_XEM    = 60      # Thời gian xem tối thiểu (giây)
MAX_GIAY_XEM    = 120     # Thời gian xem tối đa (giây)

# ── Tin tức ──────────────────────────────────────────────────────
SO_TIN_DOC      = 3       # Số bài báo mặc định (tham khảo)
SO_TIN_DOC_MIN  = 0       # Min bài báo mỗi session
SO_TIN_DOC_MAX  = 4       # Max bài báo mỗi session
SU_DUNG_GOOGLE_NEWS = True

NEWS_SITES = [
    "https://news.yahoo.co.jp",
    "https://www3.nhk.or.jp/news/",
    "https://mainichi.jp",
    "https://www.yomiuri.co.jp",
    "https://www.asahi.com",
]

# ── Vòng lặp ─────────────────────────────────────────────────────
SO_VONG_LAP         = 0     # 0 = chạy mãi; số > 0 = chạy N vòng
NGHI_GIUA_VONG_MIN  = 300   # Nghỉ bình thường min (giây) — 5 phút
NGHI_GIUA_VONG_MAX  = 900   # Nghỉ bình thường max (giây) — 15 phút
TRON_PROFILES       = True  # Xáo thứ tự profile mỗi vòng

# ── Session timing variation ─────────────────────────────────────
# Người thật đôi khi nghỉ dài 2-4h, đôi khi xem liên tục chỉ nghỉ 1-3 phút
NGHI_DAI_XAC_SUAT  = 0.08   # 8%  → nghỉ dài (2-4 tiếng)
NGHI_NGAN_XAC_SUAT = 0.15   # 15% → nghỉ rất ngắn (1-3 phút)
NGHI_DAI_MIN       = 7200   # 2 tiếng
NGHI_DAI_MAX       = 14400  # 4 tiếng
NGHI_NGAN_MIN      = 60
NGHI_NGAN_MAX      = 180

# ── Từ khóa xoay vòng ────────────────────────────────────────────
DANH_SACH_TU_KHOA = [
    "偉人の教え",
    "名言集 人生",
    "歴史の偉人 伝記",
    "成功者の習慣",
    "モチベーション 動画",
    "自己啓発 おすすめ",
    "哲学 わかりやすく",
    "人物伝 日本",
]

TU_KHOA_LIEN_QUAN = [
    "偉人", "名言", "歴史", "成功者", "人生の教え",
    "モチベーション", "自己啓発", "哲学", "人物伝", "教訓",
]

# ── Tính năng tự động ────────────────────────────────────────────
TU_DONG_DONG_POPUP  = True  # Tự động đóng popup cookie/GDPR
KIEM_TRA_PROXY      = True  # Kiểm tra proxy trước khi chạy
THU_LAI_KHI_LOI     = 1    # Số lần thử lại khi profile lỗi

# ── Log ──────────────────────────────────────────────────────────
LOG_FILE = "logs/nuoi_kenh_log.txt"   # "" để tắt

# ── Domains quảng cáo (dùng để nhận diện tab quảng cáo) ─────────
DOMAINS_QUANG_CAO = [
    "googleadservices.com", "googlesyndication.com", "doubleclick.net",
    "pagead2.googlesyndication.com", "adservice.google.com",
    "taboola.com", "outbrain.com", "mgid.com", "revcontent.com",
    "contentad.net", "adnxs.com", "adsrvr.org", "rubiconproject.com",
    "openx.net", "pubmatic.com", "casalemedia.com", "criteo.com",
    "adcolony.com", "applovin.com", "mopub.com", "inmobi.com",
    "amazon-adsystem.com", "media.net", "zedo.com", "advertising.com",
    "adblade.com", "adform.net", "smartadserver.com", "bidswitch.net",
    "lijit.com", "sovrn.com", "rhythmone.com", "sharethrough.com",
    "spotxchange.com", "tremorvideo.com", "yieldmo.com",
    "popads.net", "popcash.net", "propellerads.com", "adcash.com",
    "hilltopads.net", "trafficjunky.com", "clickadu.com",
    "googletagmanager.com", "hotjar.com", "mouseflow.com",
]
