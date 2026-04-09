// app/static/js/validators.js - VERSÃO AJUSTADA PARA SPRINT 1

console.log('✅ validators.js carregado com sucesso');

const DEBUG = typeof window !== 'undefined' ? (window.DEBUG || false) : false;

// ============================================
// VALIDADORES DE CNPJ
// ============================================

function validarCNPJ(cnpj) {
    try {
        const cnpjLimpo = String(cnpj || '').replace(/\D/g, '');

        if (cnpjLimpo.length !== 14) {
            return { valido: false, mensagem: 'CNPJ deve ter 14 dígitos.' };
        }

        if (cnpjLimpo === cnpjLimpo[0].repeat(14)) {
            return { valido: false, mensagem: 'CNPJ inválido (todos os dígitos iguais).' };
        }

        const cnpjBase = cnpjLimpo.substring(0, 12);
        const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
        let soma = 0;

        for (let i = 0; i < 12; i++) {
            soma += parseInt(cnpjBase[i]) * pesos1[i];
        }

        let resto = soma % 11;
        let dv1 = resto < 2 ? 0 : 11 - resto;

        if (parseInt(cnpjLimpo[12]) !== dv1) {
            return { valido: false, mensagem: 'CNPJ inválido. Dígito verificador incorreto.' };
        }

        const cnpjComDV1 = cnpjBase + dv1;
        const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
        soma = 0;

        for (let i = 0; i < 13; i++) {
            soma += parseInt(cnpjComDV1[i]) * pesos2[i];
        }

        resto = soma % 11;
        let dv2 = resto < 2 ? 0 : 11 - resto;

        if (parseInt(cnpjLimpo[13]) !== dv2) {
            return { valido: false, mensagem: 'CNPJ inválido. Dígito verificador incorreto.' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de CNPJ:', error);
        return { valido: false, mensagem: 'Erro ao validar CNPJ.' };
    }
}

// ============================================
// VALIDADORES DE EMAIL
// ============================================

function validarEmail(email) {
    try {
        const emailLimpo = String(email || '').trim();
        const padrao = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!padrao.test(emailLimpo)) {
            return { valido: false, mensagem: 'Email inválido. Verifique o formato (ex: usuario@exemplo.com).' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de email:', error);
        return { valido: false, mensagem: 'Erro ao validar email.' };
    }
}

// ============================================
// VALIDADORES DE TELEFONE E WHATSAPP
// ============================================

function validarTelefone(telefone) {
    try {
        const telefoneStr = String(telefone || '').trim();
        const numeros = telefoneStr.replace(/\D/g, '');

        if (numeros.length < 10 || numeros.length > 11) {
            return { valido: false, mensagem: 'Telefone deve ter 10 ou 11 dígitos.' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de telefone:', error);
        return { valido: false, mensagem: 'Erro ao validar telefone.' };
    }
}

function formatarTelefone(telefone) {
    try {
        const numeros = String(telefone || '').replace(/\D/g, '');

        if (numeros.length === 0) return '';

        if (numeros.length === 10) {
            return `(${numeros.substring(0, 2)}) ${numeros.substring(2, 6)}-${numeros.substring(6, 10)}`;
        }

        if (numeros.length === 11) {
            return `(${numeros.substring(0, 2)}) ${numeros.substring(2, 7)}-${numeros.substring(7, 11)}`;
        }

        return telefone;
    } catch (error) {
        if (DEBUG) console.error('Erro ao formatar telefone:', error);
        return telefone;
    }
}

function validarWhatsApp(whatsapp) {
    try {
        const whatsappStr = String(whatsapp || '').trim();
        const numeros = whatsappStr.replace(/\D/g, '');

        if (numeros.length !== 11 || numeros[2] !== '9') {
            return { valido: false, mensagem: 'WhatsApp inválido. Deve ser um celular com 11 dígitos e 9 após o DDD.' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de WhatsApp:', error);
        return { valido: false, mensagem: 'Erro ao validar WhatsApp.' };
    }
}

// ============================================
// VALIDADORES DE USUÁRIOS
// ============================================

function validarUsuarios(usuarios) {
    try {
        const num = parseInt(usuarios);

        if (isNaN(num) || num < 1 || num > 999) {
            return { valido: false, mensagem: 'Quantidade de pessoas deve estar entre 1 e 999.' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de usuários:', error);
        return { valido: false, mensagem: 'Erro ao validar quantidade de pessoas.' };
    }
}

function arredondarUsuarios(usuarios) {
    try {
        const num = parseInt(usuarios);

        if (isNaN(num) || num < 1) return 10;
        if (num % 10 === 0) return num;

        return Math.ceil(num / 10) * 10;
    } catch (error) {
        if (DEBUG) console.error('Erro ao arredondar usuários:', error);
        return 10;
    }
}

// ============================================
// VALIDADORES DE MOEDA
// ============================================

function validarMoeda(valor) {
    try {
        const num = typeof valor === 'string' ? desformatarMoeda(valor) : parseFloat(valor);

        if (isNaN(num) || num < 0) {
            return { valido: false, mensagem: 'Valor não pode ser negativo ou inválido.' };
        }

        if (num > 999999.99) {
            return { valido: false, mensagem: 'Valor muito alto (máximo R$ 999.999,99).' };
        }

        return { valido: true, mensagem: '' };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de moeda:', error);
        return { valido: false, mensagem: 'Erro ao validar valor monetário.' };
    }
}

function formatarMoeda(valor) {
    try {
        const num = typeof valor === 'string' ? desformatarMoeda(valor) : parseFloat(valor);

        if (isNaN(num)) return 'R$ 0,00';

        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(num);
    } catch (error) {
        if (DEBUG) console.error('Erro ao formatar moeda:', error);
        return 'R$ 0,00';
    }
}

function desformatarMoeda(valor) {
    if (!valor || typeof valor !== 'string') return 0;

    let limpo = valor.replace('R$', '').trim();
    limpo = limpo.replace(/\./g, '');
    limpo = limpo.replace(',', '.');

    const num = parseFloat(limpo);
    return isNaN(num) ? 0 : num;
}

// ============================================
// VALIDADORES DE DESCONTO
// ============================================

function validarDesconto(desconto) {
    try {
        const texto = String(desconto || '').trim();

        if (!texto) {
            return { valido: true, mensagem: '', tipo: 'valor', valor: 0 };
        }

        if (texto.includes('%')) {
            const percentual = parseFloat(texto.replace('%', '').replace(',', '.'));

            if (isNaN(percentual) || percentual < 0 || percentual > 100) {
                return { valido: false, mensagem: 'Desconto percentual deve estar entre 0 e 100%.' };
            }

            if (percentual > 50) {
                return { valido: false, mensagem: 'Desconto acima de 50% requer aprovação do gerente.' };
            }

            return { valido: true, mensagem: '', tipo: 'percentual', valor: percentual };
        }

        const valor = desformatarMoeda(texto);

        if (isNaN(valor) || valor < 0) {
            return { valido: false, mensagem: 'Desconto em valor não pode ser negativo ou inválido.' };
        }

        return { valido: true, mensagem: '', tipo: 'valor', valor: valor };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de desconto:', error);
        return { valido: false, mensagem: 'Erro ao validar desconto.' };
    }
}

// ============================================
// FUNÇÕES DE CÁLCULO
// ============================================

function calcularValorMensal(plano, usuarios) {
    const planosBase = {
        'Basic': 50.00,
        'PRO': 100.00,
        'Ultimate': 200.00,
        'Desktop': 150.00
    };

    const valorBase = planosBase[plano] || 0;
    const multiplicador = Math.max(1, Math.ceil((parseInt(usuarios) || 0) / 10));

    return valorBase * multiplicador;
}

function obterSetupPadrao(treinamento) {
    const setups = {
        'Online': 0.00,
        'Presencial': 350.00,
        'Híbrido': 250.00
    };

    return setups[treinamento] || 0.00;
}

function calcularDesconto(subtotal, descontoInfo) {
    try {
        if (!descontoInfo || !descontoInfo.valido) return 0;

        if (descontoInfo.tipo === 'percentual') {
            return subtotal * (descontoInfo.valor / 100);
        }

        return descontoInfo.valor;
    } catch (error) {
        if (DEBUG) console.error('Erro ao calcular desconto:', error);
        return 0;
    }
}

function calcularTotal(valorMensal, setup, treinamento, desconto, servicosAdicionais = 0, taxaUnica = 0) {
    try {
        const subtotal = valorMensal + setup + treinamento + servicosAdicionais + taxaUnica;
        const total = Math.max(subtotal - desconto, 0);

        return { subtotal, total };
    } catch (error) {
        if (DEBUG) console.error('Erro ao calcular total:', error);
        return { subtotal: 0, total: 0 };
    }
}

// ============================================
// SERVIÇOS ADICIONAIS
// ============================================

function validarServicosAdicionais(servicos, usuarios, plano) {
    try {
        const faixa = arredondarUsuarios(usuarios).toString();

        const tabelaPrecos = {
            'licenca_facial': { '10': 20, '20': 35, '30': 50, '40': 65, '50': 80, '60': 95 },
            'gestao_arquivos': { '10': 15, '20': 25, '30': 35, '40': 45, '50': 55, '60': 65 },
            'controle_ferias': { '10': 10, '20': 18, '30': 26, '40': 34, '50': 42, '60': 50 },
            'requis_calc_int': { '10': 25, '20': 45, '30': 65, '40': 85, '50': 105, '60': 125 }
        };

        let totalAdicionais = 0;
        let mensagem = '';

        Object.keys(servicos || {}).forEach(servico => {
            const qtd = parseInt(servicos[servico]) || 0;
            if (qtd > 0) {
                const precoFaixa = tabelaPrecos[servico] ? tabelaPrecos[servico][faixa] || 0 : 0;
                if (precoFaixa === 0) {
                    mensagem += `Preço não definido para ${servico} na faixa ${faixa}. `;
                } else {
                    totalAdicionais += qtd * precoFaixa;
                }
            }
        });

        return { valido: mensagem === '', mensagem, total: totalAdicionais };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação de serviços adicionais:', error);
        return { valido: false, mensagem: 'Erro ao validar serviços adicionais.', total: 0 };
    }
}

// ============================================
// DEMAIS FUNÇÕES
// ============================================

function calcularDataValidade(dias = 10) {
    try {
        const hoje = new Date();
        hoje.setDate(hoje.getDate() + dias);
        return hoje.toISOString().split('T')[0];
    } catch (error) {
        if (DEBUG) console.error('Erro ao calcular data de validade:', error);
        return new Date().toISOString().split('T')[0];
    }
}

function validarFormularioCompleto(formData) {
    try {
        const erros = {};

        const cnpjResult = validarCNPJ(formData.cnpj || '');
        if (!cnpjResult.valido) erros.cnpj = cnpjResult.mensagem;

        const emailResult = validarEmail(formData.email || '');
        if (!emailResult.valido) erros.email = emailResult.mensagem;

        if (formData.telefone) {
            const telResult = validarTelefone(formData.telefone);
            if (!telResult.valido) erros.telefone = telResult.mensagem;
        }

        const whatsappResult = validarWhatsApp(formData.whatsapp || '');
        if (!whatsappResult.valido) erros.whatsapp = whatsappResult.mensagem;

        const usuariosResult = validarUsuarios(formData.usuarios || 0);
        if (!usuariosResult.valido) erros.usuarios = usuariosResult.mensagem;

        ['setup', 'treinamentoValor', 'taxaUnica'].forEach(campo => {
            if (formData[campo]) {
                const moedaResult = validarMoeda(formData[campo]);
                if (!moedaResult.valido) erros[campo] = moedaResult.mensagem;
            }
        });

        const descontoResult = validarDesconto(formData.desconto || '');
        if (!descontoResult.valido) erros.desconto = descontoResult.mensagem;

        if (formData.servicosAdicionais) {
            const servicosResult = validarServicosAdicionais(formData.servicosAdicionais, formData.usuarios || 0, formData.plano || '');
            if (!servicosResult.valido) erros.servicos = servicosResult.mensagem;
        }

        const valido = Object.keys(erros).length === 0;

        let total = 0;
        if (valido) {
            const calc = calcularTotal(
                calcularValorMensal(formData.plano || '', formData.usuarios || 0),
                desformatarMoeda(formData.setup || '0'),
                desformatarMoeda(formData.treinamentoValor || '0'),
                calcularDesconto(
                    calcularValorMensal(formData.plano || '', formData.usuarios || 0) +
                    desformatarMoeda(formData.setup || '0') +
                    desformatarMoeda(formData.treinamentoValor || '0'),
                    descontoResult
                ),
                formData.servicosTotal || 0,
                desformatarMoeda(formData.taxaUnica || '0')
            );
            total = calc.total;
        }

        return { valido, erros, total, dataValidade: calcularDataValidade(10) };
    } catch (error) {
        if (DEBUG) console.error('Erro na validação geral do formulário:', error);
        return { valido: false, erros: { geral: 'Erro interno na validação.' }, total: 0 };
    }
}

async function consultarCNPJ(cnpj) {
    try {
        const cnpjLimpo = String(cnpj || '').replace(/\D/g, '');

        if (cnpjLimpo.length !== 14) {
            return { sucesso: false, mensagem: 'CNPJ deve ter 14 dígitos.' };
        }

        const resposta = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpjLimpo}`);

        if (!resposta.ok) {
            return { sucesso: false, mensagem: 'CNPJ não encontrado na consulta.' };
        }

        const dados = await resposta.json();

        return {
            sucesso: true,
            razaoSocial: dados.razao_social || '',
            nomeFantasia: dados.nome_fantasia || '',
            cnpj: dados.cnpj || cnpjLimpo
        };
    } catch (error) {
        return { sucesso: false, mensagem: 'Erro ao consultar CNPJ.' };
    }
}

console.log('✅ validators.js finalizado - Todas as funções disponíveis.');