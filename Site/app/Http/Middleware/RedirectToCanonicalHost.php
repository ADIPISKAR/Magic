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

        $requestUri = (string) $request->server('REQUEST_URI', $request->getRequestUri());
        $path = parse_url($requestUri, PHP_URL_PATH) ?: '/';
        $hasTrailingSlash = $path !== '/' && str_ends_with($path, '/');
        $hasAlternateHost = $canonicalHost && strcasecmp($request->getHost(), $canonicalHost) !== 0;

        if ($hasAlternateHost || $hasTrailingSlash) {
            $canonicalPath = $hasTrailingSlash ? rtrim($path, '/') : $path;
            $query = $request->getQueryString();

            return redirect()->away(
                rtrim($canonicalUrl, '/').$canonicalPath.($query ? '?'.$query : ''),
                301
            );
        }

        return $next($request);
    }
}
