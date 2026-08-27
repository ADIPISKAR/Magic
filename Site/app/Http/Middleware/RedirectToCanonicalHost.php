<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class RedirectToCanonicalHost
{
    /**
     * Redirect alternate production hosts (for example www) to the canonical host.
     */
    public function handle(Request $request, Closure $next): Response
    {
        if (! app()->environment('production')) {
            return $next($request);
        }

        $canonicalUrl = config('seo.canonical_url');
        $canonicalHost = parse_url($canonicalUrl, PHP_URL_HOST);

        if ($canonicalHost && strcasecmp($request->getHost(), $canonicalHost) !== 0) {
            return redirect()->away($canonicalUrl.$request->getRequestUri(), 301);
        }

        return $next($request);
    }
}
