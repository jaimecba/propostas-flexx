// 
// FORM.JS - CONTROLE DO FORMULÁRIO (COM VALIDAÇÃO DE CNPJ + PREÇOS API)
// 
// Integrado com a nova API de preços em tempo real
// Integrado com validação de CNPJ via Receita Federal
// 

document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ form.js carregado (Versão API Segura)');

    // 
    // ELEMENTOS DO DOM
    // 
    const $ = (id) => document.getElementById(id);
    
    const el = {
        // Dados do cliente
        cnpj: $('cnpj'),
        clienteNome: $('cliente_nome'),
        nomeFantasia: $('nome_fantasia'),
        email: $('email'),
        telefone: $('telefone'),
        whatsapp: $('whatsapp'),
        
        // Plano e usuários
        usuarios: $('usuarios'),
        plano: $('plano'),
        usuariosArredondados: $('usuariosArredondados'),
        
        // Valores
        valorMensal: $('valorMensal'),
        setup: $('setup'),
        treinamentoValor: $('treinamentoValor'),
        descontoValor: $('descontoValor'),
        descontoPercent: $('descontoPercent'),
        observacoes: $('observacoes'),
        charCount: $('charCount'),
        
        // Treinamento
        treinamentoOnline: $('treinamentoOnline'),
        treinamentoPresencial: $('treinamentoPresencial'),
        treinamentoHibrido: $('treinamentoHibrido'),
        
        // Serviços
        licencaFacial: $('licenca_facial'),
        qtdLicencaFacial: $('qtd_licenca_facial'),
        gestaoArquivos: $('gestao_arquivos'),
        controleFerias: $('controle_ferias'),
        requisCalcInt: $('requis_calc_int'),
        quantidadeLicenca: $('quantidade-licenca'),
        
        // Resumo
        resumoValorMensal: $('resumoValorMensal'),
        resumoSetup: $('resumoSetup'),
        resumoTreinamento: $('resumoTreinamento'),
        resumoServicosValor: $('resumo-servicos-valor'),
        resumoServicosItens: $('resumoServicosItens'),
        resumoSubtotal: $('resumoSubtotal'),
        resumoDesconto: $('resumoDesconto'),
        resumoTotal: $('resumoTotal'),
        
        // Botões
        btnGerar: $('btnGerar'),
        btnLimpar: $('btnLimpar'),
        btnValidarCNPJ: $('btnValidarCNPJ'),
        
        // Formulário
        form: $('formProposta')
    };

    // 
    // FUNÇÕES AUXILIARES
    // 
    
    function brl(valor) {
        /**Formata número para moeda BRL*/
        const num = Number(valor) || 0;
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(num);
    }

    function parseBRL(texto) {
        /**Parse de moeda BRL para número*/
        if (!texto) return 0;
        const limpo = String(texto)
            .replace(/[^\d,.-]/g, '')
            .replace(/\./g, '')
            .replace(',', '.');
        return parseFloat(limpo) || 0;
    }

    function roundUp10(num) {
        /**Arredonda para a próxima dezena*/
        const n = parseInt(num) || 0;
        if (n <= 0) return 10;
        if (n > 5000) return 'Consultar Comercial';
        return Math.ceil(n / 10) * 10;
    }

    // 
    // INTEGRAÇÃO COM A API DE PREÇOS (SUBSTITUI AS FUNÇÕES ANTIGAS DE CÁLCULO)
    // 

    let debounceTimer;

    function triggerRenderSummary() {
        clearTimeout(debounceTimer);
        // Feedback visual enquanto busca na API
        if (el.resumoValorMensal) el.resumoValorMensal.textContent = 'Calculando...';
        if (el.valorMensal) el.valorMensal.textContent = 'Calculando...';
        
        // Aguarda 400ms após o usuário parar de digitar para chamar a API
        debounceTimer = setTimeout(renderSummaryAsync, 400);
    }

    async function renderSummaryAsync() {
        console.log('🔄 renderSummaryAsync chamado (Buscando na API)');

        // ========================================
        // PASSO 1: OBTER TODOS OS VALORES BASE
        // ========================================
        const usuarios = parseInt(el.usuarios.value) || 0;
        const plano = el.plano ? el.plano.value : '';
        
        let setupValue = 0;
        if (el.setup && el.setup.value) {
            const setupParsed = parseBRL(el.setup.value);
            setupValue = !isNaN(setupParsed) ? setupParsed : 0;
        }
        
        const campoDesconto = document.getElementById('desconto');
        let descontoValue = 0;
        if (campoDesconto && campoDesconto.value) {
            const valorLimpo = campoDesconto.value.replace('R$', '').trim();
            const descParsed = parseBRL(valorLimpo);
            descontoValue = !isNaN(descParsed) ? descParsed : 0;
        }

        let faixaFlexx = roundUp10(usuarios);
        let isConsultarComercial = false;

        // REGRAS DE NEGÓCIO ORIGINAIS MANTIDAS
        if (faixaFlexx === 'Consultar Comercial') isConsultarComercial = true;
        if (plano.toLowerCase() === 'desktop' && usuarios > 1000) isConsultarComercial = true;

        let monthlyNumber = 0;
        let servicosTotal = 0;
        let servicosItems = [];
        let trainingValue = 0;
        let trainingLabel = 'Online';

        // ========================================
        // PASSO 2: BUSCAR PREÇOS NA API
        // ========================================
        
        // 2.1 Buscar Preço do Plano
        if (usuarios > 0 && plano && !isConsultarComercial) {
            try {
                const res = await fetch(`/api/precos/orcamento/calcular?plano=${plano}&usuarios=${usuarios}`, {
                    method: 'POST',
                    headers: { 'Accept': 'application/json' }
                });
                if (res.ok) {
                    const data = await res.json();
                    monthlyNumber = data.preco_final;
                    faixaFlexx = data.faixa_flexx;
                }
            } catch (error) {
                console.error('Erro ao buscar preço do plano:', error);
            }
        }

        // 2.2 Buscar Preços dos Serviços
        if (!isConsultarComercial && faixaFlexx > 0) {
            try {
                const res = await fetch(`/api/precos/servicos?faixa=${faixaFlexx}`);
                if (res.ok) {
                    const data = await res.json();
                    const servicosAPI = data.servicos;

                    if (el.licencaFacial && el.licencaFacial.checked) {
                        const srv = servicosAPI.find(s => s.nome === 'Licença Facial');
                        const qtd = parseInt(el.qtdLicencaFacial.value) || 0;
                        if (srv && qtd > 0) {
                            const val = srv.preco_unitario * qtd;
                            servicosItems.push({ nome: srv.nome, valor: val });
                            servicosTotal += val;
                        }
                    }
                    if (el.gestaoArquivos && el.gestaoArquivos.checked) {
                        const srv = servicosAPI.find(s => s.nome === 'Gestão de Arquivos');
                        if (srv) { servicosItems.push({ nome: srv.nome, valor: srv.preco_calculado }); servicosTotal += srv.preco_calculado; }
                    }
                    if (el.controleFerias && el.controleFerias.checked) {
                        const srv = servicosAPI.find(s => s.nome === 'Controle de Férias');
                        if (srv) { servicosItems.push({ nome: srv.nome, valor: srv.preco_calculado }); servicosTotal += srv.preco_calculado; }
                    }
                    if (el.requisCalcInt && el.requisCalcInt.checked) {
                        const srv = servicosAPI.find(s => s.nome === 'Mais Requis Cálc Int');
                        if (srv) { servicosItems.push({ nome: srv.nome, valor: srv.preco_calculado }); servicosTotal += srv.preco_calculado; }
                    }
                }
            } catch (error) {
                console.error('Erro ao buscar serviços:', error);
            }
        }

        // 2.3 Buscar Preço do Treinamento
        let tipoSelecionado = 'online';
        if (el.treinamentoPresencial && el.treinamentoPresencial.checked) tipoSelecionado = 'presencial';
        if (el.treinamentoHibrido && el.treinamentoHibrido.checked) tipoSelecionado = 'hibrido';

        try {
            const res = await fetch(`/api/precos/treinamento/${tipoSelecionado}`);
            if (res.ok) {
                const data = await res.json();
                trainingValue = data.preco;
                trainingLabel = data.tipo;
            }
        } catch (error) {
            console.error('Erro ao buscar treinamento:', error);
        }

        // ========================================
        // PASSO 3: ATUALIZAR A INTERFACE (DOM)
        // ========================================

        if (el.usuariosArredondados) {
            el.usuariosArredondados.textContent = isConsultarComercial ? 'Consultar Comercial' : `Faixa: ${faixaFlexx}`;
        }

        // Mensalidade
        let mensalidadeStr = brl(monthlyNumber);
        if (isConsultarComercial) mensalidadeStr = 'Consultar Comercial';
        else if (usuarios > 0 && plano && monthlyNumber === 0) mensalidadeStr = 'Não encontrado';
        
        if (el.resumoValorMensal) el.resumoValorMensal.textContent = mensalidadeStr;
        if (el.valorMensal) el.valorMensal.textContent = mensalidadeStr;

        // Serviços Adicionais
        if (el.resumoServicosItens) {
            if (servicosItems.length > 0 && !isConsultarComercial) {
                el.resumoServicosItens.innerHTML = servicosItems.map(item => 
                    `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>- ${item.nome}:</span><span>${brl(item.valor)}</span>
                    </div>`
                ).join('');
                el.resumoServicosItens.style.display = 'block';
            } else {
                el.resumoServicosItens.innerHTML = '';
                el.resumoServicosItens.style.display = 'none';
            }
        }

        const totalServicosElement = document.getElementById('resumoTotalServicos');
        if (totalServicosElement) totalServicosElement.textContent = isConsultarComercial ? brl(0) : brl(servicosTotal);

        // Também atualizar o elemento da seção de Serviços Adicionais
        const resumoServicosValor = document.getElementById('resumo-servicos-valor');
        if (resumoServicosValor) resumoServicosValor.textContent = isConsultarComercial ? brl(0) : brl(servicosTotal);

        // Total Contrato Mensal
        const totalContratoMensal = monthlyNumber + servicosTotal;
        const totalContratoElement = document.getElementById('resumoTotalContratoMensal');
        if (totalContratoElement) totalContratoElement.textContent = isConsultarComercial ? 'Consultar Comercial' : brl(totalContratoMensal);

        // Setup
        if (el.resumoSetup) el.resumoSetup.textContent = brl(setupValue);

        // Treinamento
        if (el.resumoTreinamento) {
            const labelTreinamento = document.getElementById('resumoTreinamentoLabel');
            if (labelTreinamento) labelTreinamento.textContent = `Treinamento (${trainingLabel}):`;
            el.resumoTreinamento.textContent = brl(trainingValue);
        }
        if (el.treinamentoValor) el.treinamentoValor.value = trainingValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        // Total Avulsos
        const totalAvulsos = setupValue + trainingValue;
        if (el.resumoSubtotal) el.resumoSubtotal.textContent = brl(totalAvulsos);

        // Desconto e Total Geral
        if (el.resumoDesconto) el.resumoDesconto.textContent = `- ${brl(descontoValue)}`;
        const totalGeral = Math.max(totalAvulsos - descontoValue, 0);
        if (el.resumoTotal) el.resumoTotal.textContent = brl(totalGeral);
    }

    // Função para carregar os preços dos treinamentos na UI ao abrir a página
    async function carregarPrecosTreinamentoUI() {
        try {
            const res = await fetch('/api/precos/treinamento');
            if (res.ok) {
                const data = await res.json();
                data.treinamentos.forEach(t => {
                    let radioId = '';
                    if (t.tipo.toLowerCase() === 'online') radioId = 'treinamentoOnline';
                    if (t.tipo.toLowerCase() === 'presencial') radioId = 'treinamentoPresencial';
                    if (t.tipo.toLowerCase() === 'híbrido') radioId = 'treinamentoHibrido';
                    
                    if (radioId) {
                        const radio = document.getElementById(radioId);
                        if (radio && radio.nextElementSibling) {
                            const precoSpan = radio.nextElementSibling.querySelector('.radio-preco');
                            if (precoSpan) precoSpan.textContent = `(${brl(t.preco)})`;
                        }
                    }
                });
            }
        } catch (e) { console.error('Erro ao carregar preços de treinamento na UI', e); }
    }

    // 
    // HANDLERS: CNPJ (VALIDAÇÃO COM RECEITA FEDERAL)
    // 

    function handleCNPJInput(e) {
        /**Formata CNPJ enquanto digita*/
        let valor = e.target.value.replace(/\D/g, '');
        if (valor.length <= 14) {
            if (valor.length > 0) {
                valor = valor.substring(0, 2) + '.' + 
                       valor.substring(2, 5) + '.' + 
                       valor.substring(5, 8) + '/' + 
                       valor.substring(8, 12) + '-' + 
                       valor.substring(12, 14);
            }
            e.target.value = valor;
        }
    }

    function handleCNPJChange(e) {
        const cnpj = e.target.value;
        const feedback = document.getElementById('cnpjFeedback');
        const cnpjError = document.getElementById('cnpjError');
        
        // CRÍTICO: NÃO validar se o campo estiver vazio
        if (!cnpj || cnpj.trim() === '') {
            // Limpar todos os feedbacks
            if (feedback) {
                feedback.className = 'feedback';
                feedback.textContent = '';
            }
            if (cnpjError) {
                cnpjError.style.display = 'none';
                cnpjError.textContent = '';
            }
            return;  // SAIR AQUI - não validar campo vazio
        }
        
        // Só validar se houver conteúdo
        const resultado = validarCNPJ(cnpj);
        if (resultado.valido) {
            if (feedback) {
                feedback.className = 'feedback success';
                feedback.textContent = 'CNPJ válido';
            }
            if (cnpjError) {
                cnpjError.style.display = 'none';
            }
        } else {
            if (feedback) {
                feedback.className = 'feedback error';
                feedback.textContent = resultado.mensagem;
            }
            if (cnpjError) {
                cnpjError.style.display = 'block';
                cnpjError.textContent = '❌ CNPJ inválido, verifique!';
            }
        }
    }

    function handleValidarCNPJ(e) {
        /**Busca dados do CNPJ na Receita Federal*/
        e.preventDefault();
        const cnpj = el.cnpj.value;
        const feedback = document.getElementById('cnpjFeedback');
        
        if (!cnpj) {
            if (feedback) {
                feedback.className = 'feedback error';
                feedback.textContent = 'Digite um CNPJ para validar.';
            }
            return;
        }

        // Validar formato
        const resultado = validarCNPJ(cnpj);
        if (!resultado.valido) {
            if (feedback) {
                feedback.className = 'feedback error';
                feedback.textContent = resultado.mensagem;
            }
            return;
        }

        // CNPJ válido - mostrar loading
        if (feedback) {
            feedback.className = 'feedback info';
            feedback.textContent = '⏳ Consultando Receita Federal...';
        }
        if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = true;

        // Chamar API para buscar dados do CNPJ
        buscarDadosCNPJ(cnpj);
    }

    function buscarDadosCNPJ(cnpj) {
        /**Busca os dados do CNPJ na sua própria API*/
        const cnpjLimpo = cnpj.replace(/\D/g, '');
        
        console.log(`🔍 Buscando CNPJ: ${cnpjLimpo}`);
        
        // Chamar SUA API (não a BrasilAPI diretamente)
        fetch(`/api/cnpj/${cnpjLimpo}`)
            .then(response => {
                console.log(`📡 Status da resposta: ${response.status}`);
                
                // Se não encontrou (404)
                if (response.status === 404) {
                    throw new Error('CNPJ não encontrado');
                }
                
                // Se houver outro erro
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                return response.json();
            })
            .then(data => {
                console.log('✅ Dados recebidos:', data);
                preencherDadosCNPJAlternativo(data);
            })
            .catch(error => {
                console.error('❌ Erro na busca:', error);
                const feedback = document.getElementById('cnpjFeedback');
                if (feedback) {
                    feedback.className = 'feedback warning';
                    feedback.textContent = '⚠️ CNPJ válido, mas não encontrado na Receita Federal. Preencha manualmente.';
                }
                if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = false;
            });
    }

    function preencherDadosCNPJ(data) {
        /**Preenche os campos com dados da API minha-api.com.br*/
        const feedback = document.getElementById('cnpjFeedback');
        try {
            // Preencher Razão Social
            if (data.razao_social && el.clienteNome) {
                el.clienteNome.value = data.razao_social;
                console.log('✅ Razão Social preenchida:', data.razao_social);
            }
            // Preencher Nome Fantasia
            if (data.nome_fantasia && el.nomeFantasia) {
                el.nomeFantasia.value = data.nome_fantasia;
                console.log('✅ Nome Fantasia preenchido:', data.nome_fantasia);
            }
            // Preencher Email
            if (data.email && el.email) {
                el.email.value = data.email;
                console.log('✅ Email preenchido:', data.email);
            }
            // Preencher Telefone
            if (data.telefone && el.telefone) {
                el.telefone.value = data.telefone;
                console.log('✅ Telefone preenchido:', data.telefone);
            }

            // Mostrar sucesso
            if (feedback) {
                feedback.className = 'feedback success';
                feedback.textContent = '✓ Dados carregados com sucesso!';
            }
            if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = false;
        } catch (error) {
            console.error('Erro ao preencher dados:', error);
            if (feedback) {
                feedback.className = 'feedback error';
                feedback.textContent = '❌ Erro ao processar dados do CNPJ.';
            }
            if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = false;
        }
    }

    function preencherDadosCNPJAlternativo(data) {
        /**Preenche os campos com dados da API brasilapi.com.br*/
        const feedback = document.getElementById('cnpjFeedback');
        try {
            // Preencher Razão Social
            if (data.nome_fantasia && el.clienteNome) {
                el.clienteNome.value = data.nome_fantasia;
                console.log('✅ Razão Social preenchida:', data.nome_fantasia);
            }
            // Preencher Nome Fantasia - CORRIGIDO: usar 'nome' ou 'descricao'
            if (data.nome && el.nomeFantasia) {
                el.nomeFantasia.value = data.nome;
                console.log('✅ Nome Fantasia preenchido:', data.nome);
            } else if (data.descricao && el.nomeFantasia) {
                el.nomeFantasia.value = data.descricao;
                console.log('✅ Nome Fantasia preenchido:', data.descricao);
            }

            // Mostrar sucesso
            if (feedback) {
                feedback.className = 'feedback success';
                feedback.textContent = '✓ Dados carregados com sucesso!';
            }
            if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = false;
        } catch (error) {
            console.error('Erro ao preencher dados:', error);
            if (feedback) {
                feedback.className = 'feedback error';
                feedback.textContent = '❌ Erro ao processar dados do CNPJ.';
            }
            if (el.btnValidarCNPJ) el.btnValidarCNPJ.disabled = false;
        }
    }

    // 
    // FUNÇÃO PARA FORMATAR CAMPOS DE MOEDA
    // 
    function formatarCampoMoeda(e) {
        /**Formata o campo como moeda ao sair dele (blur) ou apertar Enter*/
        if (e.type === 'keypress' && e.key !== 'Enter') {
            return;
        }
        if (e.type === 'keypress' && e.key === 'Enter') {
            e.preventDefault();
        }
        
        let valor = e.target.value;
        if (!valor || valor.trim() === '') {
            e.target.value = '0,00';
            triggerRenderSummary();
            return;
        }
        
        let limpo = valor.replace(/[^\d,.-]/g, '');
        limpo = limpo.replace(/\./g, '').replace(',', '.');
        let num = parseFloat(limpo) || 0;
        
        e.target.value = num.toLocaleString('pt-BR', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        });
        
        triggerRenderSummary();
    }

        // 
    // FUNÇÃO PARA INICIALIZAR CAMPOS DE MOEDA
    // 
    function inicializarCampoMoeda(campo) {
        /**Inicializa o campo com 0,00 e seleciona tudo ao clicar*/
        if (!campo) return;
        
        if (!campo.value || campo.value.trim() === '') {
            campo.value = '0,00';
        }
        
        campo.addEventListener('focus', function() {
            this.select();
        });
    }

        // 
    // EVENT LISTENERS
    // 

    // CNPJ
    if (el.cnpj) {
        el.cnpj.addEventListener('input', handleCNPJInput);
        el.cnpj.addEventListener('blur', handleCNPJChange);
    }
    if (el.btnValidarCNPJ) {
        el.btnValidarCNPJ.addEventListener('click', handleValidarCNPJ);
    }

    // Usuários
    if (el.usuarios) {
        el.usuarios.addEventListener('input', triggerRenderSummary);
        el.usuarios.addEventListener('change', triggerRenderSummary);
    }

    // Plano
    if (el.plano) {
        el.plano.addEventListener('change', triggerRenderSummary);
    }

    // Treinamento
    if (el.treinamentoOnline) el.treinamentoOnline.addEventListener('change', triggerRenderSummary);
    if (el.treinamentoPresencial) el.treinamentoPresencial.addEventListener('change', triggerRenderSummary);
    if (el.treinamentoHibrido) el.treinamentoHibrido.addEventListener('change', triggerRenderSummary);

    // Serviços
    if (el.licencaFacial) {
        el.licencaFacial.addEventListener('change', function() {
            if (el.quantidadeLicenca) {
                el.quantidadeLicenca.style.display = this.checked ? 'block' : 'none';
            }
            triggerRenderSummary();
        });
    }
    if (el.qtdLicencaFacial) el.qtdLicencaFacial.addEventListener('input', triggerRenderSummary);
    if (el.gestaoArquivos) el.gestaoArquivos.addEventListener('change', triggerRenderSummary);
    if (el.controleFerias) el.controleFerias.addEventListener('change', triggerRenderSummary);
    if (el.requisCalcInt) el.requisCalcInt.addEventListener('change', triggerRenderSummary);

    // Setup
    if (el.setup) {
        el.setup.addEventListener('input', triggerRenderSummary);
        el.setup.addEventListener('blur', formatarCampoMoeda);
        el.setup.addEventListener('keypress', formatarCampoMoeda);
    }

    // Desconto
    const inputDesconto = document.getElementById('desconto');
    if (inputDesconto) {
        inputDesconto.addEventListener('input', triggerRenderSummary);
        inputDesconto.addEventListener('change', triggerRenderSummary);
        inputDesconto.addEventListener('blur', formatarCampoMoeda);
        inputDesconto.addEventListener('keypress', formatarCampoMoeda);
    }
    
    if (el.descontoValor) el.descontoValor.addEventListener('input', triggerRenderSummary);
    if (el.descontoPercent) el.descontoPercent.addEventListener('input', triggerRenderSummary);

    // Botão Limpar
    if (el.btnLimpar) {
        el.btnLimpar.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Tem certeza que deseja limpar o formulário?')) {
                if (el.form) el.form.reset();
                // Limpar feedbacks
                const feedbacks = document.querySelectorAll('.feedback');
                feedbacks.forEach(fb => {
                    fb.className = 'feedback';
                    fb.textContent = '';
                });
                triggerRenderSummary();
            }
        });
    }

    // 
    // INICIALIZAÇÃO
    // 

        // Inicializar campos de moeda com 0,00 e comportamento de seleção
    inicializarCampoMoeda(el.setup);
    inicializarCampoMoeda(inputDesconto);
    
    // Esconder campo de quantidade de licença inicialmente
    if (el.quantidadeLicenca) {
        el.quantidadeLicenca.style.display = 'none';
    }

    // Carrega os preços dos treinamentos na tela e depois calcula o resumo inicial
    carregarPrecosTreinamentoUI().then(() => {
        triggerRenderSummary();
    });

    console.log('✅ form.js inicializado com sucesso');
});