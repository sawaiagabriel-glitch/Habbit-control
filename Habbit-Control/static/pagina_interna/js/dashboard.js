/**
 * Dashboard — atualiza progresso e gráfico ao trocar hábito/período.
 * Reutiliza api_dados_relatorio e criarGrafico/atualizarEstatisticas de relatorios.js.
 */

function atualizarBarraProgresso(progressoPercent, tipoHabito) {
    const fill = document.getElementById('progress_bar_fill');
    const label = document.getElementById('progress_bar_label');
    const valor = Math.round(progressoPercent || 0);

    if (fill) {
        fill.style.width = valor + '%';
        fill.setAttribute('data-tipo', tipoHabito || 'positivo');
    }
    if (label) {
        label.textContent = valor + '%';
    }
}

function carregarProgressoDashboard() {
    const habitoId = document.getElementById('habito_select')?.value;
    const periodo = document.getElementById('periodo_select')?.value || 'semana';

    if (!habitoId || !window.API_DADOS_RELATORIO_URL) {
        return;
    }

    let csrfToken = null;
    if (typeof getCookie === 'function') {
        csrfToken = getCookie('csrftoken');
    }

    fetch(`${window.API_DADOS_RELATORIO_URL}?habito_id=${habitoId}&periodo=${periodo}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Erro ao carregar progresso:', data.error);
            return;
        }

        if (typeof atualizarEstatisticas === 'function') {
            atualizarEstatisticas(data);
        }

        let progressoGeral = 0;
        if (data.habito.tipo === 'positivo') {
            if (data.total_esperado > 0) {
                progressoGeral = Math.min(100, (data.total_registrado / data.total_esperado) * 100);
            }
        } else {
            if (data.total_esperado > 0) {
                progressoGeral = Math.min(100, Math.max(0, (1 - (data.total_registrado / data.total_esperado)) * 100));
            } else {
                progressoGeral = data.total_registrado === 0 ? 100 : 0;
            }
        }

        atualizarBarraProgresso(progressoGeral, data.habito.tipo);

        if (typeof criarGrafico === 'function') {
            criarGrafico(data);
        }
    })
    .catch(error => {
        console.error('Erro ao carregar progresso da dashboard:', error);
    });
}

function initDashboard() {
    const habitoSelect = document.getElementById('habito_select');
    const periodoSelect = document.getElementById('periodo_select');

    if (!habitoSelect) {
        return;
    }

    habitoSelect.addEventListener('change', carregarProgressoDashboard);
    if (periodoSelect) {
        periodoSelect.addEventListener('change', carregarProgressoDashboard);
    }

    // Carrega gráfico com o hábito já selecionado no servidor
    carregarProgressoDashboard();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}
