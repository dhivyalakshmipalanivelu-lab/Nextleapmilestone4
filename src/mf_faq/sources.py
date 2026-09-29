"""Official HDFC URLs for the demo corpus. No other sources belong here."""


def plan_from_url(url: str) -> str:
    path = url.lower()
    if "/direct" in path:
        return "direct"
    if "/regular" in path:
        return "regular"
    return "unknown"


_ROWS = [
    (
        "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
        "HDFC Large Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Large%20Cap%20Fund_August%2026.pdf",
        "HDFC Large Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
        "HDFC Large Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-02/HDFC%20Large%20Cap%20Fund%20Leaflet%20%28Jan%202026%29.pdf",
        "HDFC Large Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
        "HDFC Flexi Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Flexi%20Cap%20Fund_August%2026.pdf",
        "HDFC Flexi Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf",
        "HDFC Flexi Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-06/Leaflet-HDFC%20Flexi%20Cap%20Fund-May%202026.pdf",
        "HDFC Flexi Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Mid%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf",
        "HDFC Mid Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Mid-Cap%20Fund_August%2026.pdf",
        "HDFC Mid Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Mid%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf",
        "HDFC Mid Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-07/HDFC%20Mid%20Cap%20Fund%20Leaflet%20%28As%20of%20May%2029%2C%202026%29.pdf",
        "HDFC Mid Cap Fund",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025.pdf",
        "HDFC ELSS Tax Saver",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/Others/2026-07/Fund%20Facts%20-%20HDFC%20TaxSaver%20Fund_July%2026.pdf",
        "HDFC ELSS Tax Saver",
    ),
    (
        "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025_0.pdf",
        "HDFC ELSS Tax Saver",
    ),
]

FUND_SCHEMES = [
    "HDFC Large Cap Fund",
    "HDFC Flexi Cap Fund",
    "HDFC Mid Cap Fund",
    "HDFC ELSS Tax Saver",
]

SOURCES = [
    {"url": url, "scheme": scheme, "plan": plan_from_url(url)}
    for url, scheme in _ROWS
]
