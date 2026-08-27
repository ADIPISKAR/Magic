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
            ->assertSee('<meta property="og:url" content="https://magiarnd.ru/">', false)
            ->assertSee('Ремонт квартир под ключ в Ростове-на-Дону — от 5 000 ₽/м² | Магия', false)
            ->assertSee('"priceRange": "от 5 000 ₽/м²"', false);
    }

    public function test_homepage_has_clear_section_navigation(): void
    {
        $this->get('/')
            ->assertOk()
            ->assertSee('href="#portfolio"', false)
            ->assertSee('href="#services"', false)
            ->assertSee('href="#reviews"', false)
            ->assertSee('href="#work-steps"', false)
            ->assertSee('href="#contacts"', false);
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
