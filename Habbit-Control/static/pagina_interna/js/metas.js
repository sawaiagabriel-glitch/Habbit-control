function getMetasConfig() {
    const el = document.getElementById('metas-page-config');
    return {
        sugerirUrl: el ? el.dataset.assistenteSugerirUrl : '',
        criarUrl: el ? el.dataset.assistenteCriarUrl : ''
    };
}

let sugestaoMetaAtual = null;
let historicoAssistente = [];

function abrirAssistenteMetas() {
    const modal = document.getElementById('assistente-modal');
    if (!modal) return;
    limparAlertaAssistente();
    resetarChatAssistente(false);
    modal.style.display = 'flex';

    const selectHabitoForm = document.getElementById('id_habito');
    const selectHabitoAssistente = document.getElementById('assistant-habito');
    if (selectHabitoForm && selectHabitoForm.value && selectHabitoAssistente) {
        selectHabitoAssistente.value = selectHabitoForm.value;
        aoSelecionarHabitoAssistente();
    } else if (selectHabitoAssistente && selectHabitoAssistente.options.length > 1) {
        if (!selectHabitoAssistente.value) {
            selectHabitoAssistente.selectedIndex = 1;
            aoSelecionarHabitoAssistente();
        }
    }

    const input = document.getElementById('assistant-chat-input');
    if (input) input.focus();
}

function fecharAssistenteMetas() {
    const modal = document.getElementById('assistente-modal');
    if (modal) modal.style.display = 'none';
}

function aoSelecionarHabitoAssistente() {
    limparAlertaAssistente();
}

function limparAlertaAssistente() {
    const alerta = document.getElementById('assistant-alert');
    if (alerta) {
        alerta.style.display = 'none';
        alerta.innerText = '';
    }
}

function mostrarAlertaAssistente(msg) {
    const alerta = document.getElementById('assistant-alert');
    if (alerta) {
        alerta.innerText = msg;
        alerta.style.display = 'block';
    }
}

function resetarChatAssistente(manterHabito) {
    historicoAssistente = [];
    sugestaoMetaAtual = null;
    const log = document.getElementById('assistant-chat-log');
    if (log) {
        log.innerHTML = '';
        appendBolhaAssistente('O que você quer alcançar com esse hábito?', false);
    }
    const input = document.getElementById('assistant-chat-input');
    if (input) input.value = '';
    const chatStep = document.getElementById('assistant-step-chat');
    const resultStep = document.getElementById('assistant-step-result');
    if (chatStep) chatStep.style.display = 'block';
    if (resultStep) resultStep.style.display = 'none';
    ocultarPlanoSugerido();
    limparAlertaAssistente();
    if (!manterHabito) {
        // mantém hábito selecionado por padrão
    }
}

function comecarNovamenteAssistente() {
    resetarChatAssistente(true);
    const input = document.getElementById('assistant-chat-input');
    if (input) input.focus();
}

function appendBolhaAssistente(texto, registrarHistorico) {
    const log = document.getElementById('assistant-chat-log');
    if (!log) return;
    const bubble = document.createElement('div');
    bubble.className = 'assistant-chat-bubble assistant-chat-bubble-bot';
    const role = document.createElement('span');
    role.className = 'assistant-chat-role';
    role.setAttribute('aria-hidden', 'true');
    role.textContent = '🤖';
    const p = document.createElement('p');
    p.className = 'assistant-chat-text';
    p.textContent = texto || '';
    bubble.appendChild(role);
    bubble.appendChild(p);
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    if (registrarHistorico) {
        historicoAssistente.push({ role: 'assistant', content: String(texto || '').slice(0, 500) });
    }
}

function appendBolhaUsuario(texto) {
    const log = document.getElementById('assistant-chat-log');
    if (!log) return;
    const bubble = document.createElement('div');
    bubble.className = 'assistant-chat-bubble assistant-chat-bubble-user';
    const p = document.createElement('p');
    p.className = 'assistant-chat-text';
    p.textContent = texto || '';
    bubble.appendChild(p);
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
}

