document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-service-plan]').forEach((plan) => {
        let config;
        try {
            config = JSON.parse(plan.dataset.planConfig);
        } catch {
            return;
        }

        const serviceName = plan.dataset.serviceName;
        const planner = plan.closest('[data-service-planner]');
        const scenarioOutput = plan.querySelector('[data-plan-scenario]');
        const totalOutput = plan.querySelector('[data-plan-total]');
        const formatter = new Intl.NumberFormat('ru-RU');
        let currentTotal = 0;
        let parameterLine = '';

        const activeScenario = () => {
            const tab = planner?.querySelector('[data-service-scenario][aria-selected="true"]');
            const panel = planner?.querySelector('[data-service-scenario-panel]:not([hidden])');
            return {
                label: tab?.textContent.replace(/^\s*\d+\s*/, '').trim() || 'Выбранный сценарий',
                title: panel?.querySelector('h3')?.textContent.trim() || '',
                points: [...(panel?.querySelectorAll('.service_scenario_points li') || [])].map((item) => item.textContent.trim()),
            };
        };

        const setRangeProgress = (input) => {
            const min = Number(input.min);
            const max = Number(input.max);
            input.style.setProperty('--range-progress', `${((Number(input.value) - min) / (max - min)) * 100}%`);
        };

        const render = () => {
            const scenario = activeScenario();
            scenarioOutput.textContent = scenario.label;

            if (config.mode === 'area') {
                const area = plan.querySelector('[data-plan-area]');
                const option = plan.querySelector('[data-plan-option]');
                const selected = config.options[Number(option.value)];
                plan.querySelector('[data-plan-area-output]').textContent = area.value;
                setRangeProgress(area);
                currentTotal = Number(area.value) * selected.rate;
                parameterLine = `${area.value} м² · ${selected.label} · ${formatter.format(selected.rate)} ₽/м²`;
            } else {
                const tileArea = plan.querySelector('[data-plan-tile-area]');
                const outputs = plan.querySelector('[data-plan-outputs]');
                const demolition = plan.querySelector('[data-plan-demolition]');
                plan.querySelector('[data-plan-tile-output]').textContent = tileArea.value;
                plan.querySelector('[data-plan-outputs-output]').textContent = outputs.value;
                setRangeProgress(tileArea);
                setRangeProgress(outputs);
                currentTotal = Number(tileArea.value) * config.tile_area.rate
                    + Number(outputs.value) * config.outputs.rate
                    + (demolition.checked ? Number(tileArea.value) * config.demolition_rate : 0);
                parameterLine = `${tileArea.value} м² облицовки · ${outputs.value} выводов${demolition.checked ? ' · с демонтажем плитки' : ''}`;
            }

            totalOutput.textContent = `от ${formatter.format(currentTotal)} ₽`;
        };

        const summary = () => {
            const scenario = activeScenario();
            const checked = [...document.querySelectorAll('[data-service-check-item]:checked')]
                .map((item) => item.closest('label')?.querySelector('em')?.textContent.trim())
                .filter(Boolean);
            const lines = [
                serviceName,
                `Сценарий: ${scenario.label}`,
                scenario.title ? `Маршрут: ${scenario.title}` : '',
                `Параметры: ${parameterLine}`,
                `Предварительный ориентир: от ${formatter.format(currentTotal)} ₽`,
                '',
                'На замере проверить:',
                ...scenario.points.map((point) => `— ${point}`),
            ];
            if (checked.length) lines.push('', 'Уже подготовлено:', ...checked.map((item) => `— ${item}`));
            lines.push('', `Примечание: ${config.note}`);
            return lines.filter((line, index) => line !== '' || lines[index - 1] !== '').join('\n');
        };

        plan.querySelectorAll('input, select').forEach((field) => field.addEventListener('input', render));
        planner?.querySelectorAll('[data-service-scenario]').forEach((tab) => tab.addEventListener('click', () => window.setTimeout(render)));

        plan.querySelector('[data-plan-download]')?.addEventListener('click', () => {
            const blob = new Blob([summary()], { type: 'text/plain;charset=utf-8' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `plan-remonta-${window.location.pathname.split('/').filter(Boolean).pop()}.txt`;
            link.click();
            URL.revokeObjectURL(link.href);
        });

        const attach = plan.querySelector('[data-plan-attach]');
        attach?.addEventListener('click', () => {
            attach.dataset.leadMessage = summary();
        });

        render();
    });
});
