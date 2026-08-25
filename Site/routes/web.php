<?php

use Illuminate\Support\Facades\Route;

Route::get('/sitemap.xml', function () {
    return response()->view('sitemap')->header('Content-Type', 'application/xml');
});

Route::get('/robots.txt', function () {
    return response("User-agent: *\nDisallow:\nSitemap: " . url('/sitemap.xml') . "\n")
        ->header('Content-Type', 'text/plain');
});

Route::get('/', function () {
    return view('welcome');
});
