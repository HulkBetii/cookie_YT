# -*- coding: utf-8 -*-
"""
CẤU HÌNH — Thị Trường US (Mỹ) & Tối Ưu Cookie Trust Score.
File cấu hình tập trung cho toàn bộ kịch bản nuôi kênh YouTube và lướt web hệ sinh thái Google / US.
"""

# ── GPM Login ────────────────────────────────────────────────────
GPM_API_URL             = "http://127.0.0.1:19995"
GPM_BROWSER_DIR         = r"C:\GPM\GPMLogin\gpm_browser"
SO_LUONG_CHAY_SONG_SONG = 1   # 1 = tuần tự từng profile; > 1 = chạy song song N profile
GPM_ADDITIONAL_ARGS     = "--lang=en-US,en --disable-notifications"  # Chromium flags tiếng Anh US

# ── Múi giờ sinh học US ──────────────────────────────────────────
MUI_GIO_US = "America/New_York"  # Múi giờ US để tính toán chu kỳ thức/ngủ (EST/EDT)

# ── YouTube ──────────────────────────────────────────────────────
SO_VIDEO        = 4       # Số video mục tiêu mỗi session
SO_VIDEO_MIN    = 2       # Min video mỗi session (random weighted)
SO_VIDEO_MAX    = 5       # Max video mỗi session
MIN_GIAY_XEM    = 60      # Thời gian xem tối thiểu (giây)
MAX_GIAY_XEM    = 130     # Thời gian xem tối đa (giây)

# ── Google News US ───────────────────────────────────────────────
SU_DUNG_GOOGLE_NEWS = True
SO_TIN_DOC          = 2   # Số bài báo mặc định
SO_TIN_DOC_MIN      = 1   # Min bài báo mỗi session
SO_TIN_DOC_MAX      = 3   # Max bài báo mỗi session

NEWS_SITES = [
    "https://www.cnn.com",
    "https://www.nytimes.com",
    "https://techcrunch.com",
    "https://www.forbes.com",
    "https://apnews.com",
    "https://www.reuters.com",
    "https://www.washingtonpost.com",
]

# ── Google Maps US (Tạo tín hiệu địa lý & Local Trust) ───────────
SU_DUNG_GOOGLE_MAPS = True
SO_MAPS_MIN         = 1
SO_MAPS_MAX         = 2

MAPS_CITIES_QUERIES = [
    "coffee shops in Brooklyn NYC",
    "best pizza in Manhattan",
    "public library in Chicago",
    "hiking trails near Los Angeles",
    "best ramen in Austin Texas",
    "bookstores in Seattle downtown",
    "fitness centers in Miami",
    "art museums in San Francisco",
    "bakeries in Boston",
    "parks near Denver Colorado",
]

# ── Reddit US (Cộng đồng số 1 US, kích hoạt cookie Google Ads) ───
SU_DUNG_REDDIT   = True
SO_REDDIT_MIN   = 1
SO_REDDIT_MAX   = 2

REDDIT_SUBREDDITS = [
    "technology",
    "AskReddit",
    "todayilearned",
    "mildlyinteresting",
    "productivity",
    "gadgets",
    "science",
    "Futurology",
]

# ── Wikipedia US (Nâng cao tri thức & duyệt liên kết tự nhiên) ───
SU_DUNG_WIKIPEDIA = True
SO_WIKI_MIN       = 1
SO_WIKI_MAX       = 2

WIKIPEDIA_TOPICS = [
    "Artificial intelligence",
    "Space exploration",
    "Renewable energy",
    "History of the Internet",
    "Cognitive science",
    "James Webb Space Telescope",
    "Quantum computing",
    "Neuroplasticity",
    "Renaissance",
    "Silicon Valley",
]

# ── Google Search US ──────────────────────────────────────────────
TIM_KIEM_GOOGLE = True
SO_GOOGLE_MIN   = 1
SO_GOOGLE_MAX   = 2

GOOGLE_KEYWORDS = [
    "how to improve focus and productivity",
    "best podcast episodes for learning",
    "morning routine for mental clarity",
    "future of artificial intelligence 2026",
    "healthy meal prep ideas for the week",
    "how to start investing in index funds",
    "top documentary films to watch",
    "mechanical keyboard switches comparison",
    "James Webb telescope latest images",
    "minimalist desk setup ideas",
    "how does neuroplasticity work",
    "best tech gadgets under 100",
    "daily habits of successful people",
    "how to learn faster feynman technique",
]
GOOGLE_SEARCH_QUERIES = GOOGLE_KEYWORDS

