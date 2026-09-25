/**
 * Estados e Cidades do Brasil
 * Dados para preenchimento de dropdowns dependentes
 */

// Dados de estados e cidades do Brasil
const estadosECidades = {
    'AC': ['Rio Branco', 'Cruzeiro do Sul', 'Sena Madureira', 'Tarauacá', 'Feijó', 'Brasiléia', 'Xapuri', 'Mâncio Lima', 'Plácido de Castro', 'Senador Guiomard'],
    'AL': ['Maceió', 'Arapiraca', 'Palmeira dos Índios', 'Rio Largo', 'Penedo', 'União dos Palmares', 'São Miguel dos Campos', 'Coruripe', 'Marechal Deodoro', 'Pilar'],
    'AP': ['Macapá', 'Santana', 'Laranjal do Jari', 'Oiapoque', 'Mazagão', 'Vitória do Jari', 'Porto Grande', 'Ferreira Gomes', 'Tartarugalzinho', 'Amapá'],
    'AM': ['Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Coari', 'Tefé', 'Maués', 'Tabatinga', 'Humaitá', 'São Gabriel da Cachoeira'],
    'BA': ['Salvador', 'Feira de Santana', 'Vitória da Conquista', 'Camaçari', 'Juazeiro', 'Ilhéus', 'Itabuna', 'Lauro de Freitas', 'Alagoinhas', 'Barreiras'],
    'CE': ['Fortaleza', 'Caucaia', 'Juazeiro do Norte', 'Maracanaú', 'Sobral', 'Crato', 'Itapipoca', 'Quixadá', 'Iguatu', 'Pacatuba'],
    'DF': ['Brasília', 'Ceilândia', 'Taguatinga', 'Sobradinho', 'Planaltina', 'Gama', 'Santa Maria', 'São Sebastião', 'Paranoá', 'Samambaia'],
    'ES': ['Vitória', 'Vila Velha', 'Cariacica', 'Serra', 'Cachoeiro de Itapemirim', 'Linhares', 'São Mateus', 'Colatina', 'Guarapari', 'Aracruz'],
    'GO': ['Goiânia', 'Aparecida de Goiânia', 'Anápolis', 'Rio Verde', 'Luziânia', 'Águas Lindas de Goiás', 'Valparaíso de Goiás', 'Trindade', 'Formosa', 'Novo Gama'],
    'MA': ['São Luís', 'Imperatriz', 'Caxias', 'Timon', 'Codó', 'Paço do Lumiar', 'Açailândia', 'Bacabal', 'Balsas', 'Santa Inês'],
    'MT': ['Cuiabá', 'Várzea Grande', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 'Cáceres', 'Sorriso', 'Lucas do Rio Verde', 'Barra do Garças', 'Primavera do Leste'],
    'MS': ['Campo Grande', 'Dourados', 'Três Lagoas', 'Corumbá', 'Ponta Porã', 'Naviraí', 'Nova Andradina', 'Paranaíba', 'Aquidauana', 'Sidrolândia'],
    'MG': ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 'Montes Claros', 'Ribeirão das Neves', 'Uberaba', 'Governador Valadares', 'Ipatinga'],
    'PA': ['Belém', 'Ananindeua', 'Marituba', 'Paragominas', 'Castanhal', 'Abaetetuba', 'Cametá', 'Bragança', 'Altamira', 'Santarém'],
    'PB': ['João Pessoa', 'Campina Grande', 'Santa Rita', 'Patos', 'Bayeux', 'Sousa', 'Cajazeiras', 'Guarabira', 'Mamanguape', 'Monteiro'],
    'PR': ['Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa', 'Cascavel', 'São José dos Pinhais', 'Foz do Iguaçu', 'Colombo', 'Guarapuava', 'Paranaguá'],
    'PE': ['Recife', 'Jaboatão dos Guararapes', 'Olinda', 'Caruaru', 'Petrolina', 'Paulista', 'Cabo de Santo Agostinho', 'Camaragibe', 'Garanhuns', 'Vitória de Santo Antão'],
    'PI': ['Teresina', 'Parnaíba', 'Picos', 'Piripiri', 'Floriano', 'Campo Maior', 'Barras', 'União', 'Pedro II', 'Oeiras'],
    'RJ': ['Rio de Janeiro', 'São Gonçalo', 'Duque de Caxias', 'Nova Iguaçu', 'Niterói', 'Campos dos Goytacazes', 'Belford Roxo', 'São João de Meriti', 'Petrópolis', 'Volta Redonda'],
    'RN': ['Natal', 'Mossoró', 'Parnamirim', 'São Gonçalo do Amarante', 'Macaíba', 'Ceará-Mirim', 'Açu', 'Currais Novos', 'Caicó', 'Nova Cruz'],
    'RS': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 'Gravataí', 'Viamão', 'Novo Hamburgo', 'São Leopoldo', 'Rio Grande'],
    'RO': ['Porto Velho', 'Ji-Paraná', 'Ariquemes', 'Vilhena', 'Cacoal', 'Rolim de Moura', 'Guajará-Mirim', 'Jaru', 'Buritis', 'Ouro Preto do Oeste'],
    'RR': ['Boa Vista', 'Rorainópolis', 'Caracaraí', 'Alto Alegre', 'Mucajaí', 'Bonfim', 'Cantá', 'Normandia', 'Pacaraima', 'Iracema'],
    'SC': ['Florianópolis', 'Joinville', 'Blumenau', 'São José', 'Criciúma', 'Chapecó', 'Itajaí', 'Lages', 'Jaraguá do Sul', 'Palhoça'],
    'SP': ['São Paulo', 'Guarulhos', 'Campinas', 'São Bernardo do Campo', 'Santo André', 'Osasco', 'São José dos Campos', 'Ribeirão Preto', 'Sorocaba', 'Santos'],
    'SE': ['Aracaju', 'Nossa Senhora do Socorro', 'Lagarto', 'Itabaiana', 'São Cristóvão', 'Propriá', 'Estância', 'Tobias Barreto', 'Simão Dias', 'Canindé de São Francisco'],
    'TO': ['Palmas', 'Araguaína', 'Gurupi', 'Porto Nacional', 'Paraíso do Tocantins', 'Colinas do Tocantins', 'Guaraí', 'Formoso do Araguaia', 'Dianópolis', 'Taguatinga']
};