function enviarMensagemAssistente() {
    limparAlertaAssistente();
    const habitoId = document.getElementById('assistant-habito').value;
    const input = document.getElementById('assistant-chat-input');
    const mensagem = input ? String(input.value || '').trim().slice(0, 500) : '';

    if (!habitoId) {
        mostrarAlertaAssistente('Selecione um hábito para continuar a conversa.');
        return;
    }
    if (!mensagem) {
        mostrarAlertaAssistente('Escreva o que você quer alcançar.');
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const btnEnviar = document.getElementById('btn-enviar-chat');
    const originalText = btnEnviar ? btnEnviar.innerHTML : '';
    if (btnEnviar) {
        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<span>Pensando...</span>';
    }

    appendBolhaUsuario(mensagem);
    if (input) input.value = '';

    const historicoParaEnvio = historicoAssistente.slice(-10).map(function (m) {
        return { role: m.role, content: String(m.content || '').slice(0, 500) };
    });

    fetch(getMetasConfig().sugerirUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            habito_id: habitoId,
            mensagem: mensagem,
            historico: historicoParaEnvio
        })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
        if (btnEnviar) {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = originalText;
        }

        if (status !== 200 || !body.sucesso) {
            mostrarAlertaAssistente(body.erro || 'Não foi possível continuar a conversa no momento.');
            return;
        }

        historicoAssistente.push({ role: 'user', content: mensagem });

        if (body.estado === 'coletando_contexto') {
            appendBolhaAssistente(body.mensagem || 'Pode me contar um pouco mais?', true);
            return;
        }

        // meta_pronta (IA ou fallback determinístico)
        if (body.mensagem) {
            appendBolhaAssistente(body.mensagem, true);
        }

        const meta = body.meta || body;
        sugestaoMetaAtual = Object.assign({}, body, meta, {
            habito_id: body.habito_id,
            quantidade_sugerida: meta.quantidade_sugerida || body.quantidade_sugerida,
            periodo: meta.periodo || body.periodo
        });

        mostrarResultadoMetaPronta(sugestaoMetaAtual);
    })
    .catch(function () {
        if (btnEnviar) {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = originalText;
        }
        mostrarAlertaAssistente('Erro de conexão ao consultar o assistente.');
    });
}

function mostrarResultadoMetaPronta(body) {
    const meta = body.meta || body;
    const tituloExibicao = meta.titulo_meta || body.titulo_meta || body.nome_habito || 'Meta sugerida';
    document.getElementById('suggestion-title').innerText = tituloExibicao;
    document.getElementById('suggestion-highlight').innerText =
        (meta.quantidade_sugerida || body.quantidade_sugerida || '') +
        ' vezes por ' +
        (meta.periodo || body.periodo || '');
    document.getElementById('suggestion-text').innerText =
        meta.mensagem || body.mensagem || '';

    const badge = document.getElementById('suggestion-origem-badge');
    if (badge) {
        badge.style.display = (body.origem === 'ia') ? 'inline-block' : 'none';
    }

    const planoFonte = Object.assign({}, meta, {
        justificativa: meta.justificativa || body.justificativa,
        nome_habito: body.nome_habito
    });
    renderizarPlanoSugerido(planoFonte);

    document.getElementById('assistant-step-chat').style.display = 'none';
    document.getElementById('assistant-step-result').style.display = 'block';
}

function ocultarPlanoSugerido() {
    const bloco = document.getElementById('assistant-plan');
    if (bloco) bloco.style.display = 'none';
    const lista = document.getElementById('plan-etapas');
    if (lista) lista.innerHTML = '';
}

