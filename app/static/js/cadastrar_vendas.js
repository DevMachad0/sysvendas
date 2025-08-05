document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.formulario-venda');
    if (!form) return;

    // Impede submit ao pressionar Enter em qualquer campo do formulário
    form.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && e.target.tagName.toLowerCase() !== 'textarea') {
            e.preventDefault();
        }
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => { data[key] = value; });

        // --- NOVO: Captura o valor do select condicoes-venda ---
        const condicoesVendaSelect = document.getElementById('condicoes-venda-select');
        if (condicoesVendaSelect) {
            data.condicoes_venda = condicoesVendaSelect.value || "";
        }
        // Se for venda à vista, zera o valor_parcelas e desabilita o campo (não oculta!)
        const condicaoSelect = document.getElementById('condicoes');
        const valorParcelaInput = document.getElementById('valor_parcelas');
        if (
            condicaoSelect &&
            condicaoSelect.value === 'A/C | 1+1' &&
            condicoesVendaSelect &&
            condicoesVendaSelect.value === 'avista'
        ) {
            data.valor_parcelas = "0";
            if (valorParcelaInput) {
                valorParcelaInput.disabled = true;
                valorParcelaInput.value = "0";
            }
        } else {
            if (valorParcelaInput) valorParcelaInput.disabled = false;
        }
        // --- FIM NOVO ---

        // --- CORREÇÃO: Enviar lista de produtos no campo produto se for personalizado ---
        const produtoSelect = document.getElementById('produto');
        const produtosPersonalizadosStr = document.getElementById('produtos-personalizados-hidden')?.value || '';
        if (produtoSelect && (produtoSelect.value === '' || produtoSelect.value === 'Personalizado')) {
            // Envia a lista de produtos no campo produto, prefixado com "Personalizado:"
            data.produto = produtosPersonalizadosStr ? `Personalizado:${produtosPersonalizadosStr}` : '';
            data.produtos_personalizados = produtosPersonalizadosStr;
            data.valor_tabela = document.getElementById('valor_tabela')?.value || '';
            data.valor_parcelas = document.getElementById('valor_parcelas')?.value || '';
            data.valor_real = document.getElementById('valor_real')?.value || '';
            data.condicoes = document.getElementById('condicoes')?.value || '';
        }
        // --- FIM CORREÇÃO ---

        // Troca de comissão para desconto
        data.desconto = data.comissao || data.desconto || "";
        delete data.comissao;

        data.tipo_cliente = data.tipo_cliente || "";

        // Preenche automaticamente os dados do vendedor atribuído
        data.usuario_id = user._id || user.usuario_id || user.id || "";
        data.nome_vendedor = user.nome_vendedor || "";
        data.email_vendedor = user.email || "";
        data.fone_vendedor = user.fone_vendedor || user.fone || "";

        // Adiciona o usuário logado para o log (não o vendedor atribuído)
        data.user_username = user.username || "";

        // Ajuste para múltiplos e-mails
        data.email = data.emails
        data.emails = data.emails.split(',')[0] || "";

        // LOGS de movimentação (apenas logs) -- removido, agora feito no backend

        // Se for admin, abrir pop-up para selecionar vendedor
        if (user.tipo === "administrador" || user.tipo === "admin") {
            e.stopImmediatePropagation();
            abrirPopupSelecionarVendedor(async function(vendedorSelecionado) {
                data.usuario_id = vendedorSelecionado._id;
                data.nome_vendedor = vendedorSelecionado.nome_completo;
                data.email_vendedor = vendedorSelecionado.email;
                data.fone_vendedor = vendedorSelecionado.fone;
                // user_username já está preenchido acima
                enviarVenda(data);
            });
            return;
        }

        // Novo campo: desconto_autorizado (checkbox)
        const descontoCheckbox = document.getElementById('desconto_autorizado');
        data.desconto_autorizado = descontoCheckbox && descontoCheckbox.checked ? true : false;

        // NOVO: quantidade de acessos
        const qtdAcessosInput = document.getElementById('quantidade-acessos');
        if (qtdAcessosInput) {
            data.quantidade_acessos = qtdAcessosInput.value || 2;
        }

        enviarVenda(data);
    });

    async function enviarVenda(data) {
        // Mostra loading
        mostrarLoading();

        const resp = await fetch('/cadastrar_vendas', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await resp.json();

        // Esconde loading antes do alert
        esconderLoading();

        if (result.success) {
            // Log de movimentação: Cadastro de venda
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const now = new Date();
            fetch('/api/inserir_log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    data: now.toLocaleDateString('pt-BR'),
                    hora: now.toLocaleTimeString('pt-BR'),
                    modificacao: 'Cadastro de venda Nº: ' + result.numero_da_venda,
                    usuario: user.username || ''
                })
            });

            alert('Venda cadastrada com sucesso! Nº: ' + result.numero_da_venda);
            window.location.href = '/vendas';
        } else {
            alert('Erro ao cadastrar venda!\n' + (result.erro || ''));
        }
    }

    // Função para abrir pop-up e buscar vendedores
    function abrirPopupSelecionarVendedor(callback) {
        const popup = document.getElementById('popup-vendedor');
        const select = document.getElementById('select-vendedor');
        popup.style.display = 'flex';
        select.innerHTML = '<option>Carregando...</option>';
        fetch('/api/vendedores')
            .then(r => r.json())
            .then(lista => {
                select.innerHTML = '';
                lista.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v._id;
                    opt.textContent = v.nome_completo + (v.status === 'ativo' ? '' : ' (inativo)');
                    opt.disabled = v.status !== 'ativo';
                    opt.dataset.email = v.email;
                    opt.dataset.fone = v.fone;
                    select.appendChild(opt);
                });
            });

        document.getElementById('btn-cancelar-popup').onclick = function() {
            popup.style.display = 'none';
        };
        document.getElementById('btn-confirmar-vendedor').onclick = function() {
            const opt = select.options[select.selectedIndex];
            if (!opt || !opt.value) return;
            const vendedor = {
                _id: opt.value,
                nome_completo: opt.textContent.replace(/ \(inativo\)$/, ''),
                email: opt.dataset.email,
                fone: opt.dataset.fone
            };
            popup.style.display = 'none';
            callback(vendedor);
        };
    }

    // Preenchimento automático para reabrir venda
    const vendaReabrir = localStorage.getItem('venda_reabrir');
    if (vendaReabrir) {
        try {
            const venda = JSON.parse(vendaReabrir);
            for (const [key, value] of Object.entries(venda)) {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = !!value;
                    } else {
                        input.value = value;
                        input.dispatchEvent(new Event('input'));
                    }
                }
            }
        } catch {}
        localStorage.removeItem('venda_reabrir');
    }
});
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('telefone-input');
    const paisSelect = document.getElementById('telefone-pais-select');
    const btnAdd = document.getElementById('add-telefone');
    const lista = document.getElementById('telefones-list');
    const hidden = document.getElementById('fones-hidden');
    const btnDropdown = document.getElementById('btn-lista-telefones');
    let telefones = [];

    function renderTelefones() {
        lista.innerHTML = '';
        telefones.forEach((tel, idx) => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';
            li.style.alignItems = 'center';
            li.style.padding = '6px 12px';
            li.style.borderBottom = '1px solid #eee';
            li.textContent = idx === 0 ? `${tel} *` : tel; // Adiciona * ao primeiro
            const btnRemove = document.createElement('button');
            btnRemove.textContent = '✖';
            btnRemove.style.background = 'none';
            btnRemove.style.border = 'none';
            btnRemove.style.color = '#e74c3c';
            btnRemove.style.cursor = 'pointer';
            btnRemove.style.fontSize = '16px';
            btnRemove.title = 'Remover';
            btnRemove.addEventListener('click', function (e) {
                e.stopPropagation();
                telefones.splice(idx, 1);
                renderTelefones();
            });
            li.appendChild(btnRemove);
            lista.appendChild(li);
        });
        hidden.value = telefones.join(',');
        input.value = '';
        input.disabled = telefones.length >= 3;
        btnAdd.disabled = telefones.length >= 3;
        btnDropdown.textContent = telefones.length > 0
            ? `Telefones adicionados (${telefones.length}) ▼`
            : 'Telefones adicionados ▼';
    }

    function addTelefone() {
        const valor = input.value.trim();
        if (!valor || telefones.length >= 3) return;
        // Pega país/código/emoji
        const paisOption = paisSelect.options[paisSelect.selectedIndex];
        const codigo = paisOption.value;
        const emoji = paisOption.getAttribute('data-emoji') || '';
        // Monta telefone completo
        const telefoneCompleto = `${emoji} ${codigo} ${valor}`;
        if (!telefones.includes(telefoneCompleto)) {
            telefones.push(telefoneCompleto);
            renderTelefones();
        }
    }

    btnAdd.addEventListener('click', addTelefone);

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTelefone();
        }
    });

    btnDropdown.addEventListener('click', function () {
        if (lista.style.display === 'none' || lista.style.display === '') {
            lista.style.display = 'block';
        } else {
            lista.style.display = 'none';
        }
    });

    // Fecha dropdown ao clicar fora
    document.addEventListener('click', function (e) {
        if (!btnDropdown.contains(e.target) && !lista.contains(e.target)) {
            lista.style.display = 'none';
        }
    });

    // Atualiza maxlength e máscara conforme país selecionado
    function atualizarMascaraTelefonePorPais() {
        const codigo = paisSelect.value;
        if (codigo === '+55') {
            input.setAttribute('maxlength', '20');
            input.value = input.value.replace(/[^0-9()\-\s]/g, '');
        } else {
            input.setAttribute('maxlength', '20');
            // Para outros países, não aplica máscara, apenas permite até 20 caracteres (números, +, -, espaço)
            input.value = input.value.replace(/[^0-9+\-\s]/g, '');
        }
    }

    paisSelect.addEventListener('change', function () {
        input.value = '';
        atualizarMascaraTelefonePorPais();
    });

    input.addEventListener('input', function () {
        atualizarMascaraTelefonePorPais();
    });

    renderTelefones();
});
document.addEventListener('DOMContentLoaded', function () {
    const cepInput = document.getElementById('cep-input');
    const ruaInput = document.getElementById('rua-input');
    const bairroInput = document.getElementById('bairro-input');
    const cidadeInput = document.getElementById('cidade-input');
    const estadoInput = document.getElementById('estado-input');

    function limpaCamposEndereco() {
        ruaInput.value = '';
        bairroInput.value = '';
        cidadeInput.value = '';
        estadoInput.value = '';
    }

    cepInput.addEventListener('blur', function () {
      const cep = cepInput.value.replace(/\D/g, '');

      function preencherCamposBrasilAPI(data) {
          ruaInput.value = data.street || data.logradouro || '';
          bairroInput.value = data.neighborhood || data.bairro || '';
          cidadeInput.value = data.city || data.localidade || '';
          estadoInput.value = data.state || data.uf || '';
      }

      function preencherCamposAwesomeAPI(data) {
          ruaInput.value = data.address || '';
          bairroInput.value = data.district || '';
          cidadeInput.value = data.city || '';
          estadoInput.value = data.state || '';
      }

      function tentaAwesomeAPI() {
          fetch(`https://cep.awesomeapi.com.br/json/${cep}`)
              .then(response => response.json())
              .then(data => {
                  if (!data.erro && !data.message && !data.status) {
                      preencherCamposAwesomeAPI(data);
                  } else {
                      limpaCamposEndereco();
                      alert('CEP não encontrado em nenhuma base.');
                  }
              })
              .catch(() => {
                  limpaCamposEndereco();
                  alert('Erro ao consultar o CEP nas duas bases.');
              });
      }

      if (cep.length === 8) {
          fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`)
              .then(response => response.json())
              .then(data => {
                  if (!data.erro && !data.message) {
                      preencherCamposBrasilAPI(data);
                  } else {
                      // Tenta a segunda API
                      tentaAwesomeAPI();
                  }
              })
              .catch(() => {
                  // Se der erro, tenta a segunda API
                  tentaAwesomeAPI();
              });
      } else {
          limpaCamposEndereco();
      }
  });
});
document.addEventListener('DOMContentLoaded', function () {
    const cnpjCpfInput = document.getElementById('cnpj-cpf-input');
    const campoRazao = document.getElementById('campo-razao-social');
    const campoIdentidade = document.getElementById('campo-identidade');
    const labelIdentidade = document.getElementById('label-identidade');

    function isCNPJ(valor) {
        // Remove não dígitos
        const num = valor.replace(/\D/g, '');
        return num.length === 14;
    }

    function isCPF(valor) {
        const num = valor.replace(/\D/g, '');
        return num.length === 11;
    }

    function atualizarCampos() {
        const valor = cnpjCpfInput.value;
        if (isCNPJ(valor)) {
            campoRazao.style.display = '';
            labelIdentidade.textContent = 'Inscrição Estadual:';
        } else {
            campoRazao.style.display = 'none';
            labelIdentidade.textContent = 'Identidade:';
            // Limpa o campo razão social ao esconder
            const razaoInput = document.getElementById('razao-social-input');
            if (razaoInput) razaoInput.value = '';
        }
    }

    cnpjCpfInput.addEventListener('input', atualizarCampos);
    atualizarCampos();
});
document.addEventListener('DOMContentLoaded', function () {
    // CEP mask
    const cepInput = document.getElementById('cep-input');
    cepInput.addEventListener('input', function () {
        let v = cepInput.value.replace(/\D/g, '').slice(0,8);
        if (v.length > 5) v = v.slice(0,5) + '-' + v.slice(5);
        cepInput.value = v;
    });

    // Estado: só 2 letras maiúsculas
    const estadoInput = document.getElementById('estado-input');
    estadoInput.addEventListener('input', function () {
        estadoInput.value = estadoInput.value.replace(/[^a-zA-Z]/g, '').toUpperCase().slice(0,2);
    });

    // CNPJ/CPF mask
    const cnpjCpfInput = document.getElementById('cnpj-cpf-input');
    cnpjCpfInput.addEventListener('input', function () {
        let v = cnpjCpfInput.value.replace(/\D/g, '');
        if (v.length <= 11) {
            // CPF: 000.000.000-00
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        } else {
            // CNPJ: 00.000.000/0000-00
            v = v.replace(/^(\d{2})(\d)/, '$1.$2');
            v = v.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
            v = v.replace(/\.(\d{3})(\d)/, '.$1/$2');
            v = v.replace(/(\d{4})(\d)/, '$1-$2');
        }
        cnpjCpfInput.value = v.slice(0,18);
    });

    // Telefone mask
    const telefoneInput = document.getElementById('telefone-input');
    telefoneInput.addEventListener('input', function () {
        let v = telefoneInput.value.replace(/\D/g, '').slice(0,11);
        if (v.length > 10) {
            v = v.replace(/^(\d{2})(\d{5})(\d{4}).*/, '($1) $2-$3');
        } else if (v.length > 6) {
            v = v.replace(/^(\d{2})(\d{4})(\d{0,4}).*/, '($1) $2-$3');
        } else if (v.length > 2) {
            v = v.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
        } else {
            v = v.replace(/^(\d{0,2})/, '($1');
        }
        telefoneInput.value = v;
    });

    // --- INÍCIO: Permitir apenas números, ponto e vírgula nos campos de valor ---
    function valorInputMask(input) {
        input.addEventListener('input', function () {
            // Permite apenas números, ponto e vírgula
            let v = input.value.replace(/[^0-9.,]/g, '');
            // Só permite um ponto ou vírgula como separador decimal
            const partes = v.split(/[.,]/);
            if (partes.length > 2) {
                v = partes[0] + '.' + partes.slice(1).join('');
            }
            input.value = v;
        });
        input.addEventListener('keypress', function (e) {
            // Bloqueia qualquer caractere que não seja número, ponto ou vírgula
            if (!/[0-9.,]/.test(e.key)) {
                e.preventDefault();
            }
        });
        input.addEventListener('paste', function (e) {
            // Impede colar texto com letras
            const pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (/[^0-9.,]/.test(pasted)) {
                e.preventDefault();
            }
        });
    }
    const valorParcelaInput = document.getElementById('valor_parcelas');
    if (valorParcelaInput) valorInputMask(valorParcelaInput);

    const valorEntradaInput = document.getElementById('valor_entrada');
    if (valorEntradaInput) valorInputMask(valorEntradaInput);

    const valorVendaAvistaInput = document.getElementById('valor_venda_avista');
    if (valorVendaAvistaInput) valorInputMask(valorVendaAvistaInput);
    // --- FIM: Permitir apenas números, ponto e vírgula nos campos de valor ---
});
document.addEventListener('DOMContentLoaded', function () {
    // --- E-mails múltiplos ---
    const emailInput = document.getElementById('email-input');
    const btnAddEmail = document.getElementById('add-email');
    const listaEmails = document.getElementById('emails-list');
    const hiddenEmails = document.getElementById('emails-hidden');
    const btnDropdownEmails = document.getElementById('btn-lista-emails');
    let emails = [];

    function renderEmails() {
        listaEmails.innerHTML = '';
        emails.forEach((mail, idx) => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';
            li.style.alignItems = 'center';
            li.style.padding = '6px 12px';
            li.style.borderBottom = '1px solid #eee';
            li.textContent = idx === 0 ? `${mail} *` : mail; // Adiciona * ao primeiro
            const btnRemove = document.createElement('button');
            btnRemove.textContent = '✖';
            btnRemove.style.background = 'none';
            btnRemove.style.border = 'none';
            btnRemove.style.color = '#e74c3c';
            btnRemove.style.cursor = 'pointer';
            btnRemove.style.fontSize = '16px';
            btnRemove.title = 'Remover';
            btnRemove.addEventListener('click', function (e) {
                e.stopPropagation();
                emails.splice(idx, 1);
                renderEmails();
            });
            li.appendChild(btnRemove);
            listaEmails.appendChild(li);
        });
        hiddenEmails.value = emails.join(',');
        emailInput.value = '';
        emailInput.disabled = emails.length >= 3;
        btnAddEmail.disabled = emails.length >= 3;
        btnDropdownEmails.textContent = emails.length > 0
            ? `E-mails adicionados (${emails.length}) ▼`
            : 'E-mails adicionados ▼';
    }

    function validarEmail(email) {
        // Regex simples para validação de e-mail
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function addEmail() {
        const valor = emailInput.value.trim();
        if (valor && emails.length < 3 && !emails.includes(valor) && validarEmail(valor)) {
            emails.push(valor);
            renderEmails();
        }
    }

    btnAddEmail && btnAddEmail.addEventListener('click', addEmail);

    emailInput && emailInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addEmail();
        }
    });

    btnDropdownEmails && btnDropdownEmails.addEventListener('click', function () {
        if (listaEmails.style.display === 'none' || listaEmails.style.display === '') {
            listaEmails.style.display = 'block';
        } else {
            listaEmails.style.display = 'none';
        }
    });

    // Fecha dropdown ao clicar fora
    document.addEventListener('click', function (e) {
        if (!btnDropdownEmails.contains(e.target) && !listaEmails.contains(e.target)) {
            listaEmails.style.display = 'none';
        }
    });

    renderEmails();
});
document.addEventListener('DOMContentLoaded', function () {
    // Impede seleção de data anterior à data atual em "Data prestação inicial"
    const dataPrestacaoInput = document.querySelector('input[name="data_prestacao_inicial"]');
    if (dataPrestacaoInput) {
        const hoje = new Date();
        const yyyy = hoje.getFullYear();
        const mm = String(hoje.getMonth() + 1).padStart(2, '0');
        const dd = String(hoje.getDate()).padStart(2, '0');
        const hojeStr = `${yyyy}-${mm}-${dd}`;
        dataPrestacaoInput.setAttribute('min', hojeStr);

        dataPrestacaoInput.addEventListener('change', function () {
            if (dataPrestacaoInput.value < hojeStr) {
                alert('Selecione uma data igual ou posterior à data atual.');
                dataPrestacaoInput.value = hojeStr;
            }
        });
    }
});
// Preenche o nome do vendedor a partir do localStorage
document.addEventListener('DOMContentLoaded', function () {
const span = document.getElementById('nome-vendedor');
const user = JSON.parse(localStorage.getItem('user') || '{}');
span.textContent = user.nome_vendedor || '';
});

document.addEventListener('DOMContentLoaded', function () {
  // Atualiza classe do SELECT de tipo do cliente (cor)
  const selectTipo = document.getElementById('tipo-cliente-input');
  if (selectTipo) {
    function updateTipoClienteSelectClass() {
      selectTipo.classList.remove('verde', 'vermelho');
      const val = (selectTipo.value || '').toLowerCase();
      if (val === 'verde' || val === 'vermelho') {
        selectTipo.classList.add(val);
      }
    }
    selectTipo.addEventListener('change', updateTipoClienteSelectClass);
    updateTipoClienteSelectClass();
  }
});

document.addEventListener("DOMContentLoaded", function () {
    const produtosJsonDiv = document.getElementById("produtos-json");
    const produtosDados = JSON.parse(produtosJsonDiv.dataset.produtos);

    const produtoSelect = document.getElementById('produto');
    const condicaoSelect = document.getElementById('condicoes');
    const valorInput = document.getElementById('valor_tabela');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorRealInput = document.getElementById('valor_real');
    const valorEntradaInput = document.getElementById('valor_entrada'); // NOVO

    function extrairParcelas(condicaoTexto) {
      const matchX = condicaoTexto.match(/(\d+)[xX]/);
      if (matchX) {
        return parseInt(matchX[1]);
      }
  
      const matchMais = condicaoTexto.match(/(\d+)\s*\+\s*(\d+)/);
      if (matchMais) {
        return parseInt(matchMais[1]) + parseInt(matchMais[2]);
      }
  
      return null;
    }
  
    function calcularValorReal() {
      const condicaoTexto = condicaoSelect.value;
      const parcelas = extrairParcelas(condicaoTexto);
      const valorParcela = parseFloat(valorParcelaInput.value.replace(',', '.'));
      const valorEntrada = valorEntradaInput ? parseFloat(valorEntradaInput.value.replace(',', '.')) : 0;

      let total = 0;
      if (!isNaN(parcelas) && !isNaN(valorParcela)) {
        total = parcelas * valorParcela;
      }
      if (!isNaN(valorEntrada) && valorEntrada > 0) {
        total += valorEntrada;
      }
      valorRealInput.value = total > 0 ? total.toFixed(2) : '';
    }
  
    produtoSelect.addEventListener('change', function () {
      const produto = this.value;
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      valorInput.value = '';
      valorParcelaInput.value = '';
      valorRealInput.value = '';
  
      if (produto && produtosDados[produto]) {
        condicaoSelect.disabled = false;
        produtosDados[produto].forEach(item => {
          const option = document.createElement('option');
          option.value = item.condicao;
          option.textContent = item.condicao;
          option.dataset.valor = item.valor;
          condicaoSelect.appendChild(option);
        });
      } else {
        condicaoSelect.disabled = true;
      }
    });
  
    condicaoSelect.addEventListener('change', function () {
      const selectedOption = this.options[this.selectedIndex];
      const valor = selectedOption.dataset.valor || '';
      valorInput.value = valor;
  
      calcularValorReal();
    });
  
    valorParcelaInput.addEventListener('input', calcularValorReal);
  
    // NOVO: recalcular ao alterar entrada
    if (valorEntradaInput) {
      valorEntradaInput.addEventListener('input', calcularValorReal);
    }
  });
document.addEventListener('DOMContentLoaded', function () {
  // Produto personalizado dinâmica
  const produtoSelect = document.getElementById('produto');
  const btnAddProduto = document.getElementById('btn-add-produto');
  const listaProdutos = document.getElementById('lista-produtos-personalizados');
  const hiddenProdutos = document.getElementById('produtos-personalizados-hidden');
  const personalizadoArea = document.getElementById('personalizado-area');
  let produtosPersonalizados = [];
  let selectTemp = null;
  const produtosJsonDiv = document.getElementById("produtos-json");
  const produtosDados = JSON.parse(produtosJsonDiv.dataset.produtos);
  const valorEntradaInput = document.getElementById('valor_entrada'); // NOVO

  // Salva as opções originais do select para restaurar depois
  const produtoSelectOriginal = produtoSelect.innerHTML;

  function renderListaProdutos() {
    listaProdutos.innerHTML = '';
    produtosPersonalizados.forEach((prod, idx) => {
      const li = document.createElement('li');
      li.textContent = prod.label;
      const btnRemove = document.createElement('button');
      btnRemove.textContent = '✖';
      btnRemove.type = 'button';
      btnRemove.title = 'Remover';
      btnRemove.onclick = function () {
        produtosPersonalizados.splice(idx, 1);
        renderListaProdutos();
        // Se após remover, ficou com menos de 2 produtos, reseta condição
        if (produtosPersonalizados.length < 2) {
          const condicaoSelect = document.getElementById('condicoes');
          condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
          condicaoSelect.disabled = true;
          document.getElementById('valor_tabela').value = '';
          document.getElementById('valor_parcelas').value = '';
          document.getElementById('valor_real').value = '';
        }
        // Sempre atualiza condições se for personalizado
        if (produtoSelect.value === 'Personalizado') {
          atualizarCondicoesPersonalizado();
        }
      };
      li.appendChild(btnRemove);
      listaProdutos.appendChild(li);
    });
    hiddenProdutos.value = produtosPersonalizados.map(p => p.value).join(',');

    // Mostra ou esconde o botão "+" conforme o número de produtos
    if (produtosPersonalizados.length >= 3) {
      btnAddProduto.style.display = 'none';
    } else if (produtoSelect.value === 'Personalizado') {
      btnAddProduto.style.display = '';
    }
    // Atualiza condições se for personalizado
    if (produtoSelect.value === 'Personalizado') {
      atualizarCondicoesPersonalizado();
    }
  }

  function atualizarCondicoesPersonalizado() {
    const condicaoSelect = document.getElementById('condicoes');
    const valorTabelaInput = document.getElementById('valor_tabela');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorRealInput = document.getElementById('valor_real');

    condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
    // Só habilita se tiver pelo menos 2 produtos
    condicaoSelect.disabled = produtosPersonalizados.length < 2;

    if (produtosPersonalizados.length < 2) {
      valorTabelaInput.value = '';
      valorParcelaInput.value = '';
      valorRealInput.value = '';
      return;
    }

    // Junta todas as condições possíveis dos produtos selecionados
    let condicoesMap = {};
    produtosPersonalizados.forEach(prod => {
      const condicoes = produtosDados[prod.value] || [];
      condicoes.forEach(item => {
        if (!condicoesMap[item.condicao]) {
          condicoesMap[item.condicao] = 0;
        }
        let valor = parseFloat(item.valor.toString().replace(',', '.')) || 0;
        condicoesMap[item.condicao] += valor;
      });
    });

    Object.entries(condicoesMap).forEach(([condicao, valorTotal]) => {
      const option = document.createElement('option');
      option.value = condicao;
      option.textContent = condicao;
      option.dataset.valor = valorTotal.toFixed(2);
      condicaoSelect.appendChild(option);
    });
  }

  produtoSelect.addEventListener('change', function () {
    if (produtoSelect.value === 'Personalizado') {
      // Altera o select principal para mostrar "Personalizado" fixo e mostra "+"
      produtoSelect.innerHTML = '<option value="Personalizado" selected>Personalizado</option>' +
        '<option value="">Desistir do personalizado</option>';
      btnAddProduto.style.display = produtosPersonalizados.length < 3 ? '' : 'none';
      personalizadoArea.style.display = '';
      produtosPersonalizados = [];
      renderListaProdutos();
      // Reseta condição
      const condicaoSelect = document.getElementById('condicoes');
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      condicaoSelect.disabled = true;
      document.getElementById('valor_tabela').value = '';
      document.getElementById('valor_parcelas').value = '';
      document.getElementById('valor_real').value = '';
    } else if (produtoSelect.value === '') {
      // Se selecionar "Desistir do personalizado", restaura opções originais
      produtoSelect.innerHTML = produtoSelectOriginal;
      btnAddProduto.style.display = 'none';
      personalizadoArea.style.display = 'none';
      produtosPersonalizados = [];
      renderListaProdutos();
      // Lógica padrão já existente para produto único
      const condicaoSelect = document.getElementById('condicoes');
      const valorTabelaInput = document.getElementById('valor_tabela');
      const valorParcelaInput = document.getElementById('valor_parcelas');
      const valorRealInput = document.getElementById('valor_real');
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      valorTabelaInput.value = '';
      valorParcelaInput.value = '';
      valorRealInput.value = '';
      if (produtoSelect.value && produtosDados[produtoSelect.value]) {
        condicaoSelect.disabled = false;
        produtosDados[produtoSelect.value].forEach(item => {
          const option = document.createElement('option');
          option.value = item.condicao;
          option.textContent = item.condicao;
          option.dataset.valor = item.valor;
          condicaoSelect.appendChild(option);
        });
      } else {
        condicaoSelect.disabled = true;
      }
    } else {
      // Seleção de produto comum
      btnAddProduto.style.display = 'none';
      personalizadoArea.style.display = 'none';
      produtosPersonalizados = [];
      renderListaProdutos();
      // Lógica padrão já existente para produto único
      const condicaoSelect = document.getElementById('condicoes');
      const valorTabelaInput = document.getElementById('valor_tabela');
      const valorParcelaInput = document.getElementById('valor_parcelas');
      const valorRealInput = document.getElementById('valor_real');
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      valorTabelaInput.value = '';
      valorParcelaInput.value = '';
      valorRealInput.value = '';
      if (produtoSelect.value && produtosDados[produtoSelect.value]) {
        condicaoSelect.disabled = false;
        produtosDados[produtoSelect.value].forEach(item => {
          const option = document.createElement('option');
          option.value = item.condicao;
          option.textContent = item.condicao;
          option.dataset.valor = item.valor;
          condicaoSelect.appendChild(option);
        });
      } else {
        condicaoSelect.disabled = true;
      }
    }
  });

  btnAddProduto.addEventListener('click', function () {
    // Cria apenas um select temporário por vez
    if (selectTemp && document.body.contains(selectTemp)) {
      selectTemp.focus();
      return;
    }
    selectTemp = document.createElement('select');
    selectTemp.innerHTML = `<option value="">Selecione...</option>` +
      Object.keys(produtosDados).map(prod => `<option value="${prod}">${prod}</option>`).join('');
    selectTemp.style.marginRight = '8px';
    selectTemp.onchange = function () {
      const value = selectTemp.value;
      const label = selectTemp.options[selectTemp.selectedIndex]?.textContent.trim();
      // --- ALTERADO: Permitir produtos repetidos ---
      if (!value /*|| produtosPersonalizados.some(p => p.value === value)*/ || produtosPersonalizados.length >= 3) return;
      produtosPersonalizados.push({ value, label });
      renderListaProdutos();
      selectTemp.remove();
      selectTemp = null;
      atualizarCondicoesPersonalizado();
    };
    // Adiciona o select temporário antes do botão
    btnAddProduto.parentNode.insertBefore(selectTemp, btnAddProduto);
    selectTemp.focus();
  });

  // Garante que ao enviar o formulário, se for personalizado, o campo produto fica vazio
  const form = document.querySelector('.formulario-venda');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (produtoSelect.value === 'Personalizado') {
        produtoSelect.value = '';
      }
    });
  }

  // Atualiza valor da tabela e cálculo ao selecionar condição (personalizado ou não)
  const condicaoSelect = document.getElementById('condicoes');
  const valorTabelaInput = document.getElementById('valor_tabela');
  const valorParcelaInput = document.getElementById('valor_parcelas');
  const valorRealInput = document.getElementById('valor_real');

  function extrairParcelas(condicaoTexto) {
    const matchX = condicaoTexto.match(/(\d+)[xX]/);
    if (matchX) {
      return parseInt(matchX[1]);
    }
    const matchMais = condicaoTexto.match(/(\d+)\s*\+\s*(\d+)/);
    if (matchMais) {
      return parseInt(matchMais[1]) + parseInt(matchMais[2]);
    }
    return null;
  }

  function calcularValorReal() {
    const condicaoTexto = condicaoSelect.value;
    const parcelas = extrairParcelas(condicaoTexto);
    const valorParcela = parseFloat(valorParcelaInput.value.replace(',', '.'));
    const valorEntrada = valorEntradaInput ? parseFloat(valorEntradaInput.value.replace(',', '.')) : 0;
    let total = 0;
    if (!isNaN(parcelas) && !isNaN(valorParcela)) {
      total = parcelas * valorParcela;
    }
    if (!isNaN(valorEntrada) && valorEntrada > 0) {
      total += valorEntrada;
    }
    valorRealInput.value = total > 0 ? total.toFixed(2) : '';
  }

  condicaoSelect.addEventListener('change', function () {
    const selectedOption = this.options[this.selectedIndex];
    const valor = selectedOption.dataset.valor || '';
    valorTabelaInput.value = valor;
    calcularValorReal();
  });

  valorParcelaInput.addEventListener('input', calcularValorReal);

  // NOVO: recalcular ao alterar entrada
  if (valorEntradaInput) {
    valorEntradaInput.addEventListener('input', calcularValorReal);
  }

  // Oculta o botão de desconto autorizado se for vendedor
  var user = JSON.parse(localStorage.getItem('user') || '{}');
  if (user.tipo === 'vendedor') {
    var labelDesconto = document.getElementById('label-desconto-autorizado');
    var campoTipoCliente = document.getElementById('tipo-cliente');
    if (labelDesconto) labelDesconto.style.display = 'none';
    if (campoTipoCliente) campoTipoCliente.style.display = 'none';
  }
});

// Funções de loading
function mostrarLoading() {
    let loader = document.getElementById('custom-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'custom-loader';
        loader.style.position = 'fixed';
        loader.style.top = '0';
        loader.style.left = '0';
        loader.style.width = '100vw';
        loader.style.height = '100vh';
        loader.style.background = 'rgba(255,255,255,0.7)';
        loader.style.display = 'flex';
        loader.style.alignItems = 'center';
        loader.style.justifyContent = 'center';
        loader.style.zIndex = '9999';
        loader.innerHTML = '<div style="padding:30px 40px;background:#fff;border-radius:10px;box-shadow:0 2px 12px #0002;font-size:20px;display:flex;flex-direction:column;align-items:center;"><div class="spinner" style="margin-bottom:12px;width:40px;height:40px;border:5px solid #eee;border-top:5px solid #007bff;border-radius:50%;animation:spin 1s linear infinite;"></div>Registrando venda...</div>';
        document.body.appendChild(loader);

        // Spinner CSS
        const style = document.createElement('style');
        style.innerHTML = '@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}';
        document.head.appendChild(style);
    } else {
        loader.style.display = 'flex';
    }
}

function esconderLoading() {
    const loader = document.getElementById('custom-loader');
    if (loader) loader.style.display = 'none';
}
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.formulario-venda');
  form.addEventListener('submit', function(e) {
    // Validação obrigatória das listas de emails e telefones
    const emails = (document.getElementById('emails-hidden').value || '').split(',').map(x => x.trim()).filter(x => x);
    const fones = (document.getElementById('fones-hidden').value || '').split(',').map(x => x.trim()).filter(x => x);

    // Verifica se as listas estão realmente preenchidas (não apenas o botão)
    const emailsList = document.getElementById('emails-list');
    const fonesList = document.getElementById('telefones-list');
    const emailsTemLi = emailsList && emailsList.querySelectorAll('li').length > 0;
    const fonesTemLi = fonesList && fonesList.querySelectorAll('li').length > 0;

    if (emails.length === 0 || !emailsTemLi) {
      alert('Adicione pelo menos um e-mail.');
      e.preventDefault();
      e.stopImmediatePropagation();
      return false;
    }
    if (fones.length === 0 || !fonesTemLi) {
      alert('Adicione pelo menos um telefone.');
      e.preventDefault();
      e.stopImmediatePropagation();
      return false;
    }
  });
});
document.addEventListener("DOMContentLoaded", function () {
    let valorAcessoExtra = 0;
    let valorAcessoAtualizacao = 0;

    fetch('/api/configs/valor_acesso')
      .then(r => r.json())
      .then(cfg => {
        valorAcessoExtra = parseFloat(cfg.valor_acesso_nova_venda || cfg.valor_acesso || 0) || 0;
        valorAcessoAtualizacao = parseFloat(cfg.valor_acesso_atualizacao || 0) || 0;
      });

    const produtoSelect = document.getElementById('produto');
    const qtdAcessosInput = document.getElementById('quantidade-acessos');
    const valorTabelaInput = document.getElementById('valor_tabela');
    const condicaoSelect = document.getElementById('condicoes');
    const hiddenProdutos = document.getElementById('produtos-personalizados-hidden');
    let valorBaseTabela = 0;

    function produtoEhLicencaExtra() {
      return produtoSelect && produtoSelect.value && produtoSelect.value.toLowerCase().includes('licença extra');
    }

    function produtoEhPersonalizado() {
      return produtoSelect && produtoSelect.value && produtoSelect.value === 'Personalizado';
    }

    // CORRIGIDO: Conta apenas se há pelo menos 1 'atualização' E pelo menos 1 'licença extra - atualização'
    function temAtualizacaoELicencaExtra() {
      if (!produtoEhPersonalizado() || !hiddenProdutos) return false;
      const produtos = (hiddenProdutos.value || '').split(',').map(p => p.trim().toLowerCase());
      const temAtualizacao = produtos.some(p => p.includes('atualização') && !p.includes('licença extra'));
      const temLicencaExtraAtualizacao = produtos.some(p => p.includes('licença extra - atualização'));
      return temAtualizacao && temLicencaExtraAtualizacao;
    }

    function contarLicencaExtraAtualizacao() {
      if (!produtoEhPersonalizado() || !hiddenProdutos) return 0;
      const produtos = (hiddenProdutos.value || '').split(',').map(p => p.trim().toLowerCase());
      // Conta quantos são 'licença extra - atualização'
      return produtos.filter(p => p.includes('licença extra - atualização')).length;
    }

    // Função para atualizar quantidade de acessos para personalizado (mínimo 3 se condição especial)
    function atualizarQtdAcessosPersonalizado() {
      if (!qtdAcessosInput) return;
      if (produtoEhPersonalizado() && temAtualizacaoELicencaExtra()) {
        const minAcessos = 2 + contarLicencaExtraAtualizacao(); // sempre mínimo 3
        // Se for menor que minAcessos, força
        if (parseInt(qtdAcessosInput.value, 10) < minAcessos || isNaN(parseInt(qtdAcessosInput.value, 10))) {
          qtdAcessosInput.value = minAcessos;
        }
        qtdAcessosInput.setAttribute('min', minAcessos);
      } else if (produtoEhLicencaExtra()) {
        qtdAcessosInput.value = 1;
        qtdAcessosInput.setAttribute('min', 1);
      } else if (produtoSelect && produtoSelect.value && produtoSelect.value !== '') {
        qtdAcessosInput.value = 2;
        qtdAcessosInput.setAttribute('min', 2);
      } else {
        qtdAcessosInput.value = 0;
        qtdAcessosInput.setAttribute('min', 0);
      }
    }

    if (condicaoSelect) {
      condicaoSelect.addEventListener('change', function () {
        const opt = condicaoSelect.options[condicaoSelect.selectedIndex];
        valorBaseTabela = parseFloat(opt?.dataset.valor || 0) || 0;
        atualizarQtdAcessosPersonalizado(); // <- CHAMA AQUI TAMBÉM!
        atualizarValorTabelaPorAcesso();
      });
    }

    function atualizarValorTabelaPorAcesso() {
      let qtd = parseInt(qtdAcessosInput.value, 10) || 0;
      let extras = Math.max(0, qtd - 2);
      let valorExtra = valorAcessoExtra;

      if (produtoEhLicencaExtra()) {
        if (qtdAcessosInput.value === "" || qtd < 1) {
          qtdAcessosInput.value = 1;
          qtd = 1;
        }
        if (qtd > 1) {
          valorTabelaInput.value = (valorBaseTabela * qtd).toFixed(2);
        } else {
          valorTabelaInput.value = valorBaseTabela > 0 ? valorBaseTabela.toFixed(2) : '';
        }
        return;
      }

      if (produtoEhPersonalizado() && temAtualizacaoELicencaExtra()) {
        const minAcessos = 2 + contarLicencaExtraAtualizacao();
        let extrasPersonalizado = Math.max(0, qtd - minAcessos);
        let valorFinal = valorBaseTabela + (extrasPersonalizado * valorExtra);
        valorTabelaInput.value = valorFinal > 0 ? valorFinal.toFixed(2) : '';
        return;
      }

      let valorFinal = valorBaseTabela + (extras * valorExtra);
      valorTabelaInput.value = valorFinal > 0 ? valorFinal.toFixed(2) : '';
    }

    if (qtdAcessosInput) {
      qtdAcessosInput.addEventListener('input', function() {
        if (produtoEhPersonalizado() && temAtualizacaoELicencaExtra()) {
          const minAcessos = 2 + contarLicencaExtraAtualizacao();
          if (parseInt(qtdAcessosInput.value, 10) < minAcessos || isNaN(parseInt(qtdAcessosInput.value, 10))) {
            qtdAcessosInput.value = minAcessos;
          }
          qtdAcessosInput.setAttribute('min', minAcessos);
        } else if (produtoEhLicencaExtra()) {
          if (qtdAcessosInput.value === "" || parseInt(qtdAcessosInput.value, 10) < 1) {
            qtdAcessosInput.value = 1;
            qtdAcessosInput.setAttribute('min', 1);
          }
        } else {
          if (produtoSelect && produtoSelect.value && parseInt(qtdAcessosInput.value, 10) < 2) {
            qtdAcessosInput.value = 2;
            qtdAcessosInput.setAttribute('min', 2);
          }
        }
        atualizarValorTabelaPorAcesso();
      });
    }

    if (produtoSelect) {
      produtoSelect.addEventListener('change', function() {
        atualizarQtdAcessosPersonalizado();
        const opt = condicaoSelect && condicaoSelect.options[condicaoSelect.selectedIndex];
        valorBaseTabela = parseFloat(opt?.dataset.valor || 0) || 0;
        atualizarValorTabelaPorAcesso();
      });
    }

    if (hiddenProdutos) {
      hiddenProdutos.addEventListener('input', function() {
        atualizarQtdAcessosPersonalizado();
        atualizarValorTabelaPorAcesso();
      });
    }

    // Também chama na inicialização para garantir
    if (produtoSelect && produtoSelect.value && qtdAcessosInput) {
      atualizarQtdAcessosPersonalizado();
      const opt = condicaoSelect && condicaoSelect.options[condicaoSelect.selectedIndex];
      valorBaseTabela = parseFloat(opt?.dataset.valor || 0) || 0;
      atualizarValorTabelaPorAcesso();
    }
});
document.addEventListener('DOMContentLoaded', function () {
  // NOVA LÓGICA DINÂMICA PARA CONDIÇÕES DA VENDA
  const condicaoSelect = document.getElementById('condicoes');
  const condicoesVendaContainer = document.getElementById('condicoes-venda-container');
  const condicoesVendaSelect = document.getElementById('condicoes-venda-select');
  const campoValorVenda = document.getElementById('campo-valor-venda');
  const valorVendaAvistaInput = document.getElementById('valor_venda_avista');
  const campoEntrada = document.getElementById('campo-entrada');
  const campoParcela = document.getElementById('campo-parcela');
  const valorEntradaInput = document.getElementById('valor_entrada');
  const valorParcelaInput = document.getElementById('valor_parcelas');
  const valorRealInput = document.getElementById('valor_real');

  function atualizarCamposCondicoesVenda() {
    if (!condicaoSelect) return;
    const condicao = condicaoSelect.value;
    // Sempre mantém o campo-parcela visível, apenas desabilita/habilita o input conforme a lógica
    if (condicao === 'A/C | 1+1') {
      condicoesVendaContainer.style.display = '';
      condicoesVendaSelect.value = '';
      campoValorVenda.style.display = 'none';
      campoEntrada.style.display = '';
      campoParcela.style.display = '';
      valorVendaAvistaInput.value = '';
      // Desabilita campos conforme seleção
      if (condicoesVendaSelect.value === 'avista') {
        if (valorParcelaInput) {
          valorParcelaInput.disabled = true;
          valorParcelaInput.value = "0";
        }
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = false;
        if (valorEntradaInput) valorEntradaInput.disabled = true;
      } else if (condicoesVendaSelect.value === 'entrada_parcela') {
        if (valorParcelaInput) valorParcelaInput.disabled = false;
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = true;
        if (valorEntradaInput) valorEntradaInput.disabled = false;
      } else {
        if (valorParcelaInput) valorParcelaInput.disabled = false;
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = true;
        if (valorEntradaInput) valorEntradaInput.disabled = false;
      }
    } else {
      condicoesVendaContainer.style.display = 'none';
      campoValorVenda.style.display = 'none';
      campoEntrada.style.display = '';
      campoParcela.style.display = '';
      if (valorParcelaInput) valorParcelaInput.disabled = false;
      if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = true;
      if (valorEntradaInput) valorEntradaInput.disabled = false;
    }
    atualizarValorReal();
  }

  function atualizarValorReal() {
    // Se for condição especial e à vista
    if (
      condicaoSelect.value === 'A/C | 1+1' &&
      condicoesVendaSelect &&
      condicoesVendaSelect.value === 'avista'
    ) {
      valorRealInput.value = valorVendaAvistaInput.value || '';
      return;
    }
    // Se for condição especial e entrada + parcela, valor real deve ser entrada + parcela (não valor da tabela)
    if (
      condicaoSelect.value === 'A/C | 1+1' &&
      condicoesVendaSelect &&
      condicoesVendaSelect.value === 'entrada_parcela'
    ) {
      const valorEntrada = valorEntradaInput ? parseFloat(valorEntradaInput.value.replace(',', '.')) : 0;
      const valorParcela = valorParcelaInput ? parseFloat(valorParcelaInput.value.replace(',', '.')) : 0;
      let total = 0;
      if (!isNaN(valorEntrada)) total += valorEntrada;
      if (!isNaN(valorParcela)) total += valorParcela;
      valorRealInput.value = total > 0 ? total.toFixed(2) : '';
      return;
    }
    // Caso padrão (inclui entrada + parcela para outras condições)
    const condicaoTexto = condicaoSelect.value;
    const parcelas = extrairParcelas(condicaoTexto);
    const valorParcela = valorParcelaInput ? parseFloat(valorParcelaInput.value.replace(',', '.')) : 0;
    const valorEntrada = valorEntradaInput ? parseFloat(valorEntradaInput.value.replace(',', '.')) : 0;

    let total = 0;
    if (!isNaN(parcelas) && !isNaN(valorParcela)) {
      total = parcelas * valorParcela;
    }
    if (!isNaN(valorEntrada) && valorEntrada > 0) {
      total += valorEntrada;
    }
    valorRealInput.value = total > 0 ? total.toFixed(2) : '';
  }

  if (condicaoSelect) {
    condicaoSelect.addEventListener('change', function () {
      atualizarCamposCondicoesVenda();
    });
  }
  if (condicoesVendaSelect) {
    condicoesVendaSelect.addEventListener('change', function () {
      // Atualiza habilitação/desabilitação dos campos conforme seleção
      if (condicoesVendaSelect.value === 'avista') {
        campoValorVenda.style.display = '';
        campoEntrada.style.display = 'none';
        campoParcela.style.display = '';
        if (valorParcelaInput) {
          valorParcelaInput.disabled = true;
          valorParcelaInput.value = "0";
        }
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = false;
        if (valorEntradaInput) valorEntradaInput.disabled = true;
        valorEntradaInput.value = "";
      } else if (condicoesVendaSelect.value === 'entrada_parcela') {
        campoValorVenda.style.display = 'none';
        campoEntrada.style.display = '';
        campoParcela.style.display = '';
        if (valorParcelaInput) valorParcelaInput.disabled = false;
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = true;
        if (valorEntradaInput) valorEntradaInput.disabled = false;
        valorVendaAvistaInput.value = "";
      } else {
        campoValorVenda.style.display = 'none';
        campoEntrada.style.display = '';
        campoParcela.style.display = '';
        if (valorParcelaInput) valorParcelaInput.disabled = false;
        if (valorVendaAvistaInput) valorVendaAvistaInput.disabled = true;
        if (valorEntradaInput) valorEntradaInput.disabled = false;
      }
      atualizarValorReal();
    });
  }
  if (valorVendaAvistaInput) {
    valorVendaAvistaInput.addEventListener('input', atualizarValorReal);
  }
  if (valorEntradaInput) {
    valorEntradaInput.addEventListener('input', atualizarValorReal);
  }
  if (valorParcelaInput) {
    valorParcelaInput.addEventListener('input', atualizarValorReal);
  }

  // Inicialização
  atualizarCamposCondicoesVenda();
});