# ── Twitter / X US ────────────────────────────────────────────────
LUOT_TWITTER   = True
SO_TWITTER_MIN = 1
SO_TWITTER_MAX = 2

TWITTER_KEYWORDS = [
    "AI technology",
    "SpaceX launch",
    "Productivity hacks",
    "Tech news",
    "Science discoveries",
    "Personal finance",
    "Daily motivation",
    "Web development",
]

# ── Google Finance US ─────────────────────────────────────────────
SU_DUNG_GOOGLE_FINANCE = True
SO_FINANCE_MIN         = 1
SO_FINANCE_MAX         = 2

FINANCE_TICKERS = [
    "AAPL:NASDAQ",
    "NVDA:NASDAQ",
    "MSFT:NASDAQ",
    "GOOGL:NASDAQ",
    "AMZN:NASDAQ",
    "SPY:NYSEARCA",
    "TSLA:NASDAQ",
]

# ── Vòng lặp & Thời gian nghỉ ────────────────────────────────────
SO_VONG_LAP         = 0     # 0 = chạy mãi; số > 0 = chạy N vòng
NGHI_GIUA_VONG_MIN  = 300   # Nghỉ bình thường min (giây) — 5 phút
NGHI_GIUA_VONG_MAX  = 900   # Nghỉ bình thường max (giây) — 15 phút
TRON_PROFILES       = True  # Xáo thứ tự profile mỗi vòng

# ── Session timing variation ─────────────────────────────────────
NGHI_DAI_XAC_SUAT  = 0.08   # 8%  → nghỉ dài (2-4 tiếng)
NGHI_NGAN_XAC_SUAT = 0.15   # 15% → nghỉ rất ngắn (1-3 phút)
NGHI_DAI_MIN       = 7200   # 2 tiếng
NGHI_DAI_MAX       = 14400  # 4 tiếng
NGHI_NGAN_MIN      = 60
NGHI_NGAN_MAX      = 180

# ── Nhịp sinh học theo giờ US trong ngày (Circadian - EST) ────────
KHUNG_GIO_NGHI_DAI = {
    (1, 6):   8.0,   # 1h-6h sáng US: đang ngủ, hầu như nghỉ dài
    (6, 9):   1.5,   # 6h-9h sáng US: chuẩn bị đi làm/học
    (9, 12):  0.6,   # 9h-12h trưa US: giờ làm việc buổi sáng
    (12, 14): 0.3,   # 12h-14h chiều US: giờ nghỉ trưa
    (14, 19): 0.6,   # 14h-19h tối US: giờ làm việc buổi chiều
    (19, 24): 0.2,   # 19h-24h tối US: cao điểm giải trí, ít nghỉ dài
    (0, 1):   0.4,   # 0h-1h đêm US: giảm dần
}

HE_SO_HOAT_DONG_THEO_GIO = {
    (1, 6):   0.15,  # ban đêm US — hoạt động tối thiểu
    (6, 9):   0.7,
    (9, 12):  0.85,
    (12, 14): 1.1,
    (14, 19): 0.9,
    (19, 24): 1.2,   # cao điểm buổi tối US
    (0, 1):   0.6,
}

# ── Từ khóa xoay vòng YouTube US ─────────────────────────────────
DANH_SACH_TU_KHOA = [
    "Huberman Lab productivity hacks",
    "Lex Fridman podcast AI",
    "MKBHD tech review latest",
    "Personal finance for beginners",
    "Morning routine of billionaires",
    "James Webb space telescope discoveries",
    "How to stop procrastinating psychology",
    "Daily habits for high performance",
    "Deep work focus music for study",
    "Stock market investing strategies",
    "Cybersecurity awareness tips",
    "Feynman technique learning fast",
]

TU_KHOA_LIEN_QUAN = [
    "productivity tips", "focus and discipline", "tech reviews 2026",
    "personal finance guide", "investing basics", "science documentaries",
    "cognitive enhancement", "podcast highlights", "healthy morning habits",
    "space exploration updates", "artificial intelligence future",
    "smart study methods", "deep focus playlist", "entrepreneurship tips",
]

# ── Gmail accounts ───────────────────────────────────────────────
GMAIL_ACCOUNTS: dict = {}

# ── Tính năng tự động ────────────────────────────────────────────
TU_DONG_DONG_POPUP  = True  # Tự động đóng popup cookie/GDPR
KIEM_TRA_PROXY      = True  # Kiểm tra proxy trước khi chạy
THU_LAI_KHI_LOI     = 1     # Số lần thử lại khi profile lỗi

# ── Log ──────────────────────────────────────────────────────────
LOG_FILE = "logs/nuoi_kenh_log.txt"

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
