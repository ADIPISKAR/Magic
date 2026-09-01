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
</urlset>
