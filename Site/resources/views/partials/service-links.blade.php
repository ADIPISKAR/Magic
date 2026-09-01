<nav class="service_links" aria-label="Направления ремонта">
    @foreach (config('seo_pages') as $serviceSlug => $servicePage)
        <a href="{{ route('service', ['service' => $serviceSlug], false) }}" @if (($slug ?? null) === $serviceSlug) aria-current="page" @endif>
            <span>{{ $servicePage['name'] }}</span><span aria-hidden="true">↗</span>
        </a>
    @endforeach
</nav>
