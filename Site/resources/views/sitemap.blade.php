<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{{ config('seo.canonical_url') }}/</loc>
        <lastmod>{{ config('seo.home_lastmod') }}</lastmod>
    </url>
    @foreach (config('seo_pages') as $slug => $page)
    <url>
        <loc>{{ config('seo.canonical_url') }}/{{ $slug }}</loc>
        <lastmod>{{ $page['updated_at'] }}</lastmod>
    </url>
    @endforeach
    <url>
        <loc>{{ config('seo.canonical_url') }}/portfolio</loc>
        <lastmod>{{ collect(config('portfolio'))->max('updated_at') }}</lastmod>
    </url>
    @foreach (config('portfolio') as $slug => $project)
    <url>
        <loc>{{ config('seo.canonical_url') }}/portfolio/{{ $slug }}</loc>
        <lastmod>{{ $project['updated_at'] }}</lastmod>
    </url>
    @endforeach
</urlset>
