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
            ->assertSee('<meta name="google-site-verification" content="9QjxoE4Ov-scAYEmS3oMIzR8NGySSXQze6AUJpLCVhI">', false)
            ->assertSee('<meta property="og:url" content="https://magiarnd.ru/">', false)
            ->assertSee('Ремонт квартир под ключ в Ростове-на-Дону — от 5 000 ₽/м² | Магия', false)
            ->assertSee('"priceRange": "от 5 000 ₽/м²"', false);
    }

    public function test_homepage_has_clear_section_navigation(): void
    {
        $this->get('/')
            ->assertOk()
            ->assertSee('class="service_header home_header"', false)
            ->assertSee('data-mobile-header', false)
            ->assertSee('data-mobile-menu-toggle', false)
            ->assertSee('id="mobile-home-menu"', false)
            ->assertSee('href="#portfolio"', false)
            ->assertSee('href="#services"', false)
            ->assertSee('href="#reviews"', false)
            ->assertSee('href="#work-steps"', false)
            ->assertSee('href="#contacts"', false)
            ->assertSee('href="https://t.me/SergeyWright"', false)
            ->assertSee('href="https://max.ru/', false)
            ->assertSee('class="request_modal_submit"', false)
            ->assertSee('Удобнее написать?')
            ->assertSee('data-exit-modal', false)
            ->assertSee('Получить скидку 10%')
            ->assertSee('Exit-intent — скидка на дизайн-проект')
            ->assertSee('name="privacy_consent"', false)
            ->assertSee('Политика обработки персональных данных')
            ->assertSee('ИНН '.config('seo.operator_inn'))
            ->assertSee('href="tel:'.config('seo.phone').'"', false);
    }

    public function test_legal_pages_identify_the_operator_and_explain_consent(): void
    {
        foreach (['/privacy', '/personal-data-consent'] as $path) {
            $this->get($path)
                ->assertOk()
                ->assertSee(config('seo.operator_name'))
                ->assertSee(config('seo.operator_inn'))
                ->assertSee(config('seo.street_address'))
                ->assertSee('noindex,follow', false);
        }
    }

    public function test_homepage_calculator_uses_published_rates(): void
    {
        $response = $this->get('/');

        $response->assertOk()
            ->assertSee('data-repair-calculator', false)
            ->assertSee('data-calculator-area', false)
            ->assertSee('Точная смета')
            ->assertSee('12 000 ₽/м²');

        $this->assertSame(5000, config('calculator.properties.new.plans.0.rate'));
        $this->assertSame(22000, config('calculator.properties.secondary.plans.3.rate'));
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

    public function test_service_pages_have_distinct_metadata_and_canonical_urls(): void
    {
        $titles = [];
        foreach (config('seo_pages') as $slug => $page) {
            $experience = config("service_content.{$slug}");
            $response = $this->get('/'.$slug.'?utm_source=test');
            $response->assertOk()
                ->assertSee('<link rel="canonical" href="https://magiarnd.ru/'.$slug.'">', false)
                ->assertSee($page['heading'])
                ->assertSee('class="service_header service_header_desktop"', false)
                ->assertSee('class="mobile_header service_mobile_header"', false)
                ->assertSee('id="mobile-service-menu"', false)
                ->assertSee('data-mobile-menu-toggle', false)
                ->assertSee('data-hero-stack', false)
                ->assertSee('data-service-planner', false)
                ->assertSee('data-service-checklist', false)
                ->assertSee($experience['planner_heading'])
                ->assertSee($experience['stages_heading'])
                ->assertSee($page['unit_prices_heading'])
                ->assertSee('data-lead-form', false)
                ->assertSee('tel:'.config('seo.phone'), false);
            foreach ($page['unit_prices'] as [$label, $price]) {
                $response->assertSee($label)->assertSee($price);
            }
            foreach ($experience['hero_slides'] as $slide) {
                $this->assertStringStartsWith('images/Portf/', $slide['image']);
                $this->assertFileExists(public_path($slide['image']));
                $response->assertSee($slide['image'], false)->assertSee($slide['title']);
            }
            foreach ($experience['scenarios'] as $scenario) {
                $response->assertSee($scenario['label'])->assertSee($scenario['title']);
            }
            $this->assertSame(1, preg_match_all('/<h1[ >]/', $response->getContent()));
            preg_match('/<script type="application\/ld\+json">(.*?)<\/script>/s', $response->getContent(), $match);
            $schema = json_decode($match[1], true, flags: JSON_THROW_ON_ERROR);
            $this->assertSame('Service', $schema['@graph'][1]['@type']);
            $this->assertSame('https://magiarnd.ru/'.$slug, $schema['@graph'][1]['url']);
            $faqSchema = collect($schema['@graph'])->firstWhere('@type', 'FAQPage');
            $this->assertNotNull($faqSchema);
            $this->assertCount(count($page['faq']) + count($experience['faq']), $faqSchema['mainEntity']);
            $titles[] = $page['title'];
        }
        $this->assertCount(count($titles), array_unique($titles));
    }

    public function test_all_service_pages_are_linked_and_listed_in_the_sitemap(): void
    {
        $home = $this->get('/');
        $sitemap = $this->get('/sitemap.xml');
        foreach (config('seo_pages') as $slug => $page) {
            $home->assertSee('href="/'.$slug.'"', false);
            $sitemap->assertSee('<loc>https://magiarnd.ru/'.$slug.'</loc>', false)
                ->assertSee('<lastmod>'.$page['updated_at'].'</lastmod>', false);
        }
        $this->get('/not-a-service')->assertNotFound();
    }

    public function test_sitemap_dates_do_not_change_without_a_content_update(): void
    {
        $before = $this->get('/sitemap.xml')->getContent();
        $this->travel(20)->days();
        $this->assertSame($before, $this->get('/sitemap.xml')->getContent());
        $this->travelBack();
    }
}