// Mapeamento de siglas para nomes completos dos estados
const nomesEstados = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
};

/**
 * Inicializa os dropdowns de estado e cidade
 * @param {string} estadoId - ID do elemento select de estado
 * @param {string} cidadeId - ID do elemento select de cidade
 */
function inicializarEstadosCidades(estadoId = 'id_estado', cidadeId = 'id_cidade') {
    const estadoSelect = document.getElementById(estadoId);
    const cidadeSelect = document.getElementById(cidadeId);
    
    if (!estadoSelect || !cidadeSelect) {
        return;
    }
    
    // Ordenar estados alfabeticamente
    const estadosOrdenados = Object.keys(estadosECidades).sort(function(a, b) {
        return nomesEstados[a].localeCompare(nomesEstados[b]);
    });
    
    // Preencher dropdown de estados
    estadosOrdenados.forEach(function(sigla) {
        const option = document.createElement('option');
        option.value = sigla;
        option.textContent = nomesEstados[sigla];
        estadoSelect.appendChild(option);
    });
    
    // Event listener para mudança de estado
    estadoSelect.addEventListener('change', function() {
        const estadoSelecionado = this.value;
        
        // Limpar e desabilitar o select de cidades
        cidadeSelect.innerHTML = '<option value="" disabled selected>Selecione a cidade</option>';
        
        if (estadoSelecionado && estadosECidades[estadoSelecionado]) {
            // Habilitar o select de cidades
            cidadeSelect.disabled = false;
            
            // Ordenar e preencher cidades
            const cidades = estadosECidades[estadoSelecionado].sort();
            cidades.forEach(function(cidade) {
                const option = document.createElement('option');
                option.value = cidade;
                option.textContent = cidade;
                cidadeSelect.appendChild(option);
            });
        } else {
            cidadeSelect.disabled = true;
        }
    });
}

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        inicializarEstadosCidades();
    });
} else {
    inicializarEstadosCidades();
}

