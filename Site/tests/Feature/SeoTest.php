<?php

namespace Tests\Feature;

use Tests\TestCase;

class SeoTest extends TestCase
{
    public function test_alternate_production_host_redirects_to_canonical_host(): void
    {
        $this->app->detectEnvironment(fn () => 'production');

        $response = $this->get('https://www.magiarnd.ru/example?source=test');

        $response->assertRedirect('https://magiarnd.ru/example?source=test');
        $response->assertStatus(301);
    }

    public function test_canonical_production_host_does_not_redirect(): void
    {
        $this->app->detectEnvironment(fn () => 'production');

        $this->get('https://magiarnd.ru/')->assertOk();
    }

    public function test_homepage_uses_stable_canonical_metadata(): void
    {
        $this->get('https://magiarnd.ru/')
            ->assertOk()
            ->assertSee('<link rel="canonical" href="https://magiarnd.ru/">', false)
            ->assertSee('<meta property="og:url" content="https://magiarnd.ru/">', false);
    }

    public function test_robots_and_sitemap_use_the_canonical_host(): void
    {
        $this->get('/robots.txt')
            ->assertOk()
            ->assertSee('Sitemap: https://magiarnd.ru/sitemap.xml', false);

        $this->get('/sitemap.xml')
            ->assertOk()
            ->assertSee('<loc>https://magiarnd.ru/</loc>', false);
    }
}
