// ============================================================================
// PRECOS.JS - INTEGRAÇÃO COM API DE PRECIFICAÇÃO (VERSÃO CORRIGIDA v2)
// ============================================================================
// Este arquivo busca os preços do banco de dados via API
// Funciona com form.js e index.html sem necessidade de alterações
// ============================================================================

// ============================================================================
// CONFIGURAÇÕES GLOBAIS
// ============================================================================
const API_BASE_URL = 'http://localhost:8000'; // Ajuste se necessário

// Cache para armazenar preços (evita chamadas repetidas)
let cachePrecos = {};
let cacheServicos = {};

// Flag para evitar múltiplas chamadas simultâneas
let requisicoesPendentes = {};

// ============================================================================
// FUNÇÃO: ARREDONDAR PESSOAS (MESMO PADRÃO DO BACKEND)
// ============================================================================
function arredondarPessoas(usuarios) {
    /**
     * Arredonda a quantidade de usuários para a faixa de 10 em 10
     * Ex: 15 → 20, 1 → 10, 55 → 60
     */
    const num = parseInt(usuarios) || 0;
    if (num <= 0) return 10;
    if (num > 5000) return 'Consultar Comercial';
    return Math.ceil(num / 10) * 10;
}

// ============================================================================
// FUNÇÃO: OBTER PREÇO DO PLANO (SÍNCRONO COM CACHE)
// ============================================================================
function obterPrecoPlano(plano, usuarios) {
    /**
     * Busca o preço de um plano para uma quantidade de usuários
     * VERSÃO SÍNCRONA: Retorna valor do cache ou 0 se não encontrado
     * A atualização do cache acontece em background
     * 
     * Parâmetros:
     *   plano (string): 'Basic', 'PRO', 'Ultimate', 'Desktop'
     *   usuarios (number): Quantidade de usuários
     * 
     * Retorna:
     *   number: Valor do preço mensal (do cache)
     *   string: 'Consultar Comercial' se acima do limite
     */
    
    // Validar entrada
    if (!plano || usuarios <= 0) {
        console.warn('⚠️ Parâmetros inválidos para obterPrecoPlano');
        return 0;
    }

    // Arredondar usuários
    const usuariosArredondados = arredondarPessoas(usuarios);
    
    if (usuariosArredondados === 'Consultar Comercial') {
        return 'Consultar Comercial';
    }

    // Chave do cache
    const cacheKey = `${plano}_${usuariosArredondados}`;
    
    // Retornar do cache se existir
    if (cachePrecos[cacheKey] !== undefined) {
        console.log(`✅ Preço do cache: ${plano} - ${usuariosArredondados} usuários = R$ ${cachePrecos[cacheKey]}`);
        return cachePrecos[cacheKey];
    }

    // Se não estiver no cache, buscar da API em background
    buscarPrecoAPIBackground(plano, usuarios);
    
    // Retornar 0 enquanto carrega (form.js vai atualizar quando chegar a resposta)
    return 0;
}

// ============================================================================
// FUNÇÃO: BUSCAR PREÇO DA API (BACKGROUND - NÃO BLOQUEIA)
// ============================================================================
function buscarPrecoAPIBackground(plano, usuarios) {
    /**
     * Busca o preço da API em background (não bloqueia a interface)
     * Atualiza o cache e o formulário quando a resposta chegar
     */
    
    const usuariosArredondados = arredondarPessoas(usuarios);
    const cacheKey = `${plano}_${usuariosArredondados}`;
    
    // Não buscar novamente se já está no cache
    if (cachePrecos[cacheKey] !== undefined) {
        return;
    }

    // Evitar múltiplas requisições simultâneas para a mesma chave
    if (requisicoesPendentes[cacheKey]) {
        console.log(`⏳ Requisição já pendente para: ${cacheKey}`);
        return;
    }

    requisicoesPendentes[cacheKey] = true;

    const url = `${API_BASE_URL}/api/preco_plano/${plano}/${usuarios}`;
    console.log(`🔄 Buscando preço da API: ${url}`);
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.sucesso && data.valor !== null) {
                // Armazenar no cache
                cachePrecos[cacheKey] = data.valor;
                console.log(`✅ Preço obtido da API: ${plano} - ${usuariosArredondados} usuários = R$ ${data.valor}`);
                
                // CRÍTICO: Atualizar o formulário IMEDIATAMENTE
                atualizarFormularioAposCarregamento();
            } else {
                console.warn(`⚠️ Preço não encontrado: ${data.mensagem}`);
            }
        })
        .catch(error => {
            console.error('❌ Erro ao obter preço do plano:', error);
        })
        .finally(() => {
            // Remover flag de requisição pendente
            delete requisicoesPendentes[cacheKey];
        });
}

// ============================================================================
// FUNÇÃO: OBTER SERVIÇOS ADICIONAIS (SÍNCRONO COM CACHE)
// ============================================================================
function obterValorServicoAdicional(chaveServico, usuarios, quantidadeLicenca = 1) {
    /**
     * Busca o valor de um serviço adicional
     * VERSÃO SÍNCRONA: Retorna valor do cache ou 0 se não encontrado
     * 
     * Parâmetros:
     *   chaveServico (string): 'licenca_facial', 'gestao_arquivos', 'controle_ferias', 'requis_calc_int'
     *   usuarios (number): Quantidade de usuários
     *   quantidadeLicenca (number): Quantidade de licenças (para facial)
     * 
     * Retorna:
     *   number: Valor do serviço
     */
    
    // Validar entrada
    if (!chaveServico || usuarios <= 0) {
        return 0;
    }

    // Arredondar usuários
    const usuariosArredondados = arredondarPessoas(usuarios);
    
    if (usuariosArredondados === 'Consultar Comercial') {
        return 'Consultar Comercial';
    }

    // Chave do cache
    const cacheKey = `${chaveServico}_${usuariosArredondados}_${quantidadeLicenca}`;
    
    // Retornar do cache se existir
    if (cacheServicos[cacheKey] !== undefined) {
        console.log(`✅ Serviço do cache: ${chaveServico} = R$ ${cacheServicos[cacheKey]}`);
        return cacheServicos[cacheKey];
    }

    // Se não estiver no cache, buscar da API em background
    buscarServicoAPIBackground(chaveServico, usuarios, quantidadeLicenca);
    
    // Retornar 0 enquanto carrega
    return 0;
}