function renderizarPlanoSugerido(body) {
    const bloco = document.getElementById('assistant-plan');
    if (!bloco) return;

    const temMetaPrincipal = !!(body && (body.titulo_meta || body.objetivo_principal));
    const etapas = body && Array.isArray(body.etapas) ? body.etapas : null;
    const temEtapas = !!(etapas && etapas.length >= 1 && etapas.length <= 4);
    const temPrazo = !!(body && body.duracao_semanas);
    const temPlanoRico = temMetaPrincipal || temEtapas || temPrazo ||
        !!(body && (body.criterio_sucesso || body.plano_recuperacao || body.justificativa));

    if (!temPlanoRico) {
        ocultarPlanoSugerido();
        return;
    }

    const metaPrincipal = body.titulo_meta || body.objetivo_principal || body.nome_habito || 'Meta sugerida';
    const objetivoLinha = body.objetivo_principal && body.titulo_meta &&
        body.objetivo_principal !== body.titulo_meta
        ? body.titulo_meta + ' — ' + body.objetivo_principal
        : metaPrincipal;
    document.getElementById('plan-meta-principal').innerText = objetivoLinha;

    const prazoEl = document.getElementById('plan-duracao');
    if (body.duracao_semanas) {
        prazoEl.innerText = body.duracao_semanas + ' semanas';
        prazoEl.parentElement.style.display = '';
    } else {
        prazoEl.innerText = '';
        prazoEl.parentElement.style.display = 'none';
    }

    document.getElementById('plan-frequencia').innerText =
        (body.quantidade_sugerida || '') + ' vezes por ' + (body.periodo || '');

    const lista = document.getElementById('plan-etapas');
    lista.innerHTML = '';
    if (temEtapas) {
        etapas.forEach((etapa, index) => {
            const li = document.createElement('li');
            li.className = 'assistant-plan-etapa';

            const tituloEl = document.createElement('p');
            tituloEl.className = 'assistant-plan-etapa-titulo';
            tituloEl.textContent = 'Etapa ' + (index + 1) + ' — ' + (etapa.titulo || '');

            const semanasEl = document.createElement('p');
            semanasEl.className = 'assistant-plan-etapa-semanas';
            const inicio = parseInt(etapa.inicio_semana, 10);
            const fim = parseInt(etapa.fim_semana, 10);
            if (!isNaN(inicio) && !isNaN(fim)) {
                semanasEl.textContent = 'Semanas ' + inicio + '–' + fim;
            } else {
                semanasEl.textContent = '';
            }

            const descEl = document.createElement('p');
            descEl.className = 'assistant-plan-etapa-desc';
            descEl.textContent = etapa.descricao || '';

            li.appendChild(tituloEl);
            if (semanasEl.textContent) li.appendChild(semanasEl);
            li.appendChild(descEl);
            lista.appendChild(li);
        });
        lista.parentElement.style.display = '';
    } else {
        lista.parentElement.style.display = 'none';
    }

    const criterioEl = document.getElementById('plan-criterio');
    if (body.criterio_sucesso) {
        criterioEl.innerText = body.criterio_sucesso;
        criterioEl.parentElement.style.display = '';
    } else {
        criterioEl.innerText = '';
        criterioEl.parentElement.style.display = 'none';
    }

    const recuperacaoEl = document.getElementById('plan-recuperacao');
    if (body.plano_recuperacao) {
        recuperacaoEl.innerText = body.plano_recuperacao;
        recuperacaoEl.parentElement.style.display = '';
    } else {
        recuperacaoEl.innerText = '';
        recuperacaoEl.parentElement.style.display = 'none';
    }

    const justificativaEl = document.getElementById('plan-justificativa');
    if (body.justificativa) {
        justificativaEl.innerText = body.justificativa;
        justificativaEl.parentElement.style.display = '';
    } else {
        justificativaEl.innerText = '';
        justificativaEl.parentElement.style.display = 'none';
    }

    bloco.style.display = 'block';
}

