"""Visualization layer for Magic SEO analytics.

Every chart in this package renders as a single flat PNG suitable for
sending straight into Telegram (sendPhoto / sendMediaGroup). The look is
shared across all charts via :mod:`charts.theme` — one visual language,
not a different style per script.

Modules:
    theme      -- colors, typography, figure sizes, shared drawing helpers.
    cards      -- small reusable building blocks (KPI tile, sparkline, chip).
    positions  -- Topvisor position charts (line, distribution, growth/drop).
    traffic    -- Yandex Metrika traffic + goals charts.
    wordstat   -- keyword frequency chart.
    dashboard  -- composite dashboards that assemble the pieces above.
    cache      -- on-disk PNG cache keyed by (report_type, period, data_version).
"""
