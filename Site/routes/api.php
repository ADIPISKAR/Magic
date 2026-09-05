<?php

use App\Http\Controllers\LeadController;
use App\Http\Controllers\SeoTelegramController;
use Illuminate\Support\Facades\Route;

Route::post('/leads', [LeadController::class, 'store']);
Route::post('/seo/telegram', [SeoTelegramController::class, 'show']);
