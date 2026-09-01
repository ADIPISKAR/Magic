<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>@yield('title') | Магия</title>
    <meta name="description" content="@yield('description')">
    <meta name="robots" content="noindex,follow">
    <link rel="canonical" href="{{ config('seo.canonical_url') }}@yield('path')">
    <link rel="icon" type="image/svg+xml" href="{{ asset('favicon.svg') }}">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @include('partials.metrika')
</head>
<body class="legal-page">
    <header class="legal_header">
        <a href="{{ route('home', [], false) }}" aria-label="Магия — главная">
            <img src="{{ asset('images/logo.svg') }}" width="189" height="46" alt="Магия" class="logo">
        </a>
        <a href="{{ route('home', [], false) }}">Вернуться на сайт ←</a>
    </header>

    <main class="legal_content">
        @yield('content')
    </main>

    @include('partials.legal-footer')
    @include('partials.cookie-consent')
</body>
</html>
