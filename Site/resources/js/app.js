import './calculator.js';
import './estimate.js';

document.addEventListener('DOMContentLoaded', () => {
	const trackGoal = (goal) => {
		if (typeof window.ym === 'function') {
			window.ym(111942996, 'reachGoal', goal, { page: window.location.pathname });
		}
	};
	document.querySelectorAll('a[href^="tel:"], a[href^="https://t.me/"], a[href^="https://max.ru/"]').forEach((link) => {
		link.addEventListener('click', () => {
			const goal = link.href.startsWith('tel:') ? 'contact_phone' : link.hostname === 't.me' ? 'contact_telegram' : 'contact_max';
			trackGoal(goal);
		});
	});
	const requestModal = document.querySelector('.request_modal');
	const modalOpenButtons = [...document.querySelectorAll('[data-modal-open]')];
	const modalCloseButtons = [...document.querySelectorAll('[data-modal-close]')];
	const leadForm = document.querySelector('[data-lead-form]');

	if (requestModal && modalOpenButtons.length) {
		const defaultLeadContext = document.querySelector('[data-lead-context]')?.textContent;
		const openModal = (button) => {
			if (!button.matches('[data-calculator-lead]')) {
				const context = document.querySelector('[data-lead-context]');
				const message = document.querySelector('[data-lead-message]');
				const source = document.querySelector('[data-lead-source]');
				if (context) context.textContent = defaultLeadContext;
				if (message) message.value = '';
				if (source) source.value = 'Форма сайта';
			}
			requestModal.classList.add('is-open');
			requestModal.setAttribute('aria-hidden', 'false');
			document.body.classList.add('modal-is-open');
			requestModal.querySelector('input')?.focus();
		};

		const closeModal = () => {
			requestModal.classList.remove('is-open');
			requestModal.setAttribute('aria-hidden', 'true');
			document.body.classList.remove('modal-is-open');
		};

		modalOpenButtons.forEach((button) => button.addEventListener('click', () => openModal(button)));
		modalCloseButtons.forEach((button) => button.addEventListener('click', closeModal));
		leadForm?.addEventListener('submit', async (event) => {
			event.preventDefault();
			const submitButton = leadForm.querySelector('button[type="submit"]');
			const status = leadForm.querySelector('.request_modal_status');
			const formData = new FormData(leadForm);

			submitButton.disabled = true;
			status.textContent = 'Отправляем заявку...';

			try {
				const response = await fetch('/api/leads', {
					method: 'POST',
					headers: {
						'Accept': 'application/json',
						'Content-Type': 'application/json',
					},
					body: JSON.stringify(Object.fromEntries(formData.entries())),
				});
				const result = await response.json();

				if (!response.ok) {
					throw new Error(response.status === 422
						? 'Проверьте имя и номер телефона.'
						: (result.message || 'Не удалось отправить заявку.'));
				}

				status.textContent = 'Заявка отправлена. Мы скоро свяжемся с вами.';
				trackGoal('lead_submit_success');
				leadForm.reset();
				window.setTimeout(closeModal, 1600);
			} catch (error) {
				status.textContent = error.message;
			} finally {
				submitButton.disabled = false;
			}
		});
		document.addEventListener('keydown', (event) => {
			if (event.key === 'Escape' && requestModal.classList.contains('is-open')) {
				closeModal();
			}
		});
	}

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

	const serviceSwitch = document.querySelector('.service_switch');
	const serviceSwitchButtons = [...document.querySelectorAll('.service_switch .switch_btn')];
	const activeSwitch = serviceSwitch?.querySelector('.enable_switch');

	if (serviceSwitch && activeSwitch && serviceSwitchButtons.length) {
		let selectedSwitch = activeSwitch;

		const moveActiveSwitch = (button) => {
			const offset = button.offsetLeft - activeSwitch.offsetLeft;
			serviceSwitch.style.setProperty('--active-switch-offset', `${offset}px`);
			serviceSwitch.style.setProperty('--active-switch-width', `${button.offsetWidth}px`);
		};

		const resetActiveSwitch = () => {
			serviceSwitch.classList.remove('is-hovering');
			moveActiveSwitch(selectedSwitch);
		};

		serviceSwitchButtons.forEach((button) => {
			button.addEventListener('mouseenter', () => {
				serviceSwitch.classList.add('is-hovering');
				moveActiveSwitch(button);
			});
		});

		serviceSwitch.addEventListener('mouseleave', resetActiveSwitch);
		window.addEventListener('resize', () => {
			moveActiveSwitch(serviceSwitch.matches(':hover')
				? serviceSwitchButtons.find((button) => button.matches(':hover')) || activeSwitch
				: selectedSwitch);
		});

		resetActiveSwitch();
		activeSwitch.classList.add('is-selected');

		const servicePriceCards = [...document.querySelectorAll('.Service_Price')];
		const servicePrice = document.querySelector('.service_price');
		const newServiceContent = servicePriceCards.map((card) => ({
			title: card.querySelector('h3').textContent,
			description: card.querySelector('.service_card_tags > p').textContent,
			tags: [...card.querySelectorAll('.service_card_tags .bord_block')].map((tag) => tag.textContent),
			price: card.querySelector('.price p').textContent,
		}));

		const switchServiceMode = (button) => {
			const isSecondary = button.dataset.serviceMode === 'secondary';

			servicePriceCards.forEach((card, index) => {
				const content = isSecondary
					? {
						title: card.dataset.secondaryTitle,
						description: card.dataset.secondaryDescription,
						tags: card.dataset.secondaryTags.split('|'),
						price: card.dataset.secondaryPrice,
					}
					: newServiceContent[index];

				card.querySelector('h3').textContent = content.title;
				card.querySelector('.service_card_tags > p').textContent = content.description;
				card.querySelector('.price p').textContent = content.price;
				card.querySelectorAll('.service_card_tags .bord_block').forEach((tag, index) => {
					tag.textContent = content.tags[index];
				});
			});

			servicePrice.classList.remove('is-changing');
			window.requestAnimationFrame(() => servicePrice.classList.add('is-changing'));

			serviceSwitchButtons.forEach((switchButton) => switchButton.classList.remove('is-selected'));
			button.classList.add('is-selected');
			selectedSwitch = button;
			moveActiveSwitch(button);
		};

		serviceSwitchButtons.forEach((button) => {
			button.addEventListener('click', () => switchServiceMode(button));
			button.addEventListener('keydown', (event) => {
				if (event.key === 'Enter' || event.key === ' ') {
					event.preventDefault();
					switchServiceMode(button);
				}
			});
		});
	}

	const portfolioCards = [...document.querySelectorAll('.portfolio_card')];

	portfolioCards.forEach((card) => {
		let slideTimer;
		let returnTimer;
		let expandFrame;
		const mobileQuery = window.matchMedia('(max-width: 768px)');

		const setBaseGeometry = () => {
			const wrapper = card.parentElement;
			const wrapperRect = wrapper.getBoundingClientRect();
			const cardRect = card.getBoundingClientRect();

			card.style.setProperty('--portfolio-base-left', `${cardRect.left - wrapperRect.left}px`);
			card.style.setProperty('--portfolio-base-top', `${cardRect.top - wrapperRect.top}px`);
			card.style.setProperty('--portfolio-base-width', `${cardRect.width}px`);
			card.style.setProperty('--portfolio-base-height', `${cardRect.height}px`);
			card.style.setProperty('--portfolio-expanded-top', '0px');
			card.style.setProperty('--portfolio-expanded-left', card.dataset.half === 'left' ? '0px' : `${wrapperRect.width / 2}px`);
			card.style.setProperty('--portfolio-expanded-width', `${wrapperRect.width / 2}px`);
			card.style.setProperty('--portfolio-expanded-height', `${wrapperRect.height}px`);
		};

		const setSlide = (slideIndex) => {
			const images = JSON.parse(card.dataset.images);
			card.querySelector('.portfolio_card_image').src = images[slideIndex % images.length];
		};

		card.addEventListener('mouseenter', () => {
			if (mobileQuery.matches) {
				return;
			}

			window.clearTimeout(returnTimer);
			card.classList.remove('is-returning');
			card.dataset.half = Number(card.style.getPropertyValue('--portfolio-column')) <= 2 ? 'left' : 'right';
			setBaseGeometry();
			card.classList.add('is-expanding');
			card.getBoundingClientRect();
			expandFrame = window.requestAnimationFrame(() => card.classList.add('is-expanded'));
			let slideIndex = 0;
			slideTimer = window.setInterval(() => {
				slideIndex += 1;
				setSlide(slideIndex);
			}, 2200);
		});

		card.addEventListener('mouseleave', () => {
			if (mobileQuery.matches) {
				return;
			}

			window.clearInterval(slideTimer);
			window.cancelAnimationFrame(expandFrame);
			card.classList.remove('is-expanded');
			card.classList.add('is-returning');
			window.clearTimeout(returnTimer);
			returnTimer = window.setTimeout(() => {
				card.classList.remove('is-expanding', 'is-returning');
				card.style.removeProperty('--portfolio-base-left');
				card.style.removeProperty('--portfolio-base-top');
				card.style.removeProperty('--portfolio-base-width');
				card.style.removeProperty('--portfolio-base-height');
			}, 420);
			window.setTimeout(() => setSlide(0), 420);
		});

		card.addEventListener('click', () => {
			if (!mobileQuery.matches) {
				return;
			}

			window.clearTimeout(returnTimer);
			window.clearInterval(slideTimer);
			window.cancelAnimationFrame(expandFrame);
			card.classList.remove('is-expanding', 'is-returning', 'is-expanded');
			card.classList.toggle('is-mobile-expanded');

			if (card.classList.contains('is-mobile-expanded')) {
				let slideIndex = 0;
				slideTimer = window.setInterval(() => {
					slideIndex += 1;
					setSlide(slideIndex);
				}, 2200);
				return;
			}

			window.setTimeout(() => setSlide(0), 420);
		});
	});
});
