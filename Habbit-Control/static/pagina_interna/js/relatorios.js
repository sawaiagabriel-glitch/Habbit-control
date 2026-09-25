/**
 * Relatórios - JavaScript
 * Gerencia a geração de relatórios e gráficos
 */

let chartInstance = null;

/**
 * Obtém o valor de um cookie
 * @param {string} name - Nome do cookie
 * @returns {string|null} - Valor do cookie ou null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Gera o relatório baseado nos filtros selecionados
 */
function gerarRelatorio() {
    const habitoId = document.getElementById('habito_select')?.value;
    const periodo = document.getElementById('periodo_select')?.value;
    
    if (!habitoId) {
        alert('Por favor, selecione um hábito.');
        return;
    }
    
    // Mostra loading
    document.getElementById('relatorio_stats').style.display = 'none';
    document.getElementById('relatorio_chart_container').style.display = 'none';
    document.getElementById('relatorio_empty').style.display = 'none';
    
    let csrfToken = getCookie('csrftoken');
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) csrfToken = csrfInput.value;
    
    // URL da API - configurada pelo Django template
    const apiUrl = window.API_DADOS_RELATORIO_URL;
    if (!apiUrl) {
        alert('URL da API não configurada');
        return;
    }
    
    fetch(`${apiUrl}?habito_id=${habitoId}&periodo=${periodo}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            atualizarEstatisticas(data);
            criarGrafico(data)
            mostrarElementos();
        } else {
            alert('Erro ao gerar relatório: ' + (data.error || 'Erro desconhecido'));
            document.getElementById('relatorio_empty').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao gerar relatório. Tente novamente.');
        document.getElementById('relatorio_empty').style.display = 'block';
    });
}

/**
 * Atualiza as estatísticas do relatório
 * @param {Object} data - Dados do relatório
 */
function atualizarEstatisticas(data) {
    document.getElementById('stat_registrado').textContent = data.total_registrado;
    document.getElementById('stat_esperado').textContent = data.total_esperado;
    
    // Calcula progresso geral
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
    document.getElementById('stat_progresso').textContent = Math.round(progressoGeral) + '%';
    
    // Atualiza título do gráfico
    document.getElementById('chart_title').textContent = data.habito.nome;
    document.getElementById('chart_subtitle').textContent = `Frequência desejada: ${data.habito.frequencia_desejada_valor} ${data.habito.frequencia_desejada_periodo}`;
}

/**
 * Mostra os elementos do relatório
 */
function mostrarElementos() {
    document.getElementById('relatorio_stats').style.display = 'grid';
    document.getElementById('relatorio_chart_container').style.display = 'block';
    document.getElementById('relatorio_empty').style.display = 'none';
}

/**
 * Cria ou atualiza o gráfico do relatório
 * @param {Object} data - Dados do relatório
 */
function criarGrafico(data) {
    const ctx = document.getElementById('relatorioChart');
    if (!ctx) return;
    
    // Destroi gráfico anterior se existir
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const corLinha = data.habito.tipo === 'positivo' ? '#10B981' : '#EF4444';
    const corFundo = data.habito.tipo === 'positivo' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Registrado (Acumulado)',
                    data: data.dados_registrados,
                    borderColor: corLinha,
                    backgroundColor: corFundo,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: corLinha,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Esperado (Acumulado)',
                    data: data.dados_esperados,
                    borderColor: '#004B5E',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#004B5E',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Progresso (%)',
                    data: data.progresso_percent,
                    borderColor: '#FF8C42',
                    backgroundColor: 'rgba(255, 140, 66, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 2) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Quantidade (Acumulada)',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Progresso (%)',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Alias para compatibilidade
window.criarGrafico = criarGrafico;

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Funções já estão disponíveis globalmente
    });
} else {
    // DOM já está pronto
}