// ============================================================================
// FUNÇÃO: BUSCAR SERVIÇO DA API (BACKGROUND - NÃO BLOQUEIA)
// ============================================================================
function buscarServicoAPIBackground(chaveServico, usuarios, quantidadeLicenca = 1) {
    /**
     * Busca o valor do serviço da API em background
     * Atualiza o cache e o formulário quando a resposta chegar
     */
    
    const usuariosArredondados = arredondarPessoas(usuarios);
    const cacheKey = `${chaveServico}_${usuariosArredondados}_${quantidadeLicenca}`;
    
    // Não buscar novamente se já está no cache
    if (cacheServicos[cacheKey] !== undefined) {
        return;
    }

    // Evitar múltiplas requisições simultâneas para a mesma chave
    if (requisicoesPendentes[cacheKey]) {
        console.log(`⏳ Requisição já pendente para: ${cacheKey}`);
        return;
    }

    requisicoesPendentes[cacheKey] = true;

    // Mapear chave do serviço para nome do plano (usar o selecionado no formulário)
    const planoElement = document.querySelector('input[name="plano"]:checked');
    const plano = planoElement ? planoElement.value : 'Basic';

    const payload = {
        plano: plano,
        quant_pessoas: usuarios,
        servicos: [chaveServico],
        quantidade_licenca_facial: quantidadeLicenca
    };

    const url = `${API_BASE_URL}/api/calcular_servicos`;
    console.log(`🔄 Buscando serviço da API: ${chaveServico}`);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.sucesso && data.servicos && data.servicos.length > 0) {
                const valor = data.servicos[0].valor_total || 0;
                
                // Armazenar no cache
                cacheServicos[cacheKey] = valor;
                console.log(`✅ Serviço obtido da API: ${chaveServico} = R$ ${valor}`);
                
                // CRÍTICO: Atualizar o formulário IMEDIATAMENTE
                atualizarFormularioAposCarregamento();
            } else {
                console.warn(`⚠️ Serviço não encontrado: ${data.mensagem}`);
            }
        })
        .catch(error => {
            console.error('❌ Erro ao obter serviço adicional:', error);
        })
        .finally(() => {
            // Remover flag de requisição pendente
            delete requisicoesPendentes[cacheKey];
        });
}

// ============================================================================
// FUNÇÃO CRÍTICA: ATUALIZAR FORMULÁRIO APÓS CARREGAMENTO
// ============================================================================
function atualizarFormularioAposCarregamento() {
    /**
     * FUNÇÃO CRÍTICA: Força a atualização do resumo da proposta
     * Chamada assim que os dados chegam da API
     * Garante que os valores apareçam IMEDIATAMENTE
     */
    
    // Verificar se renderSummary existe (função do form.js)
    if (typeof renderSummary === 'function') {
        console.log('🔄 Atualizando formulário após carregamento...');
        renderSummary();
    } else {
        console.warn('⚠️ renderSummary não encontrada. Tentando alternativa...');
        
        // Alternativa: disparar evento de mudança para forçar atualização
        const usuariosInput = document.getElementById('usuarios');
        if (usuariosInput) {
            usuariosInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}

// ============================================================================
// FUNÇÃO: OBTER DESCRIÇÃO DA FUNCIONALIDADE
// ============================================================================
function obterDescricaoFuncionalidade(funcionalidade) {
    /**
     * Retorna a descrição legível de uma funcionalidade
     */
    const descricoes = {
        'licenca_facial': 'Licença Facial',
        'gestao_arquivos': 'Gestão de Arquivos',
        'controle_ferias': 'Controle de Férias',
        'requis_calc_int': 'Mais Requis Cálc Int'
    };
    return descricoes[funcionalidade] || funcionalidade;
}

// ============================================================================
// FUNÇÃO: OBTER NOME DO PLANO
// ============================================================================
function obterNomePlano(plano) {
    /**
     * Retorna o nome formatado do plano
     */
    return plano || '';
}

// ============================================================================
// FUNÇÃO: LIMPAR CACHE (OPCIONAL)
// ============================================================================
function limparCache() {
    /**
     * Limpa o cache de preços e serviços
     * Útil para forçar atualização dos dados
     */
    cachePrecos = {};
    cacheServicos = {};
    requisicoesPendentes = {};
    console.log('✅ Cache limpo');
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ precos.js carregado e pronto para usar');
    console.log(`📡 API Base URL: ${API_BASE_URL}`);
    console.log('🔄 Aguardando interações do usuário...');
});

// ============================================================================
// EXPORTAR FUNÇÕES (para uso em outros scripts)
// ============================================================================
// Estas funções estão disponíveis globalmente para form.js usar:
// obterPrecoPlano(plano, usuarios)
// obterValorServicoAdicional(chaveServico, usuarios, quantidadeLicenca)
// arredondarPessoas(usuarios)
// obterDescricaoFuncionalidade(funcionalidade)
// obterNomePlano(plano)
// limparCache()