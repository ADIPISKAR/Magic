document.addEventListener('DOMContentLoaded', () => {
	const calculator = document.querySelector('[data-repair-calculator]');
	if (!calculator) return;

	let settings;
	try {
		settings = JSON.parse(calculator.dataset.calculator);
	} catch {
		return;
	}

	const propertyButtons = [...calculator.querySelectorAll('[data-property]')];
	const planContainer = calculator.querySelector('[data-calculator-plans]');
	const areaInput = calculator.querySelector('[data-calculator-area]');
	const areaOutput = calculator.querySelector('[data-calculator-area-output]');
	const totalOutput = calculator.querySelector('[data-calculator-total]');
	const rateOutput = calculator.querySelector('[data-calculator-rate]');
	const leadButton = calculator.querySelector('[data-calculator-lead]');
	const formatter = new Intl.NumberFormat('ru-RU');
	const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	let property = settings.default_property;
	let planIndex = Number(settings.default_plan);
	let displayedTotal = 0;
	let animationFrame;

	const activePlan = () => settings.properties[property].plans[planIndex];
	const formatTotal = (value) => `от ${formatter.format(Math.round(value))} ₽`;

	const animateTotal = (nextTotal) => {
		window.cancelAnimationFrame(animationFrame);
		if (reducedMotion || displayedTotal === 0) {
			displayedTotal = nextTotal;
			totalOutput.textContent = formatTotal(nextTotal);
			return;
		}

		const previousTotal = displayedTotal;
		const startedAt = performance.now();
		const tick = (now) => {
			const progress = Math.min((now - startedAt) / 380, 1);
			const eased = 1 - ((1 - progress) ** 3);
			displayedTotal = previousTotal + ((nextTotal - previousTotal) * eased);
			totalOutput.textContent = formatTotal(displayedTotal);
			if (progress < 1) animationFrame = window.requestAnimationFrame(tick);
		};
		animationFrame = window.requestAnimationFrame(tick);
	};

	const renderPlans = () => {
		planContainer.innerHTML = settings.properties[property].plans.map((plan, index) => `
			<option value="${index}"${index === planIndex ? ' selected' : ''}>${plan.name}</option>
		`).join('');
	};

	const updateResult = () => {
		const area = Number(areaInput.value);
		const plan = activePlan();
		areaOutput.textContent = `${area} м²`;
		rateOutput.textContent = `${formatter.format(plan.rate)} ₽/м²`;
		areaInput.style.setProperty('--range-progress', `${((area - settings.minimum_area) / (settings.maximum_area - settings.minimum_area)) * 100}%`);
		animateTotal(area * plan.rate);
		calculator.classList.remove('is-updating');
		window.requestAnimationFrame(() => calculator.classList.add('is-updating'));
	};

	propertyButtons.forEach((button) => {
		button.addEventListener('click', () => {
			property = button.dataset.property;
			planIndex = Number(settings.default_plan);
			propertyButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
			renderPlans();
			updateResult();
		});
	});

	areaInput.addEventListener('input', updateResult);
	planContainer.addEventListener('change', () => {
		planIndex = Number(planContainer.value);
		updateResult();
	});
	leadButton.addEventListener('click', () => {
		const modalText = document.querySelector('[data-lead-context]');
		const message = document.querySelector('[data-lead-message]');
		const source = document.querySelector('[data-lead-source]');
		const summary = `${settings.properties[property].label}, ${areaInput.value} м², ${activePlan().name.toLowerCase()}, ориентир ${formatTotal(Number(areaInput.value) * activePlan().rate)}`;
		if (modalText) {
			modalText.textContent = `${settings.properties[property].label}, ${areaInput.value} м², ${activePlan().name.toLowerCase()}. Оставьте номер — уточним детали и подготовим точную смету.`;
		}
		if (message) message.value = summary;
		if (source) source.value = 'Калькулятор стоимости';
	});

	renderPlans();
	updateResult();
});
