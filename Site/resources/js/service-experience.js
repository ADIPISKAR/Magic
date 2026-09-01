document.addEventListener('DOMContentLoaded', () => {
	document.querySelectorAll('[data-hero-stack]').forEach((stack) => {
		const cards = [...stack.querySelectorAll('.hero_card')];
		if (cards.length < 2) return;

		const hoverQuery = window.matchMedia('(hover: hover) and (pointer: fine)');
		const transitionDuration = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 20 : 650;
		let queue = cards;
		let isAnimating = false;

		const setFlipped = (card, isFlipped) => {
			card.classList.toggle('is-flipped', isFlipped);
			card.setAttribute('aria-pressed', String(isFlipped));
		};

		const updatePositions = () => {
			queue.forEach((card, position) => {
				card.dataset.position = position;
				card.tabIndex = position === 0 ? 0 : -1;
				if (position === 0) card.removeAttribute('aria-hidden');
				else card.setAttribute('aria-hidden', 'true');
			});
		};

		const moveToNextCard = (card) => {
			if (isAnimating || card.dataset.position !== '0') return;

			isAnimating = true;
			card.classList.remove('is-hover-flipped', 'is-click-flipped');
			setFlipped(card, false);
			card.classList.add('is-leaving');

			window.setTimeout(() => {
				queue = [...queue.slice(1), queue[0]];
				card.classList.remove('is-leaving');
				updatePositions();
				window.setTimeout(() => { isAnimating = false; }, transitionDuration);
			}, transitionDuration);
		};

		cards.forEach((card) => {
			card.addEventListener('mouseenter', () => {
				if (!hoverQuery.matches || isAnimating || card.dataset.position !== '0' || card.classList.contains('is-click-flipped')) return;
				card.classList.add('is-hover-flipped');
				setFlipped(card, true);
			});

			card.addEventListener('mouseleave', () => {
				if (!hoverQuery.matches) return;
				card.classList.remove('is-hover-flipped');
				if (!card.classList.contains('is-click-flipped') && card.classList.contains('is-flipped')) moveToNextCard(card);
			});

			card.addEventListener('click', () => {
				if (isAnimating || card.dataset.position !== '0') return;
				if (card.classList.contains('is-click-flipped')) {
					moveToNextCard(card);
					return;
				}

				card.classList.add('is-click-flipped');
				card.classList.remove('is-hover-flipped');
				setFlipped(card, true);
			});

			card.addEventListener('keydown', (event) => {
				if (event.key === 'ArrowRight') {
					event.preventDefault();
					moveToNextCard(card);
				} else if (event.key === 'Escape') {
					card.classList.remove('is-click-flipped', 'is-hover-flipped');
					setFlipped(card, false);
				}
			});
		});

		updatePositions();
	});

	document.querySelectorAll('[data-service-planner]').forEach((planner) => {
		const tabs = [...planner.querySelectorAll('[data-service-scenario]')];
		const panels = [...planner.querySelectorAll('[data-service-scenario-panel]')];

		if (!tabs.length || tabs.length !== panels.length) return;

		const activate = (index, moveFocus = false) => {
			tabs.forEach((tab, tabIndex) => {
				const isActive = tabIndex === index;
				tab.setAttribute('aria-selected', String(isActive));
				tab.tabIndex = isActive ? 0 : -1;
				panels[tabIndex].hidden = !isActive;
				panels[tabIndex].classList.toggle('is-active', isActive);
			});

			if (moveFocus) tabs[index].focus();
		};

		tabs.forEach((tab, index) => {
			tab.addEventListener('click', () => activate(index));
			tab.addEventListener('keydown', (event) => {
				let nextIndex = index;
				if (event.key === 'ArrowRight' || event.key === 'ArrowDown') nextIndex = (index + 1) % tabs.length;
				else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') nextIndex = (index - 1 + tabs.length) % tabs.length;
				else if (event.key === 'Home') nextIndex = 0;
				else if (event.key === 'End') nextIndex = tabs.length - 1;
				else return;

				event.preventDefault();
				activate(nextIndex, true);
			});
		});

		activate(Math.max(tabs.findIndex((tab) => tab.getAttribute('aria-selected') === 'true'), 0));
	});

	document.querySelectorAll('[data-service-checklist]').forEach((checklist) => {
		const items = [...checklist.querySelectorAll('[data-service-check-item]')];
		const status = checklist.querySelector('[data-service-checklist-status]');
		const bar = checklist.querySelector('[data-service-checklist-bar]');
		const hint = checklist.querySelector('[data-service-checklist-hint]');
		const reset = checklist.querySelector('[data-service-checklist-reset]');

		if (!items.length || !status || !bar || !hint) return;

		const render = () => {
			const completed = items.filter((item) => item.checked).length;
			const remaining = items.length - completed;
			status.textContent = `${completed} из ${items.length}`;
			bar.style.width = `${(completed / items.length) * 100}%`;
			checklist.classList.toggle('is-complete', completed === items.length);

			if (completed === items.length) {
				hint.textContent = 'Отличная подготовка. На замере останется проверить объект и уточнить детали сметы.';
			} else if (completed > 0) {
				hint.textContent = `Осталось ${remaining}. Недостающие решения можно принять вместе со специалистом.`;
			} else {
				hint.textContent = 'Начните с любого пункта — всё остальное обсудим на замере.';
			}
		};

		items.forEach((item) => item.addEventListener('change', render));
		reset?.addEventListener('click', () => {
			items.forEach((item) => { item.checked = false; });
			render();
			items[0].focus();
		});
		render();
	});
});