function usarECriarMetaAssistente() {
    if (!sugestaoMetaAtual) return;

    const meta = sugestaoMetaAtual.meta || sugestaoMetaAtual;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const btn = document.getElementById('btn-usar-criar-meta');
    const originalHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>Criando...</span>';
    }

    const payload = {
        habito_id: sugestaoMetaAtual.habito_id,
        quantidade_minima: meta.quantidade_sugerida || sugestaoMetaAtual.quantidade_sugerida,
        periodo: meta.periodo || sugestaoMetaAtual.periodo,
        titulo_meta: meta.titulo_meta || sugestaoMetaAtual.titulo_meta,
        objetivo_principal: meta.objetivo_principal || sugestaoMetaAtual.objetivo_principal,
        nivel: meta.nivel || sugestaoMetaAtual.nivel,
        mensagem: meta.mensagem || sugestaoMetaAtual.mensagem,
        justificativa: meta.justificativa || sugestaoMetaAtual.justificativa,
        duracao_semanas: meta.duracao_semanas || sugestaoMetaAtual.duracao_semanas,
        criterio_sucesso: meta.criterio_sucesso || sugestaoMetaAtual.criterio_sucesso,
        plano_recuperacao: meta.plano_recuperacao || sugestaoMetaAtual.plano_recuperacao,
        etapas: meta.etapas || sugestaoMetaAtual.etapas,
        plano: {
            titulo_meta: meta.titulo_meta || sugestaoMetaAtual.titulo_meta,
            objetivo_principal: meta.objetivo_principal || sugestaoMetaAtual.objetivo_principal,
            nivel: meta.nivel || sugestaoMetaAtual.nivel,
            mensagem: meta.mensagem || sugestaoMetaAtual.mensagem,
            justificativa: meta.justificativa || sugestaoMetaAtual.justificativa,
            duracao_semanas: meta.duracao_semanas || sugestaoMetaAtual.duracao_semanas,
            criterio_sucesso: meta.criterio_sucesso || sugestaoMetaAtual.criterio_sucesso,
            plano_recuperacao: meta.plano_recuperacao || sugestaoMetaAtual.plano_recuperacao,
            etapas: meta.etapas || sugestaoMetaAtual.etapas
        }
    };

    fetch(getMetasConfig().criarUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
        if (status !== 200 || !body.sucesso) {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
            mostrarAlertaAssistente(body.erro || 'Não foi possível criar a meta.');
            return;
        }
        window.location.href = body.redirect_url || ('/metas/#meta-' + body.meta_id);
    })
    .catch(function () {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
        mostrarAlertaAssistente('Erro de conexão ao criar a meta.');
    });
}

function destacarMetaPorHash() {
    const hash = window.location.hash || '';
    const match = hash.match(/^#meta-(\d+)$/);
    if (!match) return;
    const card = document.getElementById('meta-' + match[1]);
    if (!card) return;
    card.classList.add('goal-card-highlight');
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(function () { card.classList.remove('goal-card-highlight'); }, 2600);
}

document.addEventListener('DOMContentLoaded', destacarMetaPorHash);
window.addEventListener('hashchange', destacarMetaPorHash);

function copiarLinkPublico(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.select();
    input.setSelectionRange(0, 99999);
    const span = btn.querySelector('span');
    const originalText = span ? span.innerText : 'Copiar link';
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(input.value).then(() => {
            if (span) span.innerText = 'Copiado!';
            setTimeout(() => { if (span) span.innerText = originalText; }, 2000);
        }).catch(() => {
            document.execCommand('copy');
            if (span) span.innerText = 'Copiado!';
            setTimeout(() => { if (span) span.innerText = originalText; }, 2000);
        });
    } else {
        document.execCommand('copy');
        if (span) span.innerText = 'Copiado!';
        setTimeout(() => { if (span) span.innerText = originalText; }, 2000);
    }
}

function compartilharNativo(titulo, url) {
    if (navigator.share) {
        navigator.share({
            title: 'Meta: ' + titulo,
            text: 'Acompanhe a minha meta no Habbit-Control!',
            url: url
        }).catch(() => {});
    } else {
        navigator.clipboard.writeText(url).then(() => {
            alert('Link copiado para a área de transferência!');
        }).catch(() => {});
    }
}
