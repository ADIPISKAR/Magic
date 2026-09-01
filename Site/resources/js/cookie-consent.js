document.addEventListener('DOMContentLoaded', () => {
	const notice = document.querySelector('[data-cookie-notice]');
	if (!notice) return;

	const consentKey = 'magic_cookie_consent_v1';
	const preview = new URLSearchParams(window.location.search).get('preview') === 'cookie1';
	const rejectButton = notice.querySelector('[data-cookie-reject]');

	const getDecision = () => {
		try {
			return window.localStorage.getItem(consentKey);
		} catch {
			return null;
		}
	};

	const setDecision = (decision) => {
		try {
			window.localStorage.setItem(consentKey, decision);
		} catch {
			// The choice applies to the current page when storage is unavailable.
		}
	};

	const open = () => {
		notice.classList.add('is-open');
		notice.setAttribute('aria-hidden', 'false');
	};

	const close = () => {
		notice.classList.remove('is-open');
		notice.setAttribute('aria-hidden', 'true');
	};

	const loadExternalContent = () => {
		document.querySelectorAll('[data-cookie-src]').forEach((frame) => {
			if (!frame.getAttribute('src')) frame.setAttribute('src', frame.dataset.cookieSrc);
			frame.closest('[data-cookie-embed]')?.classList.add('is-loaded');
		});
	};

	document.querySelectorAll('[data-cookie-accept]').forEach((button) => button.addEventListener('click', () => {
		setDecision('analytics');
		window.magicMetrikaInit?.();
		loadExternalContent();
		close();
	}));

	rejectButton?.addEventListener('click', () => {
		const analyticsWasLoaded = getDecision() === 'analytics' || window.magicMetrikaLoaded;
		setDecision('essential');
		close();
		if (analyticsWasLoaded) window.location.reload();
	});

	document.querySelectorAll('[data-cookie-settings]').forEach((button) => {
		button.addEventListener('click', open);
	});

	if (getDecision() === 'analytics') loadExternalContent();

	if (preview || !getDecision()) {
		window.setTimeout(open, preview ? 150 : 600);
	}
});
