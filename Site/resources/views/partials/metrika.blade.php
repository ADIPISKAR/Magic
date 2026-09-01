<script>
    (() => {
        const consentKey = 'magic_cookie_consent_v1';

        window.magicMetrikaInit = () => {
            if (window.magicMetrikaLoaded) return;
            window.magicMetrikaLoaded = true;

            (function(m,e,t,r,i,k,a){
                m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
                m[i].l=1*new Date();
                for (let j = 0; j < document.scripts.length; j++) {
                    if (document.scripts[j].src === r) return;
                }
                k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a);
            })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js?id=111942996', 'ym');

            ym(111942996, 'init', {
                ssr: true,
                webvisor: true,
                clickmap: true,
                ecommerce: 'dataLayer',
                referrer: document.referrer,
                url: location.href,
                accurateTrackBounce: true,
                trackLinks: true,
            });
        };

        try {
            if (window.localStorage.getItem(consentKey) === 'analytics') window.magicMetrikaInit();
        } catch {
            // Analytics remains disabled when consent storage is unavailable.
        }
    })();
</script>
