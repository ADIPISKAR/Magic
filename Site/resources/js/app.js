document.addEventListener('DOMContentLoaded', () => {
	const navigation = document.querySelector('.navigation');
	const navigationButtons = [...document.querySelectorAll('.navigation .Button_Navigation')];
	const activeNavigation = navigation?.querySelector('.Active_Navigation');

	if (navigation && activeNavigation && navigationButtons.length) {
		const activeNavigationPadding = Number.parseFloat(
			window.getComputedStyle(activeNavigation).paddingLeft,
		);
		activeNavigation.style.setProperty('--active-navigation-padding', `${activeNavigationPadding}px`);

		const moveActiveNavigation = (button) => {
			const offset = button.offsetLeft - activeNavigation.offsetLeft - (
				button === activeNavigation ? 0 : activeNavigationPadding
			);
			const buttonWidth = button === activeNavigation
				? button.offsetWidth - activeNavigationPadding * 2
				: button.offsetWidth;

			activeNavigation.style.setProperty('--active-navigation-offset', `${offset}px`);
			activeNavigation.style.setProperty('--active-navigation-width', `${buttonWidth}px`);
		};

		const resetActiveNavigation = () => {
			navigation.classList.remove('is-hovering');
			moveActiveNavigation(activeNavigation);
		};

		navigationButtons.forEach((button) => {
			button.addEventListener('mouseenter', () => {
				navigation.classList.add('is-hovering');
				moveActiveNavigation(button);
			});
		});

		navigation.addEventListener('mouseleave', resetActiveNavigation);
		window.addEventListener('resize', () => {
			moveActiveNavigation(navigation.matches(':hover')
				? navigationButtons.find((button) => button.matches(':hover')) || activeNavigation
				: activeNavigation);
		});

		resetActiveNavigation();
	}

	const cards = [...document.querySelectorAll('.hero_card')];

	if (!cards.length) {
		return;
	}

	let queue = cards;
	let isAnimating = false;

	const updatePositions = () => {
		queue.forEach((card, position) => {
			card.dataset.position = position;
		});
	};

	const moveToNextCard = (card) => {
		if (isAnimating || card.dataset.position !== '0') {
			return;
		}

		isAnimating = true;
		card.classList.remove('is-hover-flipped', 'is-click-flipped');
		card.classList.remove('is-flipped');
		card.classList.add('is-leaving');

		window.setTimeout(() => {
			queue = [...queue.slice(1), queue[0]];
			card.classList.remove('is-leaving');
			updatePositions();

			window.setTimeout(() => {
				isAnimating = false;
			}, 650);
		}, 650);
	};

	cards.forEach((card) => {
		card.addEventListener('mouseenter', () => {
			if (!isAnimating && card.dataset.position === '0' && !card.classList.contains('is-click-flipped')) {
				card.classList.add('is-hover-flipped');
				card.classList.add('is-flipped');
			}
		});

		card.addEventListener('mouseleave', () => {
			card.classList.remove('is-hover-flipped');

			if (!card.classList.contains('is-click-flipped') && card.classList.contains('is-flipped')) {
				moveToNextCard(card);
			}
		});

		card.addEventListener('click', (event) => {
			event.stopPropagation();

			if (isAnimating || card.dataset.position !== '0') {
				return;
			}

			if (card.classList.contains('is-click-flipped')) {
				moveToNextCard(card);
				return;
			}

			if (card.classList.toggle('is-click-flipped')) {
				card.classList.remove('is-hover-flipped');
				card.classList.add('is-flipped');
				return;
			}

			card.classList.remove('is-flipped');
		});
	});

	updatePositions();
});
