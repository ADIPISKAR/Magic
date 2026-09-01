document.addEventListener('DOMContentLoaded', () => {
	const modal = document.querySelector('[data-exit-modal]');
	if (!modal) return;

	const storageKey = 'magic_exit_offer_seen_v1';
	const preview = new URLSearchParams(window.location.search).get('preview') === 'exit-popup1';
	const coarsePointer = window.matchMedia('(pointer: coarse)').matches;
	let armed = false;
	let shown = false;
	let lastFocused = null;
	let highestScroll = window.scrollY;

	const wasSeen = () => {
		try {
			return window.sessionStorage.getItem(storageKey) === '1';
		} catch {
			return shown;
		}
	};

	const remember = () => {
		shown = true;
		try {
			window.sessionStorage.setItem(storageKey, '1');
		} catch {
			// The in-memory flag still prevents repeated displays.
		}
	};

	const open = (force = false) => {
		if ((!force && (!armed || wasSeen())) || document.querySelector('.request_modal.is-open, .cookie_notice.is-open')) return;
		lastFocused = document.activeElement;
		remember();
		modal.classList.add('is-open');
		modal.setAttribute('aria-hidden', 'false');
		document.body.classList.add('modal-is-open');
		modal.querySelector('[data-exit-accept]')?.focus();
	};

	const close = (restoreFocus = true) => {
		modal.classList.remove('is-open');
		modal.setAttribute('aria-hidden', 'true');
		if (!document.querySelector('.request_modal.is-open')) {
			document.body.classList.remove('modal-is-open');
		}
		if (restoreFocus && lastFocused instanceof HTMLElement) lastFocused.focus();
	};

	modal.querySelectorAll('[data-exit-close]').forEach((button) => {
		button.addEventListener('click', () => close());
	});

	modal.querySelector('[data-exit-accept]')?.addEventListener('click', () => close(false));

	document.addEventListener('keydown', (event) => {
		if (event.key === 'Escape' && modal.classList.contains('is-open')) close();
	});

	if (preview) {
		window.setTimeout(() => open(true), 450);
		return;
	}

	window.setTimeout(() => {
		armed = true;
	}, 10000);

	if (!coarsePointer) {
		document.addEventListener('mouseout', (event) => {
			if (event.clientY <= 0 && !event.relatedTarget) open();
		});
		return;
	}

	window.addEventListener('scroll', () => {
		const currentScroll = window.scrollY;
		highestScroll = Math.max(highestScroll, currentScroll);
		const pageHeight = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
		const readEnough = highestScroll / pageHeight >= 0.55;
		const returningUp = highestScroll - currentScroll >= 240;

		if (readEnough && returningUp) open();
	}, { passive: true });
});
