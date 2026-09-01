<?php

use Illuminate\Support\Facades\Route;

Route::get('/sitemap.xml', function () {
    return response()->view('sitemap')->header('Content-Type', 'application/xml');
});

Route::get('/robots.txt', function () {
    return response("User-agent: *\nDisallow:\nSitemap: ".config('seo.canonical_url')."/sitemap.xml\n")
        ->header('Content-Type', 'text/plain');
});

Route::get('/', function () {
    return view('welcome');
})->name('home');

Route::get('/{service}', function (string $service) {
    $page = config("seo_pages.{$service}");
    abort_unless(is_array($page), 404);

    return view('service', ['page' => $page, 'slug' => $service]);
})->where('service', implode('|', array_map(fn ($slug) => preg_quote($slug, '/'), array_keys(config('seo_pages')))))
    ->name('service');
