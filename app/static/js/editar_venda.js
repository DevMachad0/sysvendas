document.addEventListener('DOMContentLoaded', function() {
  // Atualiza classe do SELECT de status
  function updateStatusSelectClass() {
    const select = document.getElementById('status-editar');
    if (!select) return;

    // Classes possíveis (com inicial maiúscula)
    const classes = ['Aprovada', 'Cancelada', 'Aguardando', 'Refazer', 'Faturado'];
    select.classList.remove(...classes);

    // Valor selecionado com inicial maiúscula
    const val = select.value ? select.value.charAt(0).toUpperCase() + select.value.slice(1).toLowerCase() : '';
    if (classes.includes(val)) {
      select.classList.add(val); // adiciona classe CSS correta
    }
  }

  // Atualiza classe do SELECT de tipo do cliente
  function updateTipoClienteSelectClass() {
    const select = document.getElementById('tipo-cliente-editar');
    if (!select) return;

    select.classList.remove('verde', 'vermelho');
    const val = (select.value || '').toLowerCase();
    if (val === 'verde' || val === 'vermelho') {
      select.classList.add(val);
    }
  }

  // Inicialização + eventos
  const selectStatus = document.getElementById('status-editar');
  const selectTipo = document.getElementById('tipo-cliente-editar');

  if (selectStatus) {
    selectStatus.addEventListener('change', updateStatusSelectClass);
    updateStatusSelectClass(); // <- aplica ao carregar
  }

  if (selectTipo) {
    selectTipo.addEventListener('change', updateTipoClienteSelectClass);
    updateTipoClienteSelectClass(); // <- aplica ao carregar
  }

  // Envio do formulário (AJAX opcional)
  const form = document.getElementById('form-editar-venda');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();

      // GARANTE QUE O SELECT DE PRODUTO NÃO ESTÁ DISABLED ANTES DE PEGAR OS DADOS
      const produtoSelect = document.getElementById('produto');
      if (produtoSelect && produtoSelect.disabled) {
        produtoSelect.disabled = false;
      }

      // Agora sim pega os dados do formulário
      const data = Object.fromEntries(new FormData(form).entries());
      // Inclui o valor do checkbox desconto_autorizado
      const descontoCheckbox = document.getElementById('desconto_autorizado');
      data.desconto_autorizado = descontoCheckbox && descontoCheckbox.checked ? true : false;
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        data.quem = user.nome_vendedor || user.username || '';
        // Se vendedor e status era "Refazer", força status para "Aguardando" no envio
        const statusSelect = document.getElementById('status-editar');
        if (
          user.tipo === 'vendedor' &&
          statusSelect &&
          statusSelect.getAttribute('data-original-status') === 'Refazer'
        ) {
          data.status = 'Aguardando';
        }
      } catch {}

      // NOVO: Mostra loading antes do fetch
      let loadingDiv = document.createElement('div');
      loadingDiv.id = 'loading-editar-venda';
      loadingDiv.style.position = 'fixed';
      loadingDiv.style.top = '0';
      loadingDiv.style.left = '0';
      loadingDiv.style.width = '100vw';
      loadingDiv.style.height = '100vh';
      loadingDiv.style.background = 'rgba(255,255,255,0.7)';
      loadingDiv.style.display = 'flex';
      loadingDiv.style.alignItems = 'center';
      loadingDiv.style.justifyContent = 'center';
      loadingDiv.style.zIndex = '9999';
      loadingDiv.innerHTML = '<div style="padding:30px 40px;background:#fff;border-radius:10px;box-shadow:0 2px 12px #bbb;font-size:1.2em;display:flex;align-items:center;gap:16px;"><span class="spinner" style="width:28px;height:28px;border:4px solid #2980b9;border-top:4px solid #eee;border-radius:50%;display:inline-block;animation:spin 1s linear infinite;"></span>Salvando venda...</div><style>@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>';
      document.body.appendChild(loadingDiv);

      fetch('/salvar_edicao_venda', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(resp => {
        // Remove loading
        const loading = document.getElementById('loading-editar-venda');
        if (loading) loading.remove();

        if (resp.success) {
          // Log de movimentação: Edição de venda detalhado
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          const now = new Date();
          // NOVO: inclui número da venda e status atual no log
          const numeroVenda = data.numero_da_venda || '';
          const statusAtual = data.status || '';
          fetch('/api/inserir_log', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                  data: now.toLocaleDateString('pt-BR'),
                  hora: now.toLocaleTimeString('pt-BR'),
                  modificacao: `Edição de venda - Nº: ${numeroVenda} | Status: ${statusAtual}`,
                  usuario: user.username || ''
              })
          });
          if (resp.success !== true) {alert(resp.success);}
          else {alert('Venda atualizada com sucesso!');}
          window.location.href = '/vendas';
        } else {
          alert('Erro ao atualizar: ' + (resp.erro || ''));
        }
      });
    });
  }

  // Preenchimento automático dos campos financeiros ao editar venda
  const produtosJsonDiv = document.getElementById("produtos-json");
  if (!produtosJsonDiv) return;
  const produtosDados = JSON.parse(produtosJsonDiv.dataset.produtos);

  // Personalizado edição
  const produtoSelect = document.getElementById('produto');
  const btnAddProduto = document.getElementById('btn-add-produto-editar');
  const listaProdutos = document.getElementById('lista-produtos-personalizados-editar');
  const hiddenProdutos = document.getElementById('produtos-personalizados-hidden-editar');
  const personalizadoArea = document.getElementById('personalizado-area-editar');
  let produtosPersonalizados = [];
  let selectTemp = null;
  let personalizadoBanco = false; // novo flag

  // Inicializa lista se já for personalizado do banco
  function inicializarPersonalizado() {
    const produtoStr = produtoSelect.value || '';
    if (produtoStr.startsWith('Personalizado:')) {
      personalizadoBanco = true;
      produtosPersonalizados = produtoStr.replace('Personalizado:', '').split(',').map(p => {
        const val = p.trim();
        return val ? { value: val, label: val } : null;
      }).filter(Boolean);
    } else {
      personalizadoBanco = false;
      produtosPersonalizados = [];
    }
  }
  inicializarPersonalizado();

  function renderListaProdutos() {
    // Se for personalizado do banco, não exibe lista nem botão
    if (personalizadoBanco) {
      listaProdutos.innerHTML = '';
      btnAddProduto.style.display = 'none';
      hiddenProdutos.value = '';
      return;
    }
    listaProdutos.innerHTML = '';
    produtosPersonalizados.forEach((prod, idx) => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.justifyContent = 'space-between';
      li.style.alignItems = 'center';
      li.style.padding = '6px 12px';
      li.style.borderBottom = '1px solid #eee';
      li.textContent = prod.label;
      if (!personalizadoBanco) {
        const btnRemove = document.createElement('button');
        btnRemove.textContent = '✖';
        btnRemove.type = 'button';
        btnRemove.title = 'Remover';
        btnRemove.style.background = 'none';
        btnRemove.style.border = 'none';
        btnRemove.style.color = '#e74c3c';
        btnRemove.style.cursor = 'pointer';
        btnRemove.style.fontSize = '16px';
        btnRemove.onclick = function () {
          produtosPersonalizados.splice(idx, 1);
          renderListaProdutos();
          atualizarCondicoesPersonalizadoEditar();
        };
        li.appendChild(btnRemove);
      }
      listaProdutos.appendChild(li);
    });
    hiddenProdutos.value = produtosPersonalizados.map(p => p.value).join(',');

    // Mostra ou esconde o botão "+" conforme o número de produtos e tipo
    if (produtosPersonalizados.length >= 3) {
      btnAddProduto.style.display = 'none';
    } else if (produtoSelect.value === 'Personalizado') {
      btnAddProduto.style.display = '';
    }
    // Atualiza condições se for personalizado editável
    if (produtoSelect.value === 'Personalizado' && !personalizadoBanco) {
      atualizarCondicoesPersonalizadoEditar();
    }
  }

  function atualizarCondicoesPersonalizadoEditar() {
    const condicaoSelect = document.getElementById('condicoes');
    const valorTabelaInput = document.getElementById('valor_tabela');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorRealInput = document.getElementById('valor_real');

    // Limpa as opções antes de adicionar novas (evita duplicidade)
    condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
    // Só habilita se tiver pelo menos 2 produtos
    condicaoSelect.disabled = produtosPersonalizados.length < 2;

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

    // --- NOVO: Atualiza o valor da tabela ao selecionar condição ---
    condicaoSelect.onchange = function () {
      const selectedOption = condicaoSelect.options[condicaoSelect.selectedIndex];
      const valor = selectedOption && selectedOption.dataset.valor ? selectedOption.dataset.valor : '';
      valorTabelaInput.value = valor;
      valorTabelaInput.readOnly = false; // <-- Permite edição para personalizado
    };

    // --- CORREÇÃO: Preenche valor_tabela se já houver condição selecionada ---
    if (condicaoSelect.selectedIndex > 0) {
      const selectedOption = condicaoSelect.options[condicaoSelect.selectedIndex];
      const valor = selectedOption && selectedOption.dataset.valor ? selectedOption.dataset.valor : '';
      valorTabelaInput.value = valor;
      valorTabelaInput.readOnly = false;
    } else {
      // Se só houver uma condição possível, seleciona automaticamente
      if (condicaoSelect.options.length === 2) {
        condicaoSelect.selectedIndex = 1;
        const selectedOption = condicaoSelect.options[1];
        const valor = selectedOption && selectedOption.dataset.valor ? selectedOption.dataset.valor : '';
        valorTabelaInput.value = valor;
        valorTabelaInput.readOnly = false;
      } else {
        valorTabelaInput.value = '';
        valorTabelaInput.readOnly = false;
      }
    }
    valorParcelaInput.value = '';
    valorRealInput.value = '';

    // --- NOVO: Bloqueia edição do valor_tabela para personalizado (força readOnly e tabindex -1) ---
    valorTabelaInput.readOnly = true;
    valorTabelaInput.tabIndex = -1;
    valorTabelaInput.addEventListener('keydown', function(e) { e.preventDefault(); });
    valorTabelaInput.addEventListener('paste', function(e) { e.preventDefault(); });
    valorTabelaInput.style.backgroundColor = '#f5f5f5';
    valorTabelaInput.style.pointerEvents = 'none';
  }

  produtoSelect.addEventListener('change', function () {
    inicializarPersonalizado();
    if (produtoSelect.value === 'Personalizado') {
      personalizadoArea.style.display = '';
      btnAddProduto.style.display = produtosPersonalizados.length < 3 ? '' : 'none';
      renderListaProdutos();
      // Limpa as opções antes de atualizar para evitar duplicidade
      document.getElementById('condicoes').innerHTML = '<option value="">Selecione uma condição</option>';
      atualizarCondicoesPersonalizadoEditar();
    } else if (produtoSelect.value.startsWith('Personalizado:')) {
      personalizadoArea.style.display = '';
      btnAddProduto.style.display = 'none';
      listaProdutos.innerHTML = '';
      hiddenProdutos.value = '';
      if (valoresPersonalizadoBanco) {
        const condicoesSelect = document.getElementById('condicoes');
        condicoesSelect.innerHTML = '';
        if (valoresPersonalizadoBanco.condicao) {
          const opt = document.createElement('option');
          opt.value = valoresPersonalizadoBanco.condicao;
          opt.textContent = valoresPersonalizadoBanco.condicao;
          condicoesSelect.appendChild(opt);
          condicoesSelect.value = valoresPersonalizadoBanco.condicao;
        }
        document.getElementById('valor_tabela').value = valoresPersonalizadoBanco.valorTabela;
        document.getElementById('valor_parcelas').value = valoresPersonalizadoBanco.valorParcelas;
        document.getElementById('valor_real').value = valoresPersonalizadoBanco.valorReal;
      }
      document.getElementById('valor_tabela').readOnly = true;
      document.getElementById('valor_real').readOnly = true;
    } else {
      personalizadoArea.style.display = 'none';
      btnAddProduto.style.display = 'none';
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
        produtosDados[produtoSelect.value].forEach(item => {
          const option = document.createElement('option');
          option.value = item.condicao;
          option.textContent = item.condicao;
          option.dataset.valor = item.valor;
          condicaoSelect.appendChild(option);
        });
      } else {
      }
      // Libera edição dos campos
      condicaoSelect.disabled = false;
      valorTabelaInput.readOnly = false;
      valorParcelaInput.readOnly = false;
      valorRealInput.readOnly = false;
    }
  });

  btnAddProduto.addEventListener('click', function () {
    if (personalizadoBanco) return; // não permite adicionar se for personalizado do banco
    if (selectTemp && document.body.contains(selectTemp)) {
      selectTemp.focus();
      return;
    }
    selectTemp = document.createElement('select');
    selectTemp.innerHTML = `<option value="">Selecione...</option>${
      Object.keys(produtosDados).map(prod => `<option value="${prod}">${prod}</option>`).join('')
    }`;
    selectTemp.style.marginRight = '8px';
    selectTemp.onchange = function () {
      const value = selectTemp.value;
      const label = selectTemp.options[selectTemp.selectedIndex]?.textContent.trim();
      if (!value /*|| produtosPersonalizados.some(p => p.value === value) */ || produtosPersonalizados.length >= 3) return;
      produtosPersonalizados.push({ value, label });
      renderListaProdutos();
      selectTemp.remove();
      selectTemp = null;
      atualizarCondicoesPersonalizadoEditar();
    };
    btnAddProduto.parentNode.insertBefore(selectTemp, btnAddProduto);
    selectTemp.focus();
  });

  // Salva valores originais do banco para o produto personalizado
  let valoresPersonalizadoBanco = null;
  function salvarValoresPersonalizadoBanco() {
    const produtoStr = produtoSelect.value || '';
    if (produtoStr.startsWith('Personalizado:')) {
      valoresPersonalizadoBanco = {
        condicao: document.getElementById('condicoes').value,
        valorTabela: document.getElementById('valor_tabela').value,
        valorParcelas: document.getElementById('valor_parcelas').value,
        valorReal: document.getElementById('valor_real').value
      };
      // Torna global para uso em outros scripts/templates
      window.valoresPersonalizadoBanco = valoresPersonalizadoBanco;
    }
  }
  salvarValoresPersonalizadoBanco();

  // Inicializa lista personalizada ao carregar
  if (produtoSelect.value === 'Personalizado' || produtoSelect.value.startsWith('Personalizado:')) {
    personalizadoArea.style.display = '';
    btnAddProduto.style.display = (!personalizadoBanco && produtosPersonalizados.length < 3) ? '' : 'none';
    renderListaProdutos();
    if (!personalizadoBanco) {
      atualizarCondicoesPersonalizadoEditar();
    } else {
      listaProdutos.innerHTML = '';
      hiddenProdutos.value = '';
      const condicoesSelect = document.getElementById('condicoes');
      condicoesSelect.innerHTML = '';
      if (valoresPersonalizadoBanco && valoresPersonalizadoBanco.condicao) {
        const opt = document.createElement('option');
        opt.value = valoresPersonalizadoBanco.condicao;
        opt.textContent = valoresPersonalizadoBanco.condicao;
        condicoesSelect.appendChild(opt);
        condicoesSelect.value = valoresPersonalizadoBanco.condicao;
      }
      document.getElementById('valor_tabela').readOnly = true;
      document.getElementById('valor_real').readOnly = true;
      salvarValoresPersonalizadoBanco();
    }
  }

  // BLOQUEIO DE CAMPOS PARA VENDEDOR E FATURAMENTO
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const tipo = user.tipo;
  const statusSelect = document.getElementById('status-editar');
  const btnSalvar = document.getElementById('btn-salvar-editar');
  const btnCancelar = document.querySelector('.cancelar');
  const btnCopiar = document.getElementById('btn-copiar-dados');
  const statusVenda = (statusSelect && statusSelect.value) ? statusSelect.value.toLowerCase() : '';

  // --- BLOQUEIO DO CAMPO TIPO DO CLIENTE PARA VENDEDOR ---
  const tipoClienteSelect = document.getElementById('tipo-cliente-editar');
  if (tipo === 'vendedor' && tipoClienteSelect) {
    tipoClienteSelect.disabled = true;
    tipoClienteSelect.style.backgroundColor = '#f5f5f5';
    tipoClienteSelect.style.pointerEvents = 'none';
  }

  // Salva status original para uso no submit
  if (statusSelect) {
    statusSelect.setAttribute('data-original-status', statusSelect.value);
  }

  // --- PERMISSÃO DE EDIÇÃO DO STATUS E SALVAR ---
  if (statusSelect && btnSalvar) {
    if (tipo === "vendedor") {
      statusSelect.disabled = true;
      // --- NOVO: Permite salvar se status for "Refazer" ---
      if (statusVenda === 'refazer') {
        btnSalvar.disabled = false;
        btnSalvar.style.backgroundColor = '';
        btnSalvar.style.cursor = '';
      } else {
        btnSalvar.disabled = true;
        btnSalvar.style.backgroundColor = '#7f8c8d';
        btnSalvar.style.cursor = 'not-allowed';
      }
    } else if (tipo === "faturamento") {
      // FATURAMENTO: agora pode editar tudo normalmente
      statusSelect.disabled = false;
      btnSalvar.disabled = false;
      Array.from(statusSelect.options).forEach(opt => {
        opt.disabled = false;
        opt.style.display = "";
      });
      // Remove qualquer bloqueio dos campos do formulário
      if (form) {
        Array.from(form.elements).forEach(function(el) {
          el.readOnly = false;
          el.disabled = false;
        });
      }
    } else if (tipo === "pos_vendas") {
      // Pós-vendas pode sempre editar status e salvar, mesmo se status for "Aprovada"
      statusSelect.disabled = false;
      btnSalvar.disabled = false;
      Array.from(statusSelect.options).forEach(opt => {
        opt.disabled = false;
        opt.style.display = "";
      });
    } else {
      // Para admin e outros: tudo liberado
      statusSelect.disabled = false;
      btnSalvar.disabled = false;
      Array.from(statusSelect.options).forEach(opt => {
        opt.disabled = false;
        opt.style.display = "";
      });
    }
  }

  // BLOQUEIO TOTAL PARA VENDEDOR SE STATUS FOR FATURADO, AGUARDANDO OU APROVADA
  if (
    tipo === 'vendedor' &&
    (statusVenda === 'faturado' || statusVenda === 'aguardando' || statusVenda === 'aprovada')
  ) {
    if (form) {
      Array.from(form.elements).forEach(function(el) {
        // Só libera o botão cancelar
        if (el.classList.contains('cancelar')) {
          el.disabled = false;
          el.style.backgroundColor = '';
          el.style.cursor = '';
        } else if (el.name !== 'numero_da_venda') {
          el.readOnly = true;
          el.disabled = true;
        }
      });
    }
    if (btnSalvar) {
      btnSalvar.disabled = true;
      btnSalvar.style.backgroundColor = '#7f8c8d';
      btnSalvar.style.cursor = 'not-allowed';
    }
    if (btnCancelar) {
      btnCancelar.disabled = false;
      btnCancelar.style.backgroundColor = '';
      btnCancelar.style.cursor = '';
    }
    // Não execute mais nada para vendedor/faturado/aguardando/aprovada
    return;
  }

  // FATURAMENTO: agora não bloqueia mais nada, pode editar tudo
  // ...NÃO BLOQUEAR MAIS NADA PARA FATURAMENTO...

  // POS_VENDAS: bloqueia todos os campos exceto alguns, libera salvar/cancelar/caminho_arquivos/obs_vendas, MAS libera geral para aguardando/aprovada
  else if (tipo === 'pos_vendas' && statusVenda !== 'aguardando' && statusVenda !== 'aprovada') {
    if (form) {
      Array.from(form.elements).forEach(function(el) {
        // NÃO bloqueie produto, status, caminho_arquivos, obs_vendas
        if (
          el.name !== 'numero_da_venda' &&
          el.name !== 'status' &&
          el.name !== 'produto' &&
          el.name !== 'caminho_arquivos' &&
          el.name !== 'obs_vendas' &&
          el.name !== 'status-editar'
        ) {
          el.readOnly = true;
          el.disabled = true;
        } else {
          el.readOnly = false;
          el.disabled = false;
        }
      });
      const produtoSelect = document.getElementById('produto');
      if (produtoSelect) {
        produtoSelect.style.pointerEvents = 'none';
        produtoSelect.style.backgroundColor = '#f5f5f5';
      }
    }
    if (btnCancelar) {
      btnCancelar.disabled = false;
      btnCancelar.style.backgroundColor = '';
      btnCancelar.style.cursor = '';
    }
    if (btnCopiar) {
      btnCopiar.disabled = false;
      btnCopiar.style.backgroundColor = '';
      btnCopiar.style.cursor = '';
      btnCopiar.style.display = '';
    }
  }
  // Se status == "Cancelada", bloqueia todos os campos e botão salvar para qualquer usuário
  else if (statusVenda === 'cancelada') {
    Array.from(form.elements).forEach(function(el) {
      if (el.name !== 'numero_da_venda') {
        el.readOnly = true;
        el.disabled = true;
      }
    });
    if (btnSalvar) {
      btnSalvar.disabled = true;
      btnSalvar.style.backgroundColor = '#7f8c8d';
      btnSalvar.style.cursor = 'not-allowed';
    }
  }
  // Se vendedor e status == "Aguardando", bloqueia todos os campos e botão salvar
  else if (tipo === 'vendedor' && statusVenda === 'aguardando') {
    Array.from(form.elements).forEach(function(el) {
      if (el.name !== 'numero_da_venda') {
        el.readOnly = true;
        el.disabled = true;
      }
    });
    if (btnSalvar) {
      btnSalvar.disabled = true;
      btnSalvar.style.backgroundColor = '#7f8c8d';
      btnSalvar.style.cursor = 'not-allowed';
    }
  }
  // Se vendedor e status == "Aprovada", bloqueia todos os campos e botão salvar (apenas consulta)
  else if (tipo === 'vendedor' && statusVenda === 'aprovada') {
    Array.from(form.elements).forEach(function(el) {
      if (el.name !== 'numero_da_venda') {
        el.readOnly = true;
        el.disabled = true;
      }
    });
    if (btnSalvar) {
      btnSalvar.disabled = true;
      btnSalvar.style.backgroundColor = '#7f8c8d';
      btnSalvar.style.cursor = 'not-allowed';
    }
  }
  // Se vendedor e status == "Refazer", libera tudo, mas ao salvar força status para "Aguardando"
  else if (tipo === 'vendedor' && statusVenda === 'refazer') {
    if (statusSelect) statusSelect.disabled = true;
    // O submit já trata o envio do status acima
  }
});

// filepath: c:\Users\deivid\Desktop\sistemaVendas\app\templates\editar_venda.html
document.addEventListener('DOMContentLoaded', function () {
  var user = JSON.parse(localStorage.getItem('user') || '{}');
  var tipo = user.tipo;
  var status = "{{ venda.status }}";
  var form = document.getElementById('form-editar-venda');
  var btnSalvar = document.getElementById('btn-salvar-editar');
  var statusSelect = document.getElementById('status-editar');

  // Vendedor não pode editar o status
  if (tipo === 'vendedor' && statusSelect) {
    statusSelect.disabled = true;
  }

  // Se vendedor e status == "Aguardando", bloqueia todos os campos e botão salvar
  if (tipo === 'vendedor' && status.toLowerCase() === 'aguardando') {
    Array.from(form.elements).forEach(function(el) {
      if (el.name !== 'numero_da_venda') {
        el.readOnly = true;
        el.disabled = true;
      }
    });
    if (btnSalvar) {
      btnSalvar.disabled = true;
      btnSalvar.style.backgroundColor = '#7f8c8d';
      btnSalvar.style.cursor = 'not-allowed';
    }
  }

  // Se vendedor e status == "Refazer", libera tudo, mas ao salvar força status para "Aguardando"
  if (tipo === 'vendedor' && status.toLowerCase() === 'refazer') {
    if (statusSelect) statusSelect.disabled = true;
    if (form) {
      form.addEventListener('submit', function(e) {
        var statusInput = document.getElementById('status-editar');
        if (statusInput) {
          statusInput.disabled = false;
          statusInput.value = 'Aguardando';
        }
      });
    }
  }

  // Botão copiar dados - para admin, pos_vendas e faturamento
  const btnCopiar = document.getElementById('btn-copiar-dados');
  let userTipo = '';
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    userTipo = user.tipo;
  } catch {}
  if (btnCopiar) {
    if (userTipo === 'admin' || userTipo === 'pos_vendas' || userTipo === 'faturamento') {
      btnCopiar.style.display = '';
      btnCopiar.disabled = false;
      // Garante a cor original do botão
      btnCopiar.style.backgroundColor = '#2980b9';
      btnCopiar.style.color = '#fff';
      btnCopiar.style.cursor = '';
      btnCopiar.addEventListener('click', function () {
        const form = document.getElementById('form-editar-venda');
        if (!form) return;
        const get = name => form.elements[name] ? form.elements[name].value : '';
        const endereco = {
          rua: get('endereco_rua'),
          bairro: get('endereco_bairro'),
          numero: get('endereco_numero'),
          cidade: get('endereco_cidade'),
          estado: get('endereco_estado')
        };
        // Sempre pega o vendedor atribuído da venda (injetado pelo template Jinja)
        const vendedorFinal = window.vendaVendedor || '';

        const [ano, mes, dia] = get('data_prestacao_inicial').split('-');
        const dataPrestacao = `${dia}/${mes}/${ano}`;

        const texto =
`------ Dados Pessoais ------
NOME/RAZÃO SOCIAL: ${get('nome').toUpperCase()}
CONTATO: ${get('nome_do_contato').toUpperCase()}
CPF ou CNPJ: ${get('cnpj_cpf')}
IE/RG: ${get('inscricao_estadual_identidade')}
E-MAIL: ${get('email').toLowerCase()}
TELEFONES: ${get('fones')}

------ Endereço ------
RUA: ${endereco.rua.toUpperCase()}
BAIRRO: ${endereco.bairro.toUpperCase()}
NÚMERO: ${endereco.numero.toUpperCase()}
CIDADE: ${endereco.cidade.toUpperCase()}
ESTADO: ${endereco.estado.toUpperCase()}
CEP: ${get('cep')}

------ Dados da Venda ------
PRODUTO: ${get('produto').toUpperCase()}
VALOR: ${get('valor_real')}
CONDIÇÕES: ${get('condicoes')} de ${get('valor_parcelas').toUpperCase()}
PRESTAÇÃO INICIAL: ${dataPrestacao}
TIPO DE ENVIO DE BOLETO: ${get('tipo_envio_boleto').toUpperCase()}
TIPO DE REMESSA: ${get('tipo_remessa').toUpperCase()}
VENDEDOR: ${vendedorFinal.toUpperCase()}

OBSERVAÇÕES: ${get('obs').toUpperCase()}
`;
        navigator.clipboard.writeText(texto).then(function () {
          btnCopiar.textContent = 'Copiado!';
          setTimeout(() => btnCopiar.textContent = 'Copiar dados', 1500);
        });
      });
    } else {
      btnCopiar.style.display = 'none';
    }
  }

  // --- NOVO: Lógica dinâmica para condições da venda (A/C | 1+1) ---
  const condicaoSelect = document.getElementById('condicoes');
  const condicoesVendaContainer = document.getElementById('condicoes-venda-container-editar');
  const condicoesVendaSelect = document.getElementById('condicoes-venda-select-editar');
  const campoValorVenda = document.getElementById('campo-valor-venda-editar');
  const valorVendaAvistaInput = document.getElementById('valor_venda_avista_editar');
  const campoEntrada = document.getElementById('campo-entrada-editar');
  const campoParcela = document.getElementById('campo-parcela-editar');
  const valorEntradaInput = document.getElementById('valor_entrada_editar');
  const valorParcelaInput = document.getElementById('valor_parcelas');
  const valorRealInput = document.getElementById('valor_real');

  // Função para atualizar exibição dos campos conforme condição
  function atualizarCamposCondicoesVendaEditar() {
    if (!condicaoSelect) return;
    const condicao = condicaoSelect.value;
    // Sempre mantém o campo-parcela visível, apenas desabilita/habilita o input conforme a lógica
    if (condicao === 'A/C | 1+1') {
      condicoesVendaContainer.style.display = '';
      campoValorVenda.style.display = condicoesVendaSelect.value === 'avista' ? '' : 'none';
      campoEntrada.style.display = condicoesVendaSelect.value === 'avista' ? 'none' : '';
      campoParcela.style.display = '';
      if (condicoesVendaSelect.value === 'avista') {
        if (valorParcelaInput) {
          valorParcelaInput.value = '0';
          valorParcelaInput.readOnly = true;
          valorParcelaInput.tabIndex = -1;
          valorParcelaInput.style.backgroundColor = '#f5f5f5';
          valorParcelaInput.style.pointerEvents = 'none';
        }
        if (valorEntradaInput) valorEntradaInput.value = '';
        if (valorVendaAvistaInput) valorVendaAvistaInput.readOnly = false;
      } else {
        if (valorParcelaInput) {
          valorParcelaInput.readOnly = false;
          valorParcelaInput.tabIndex = 0;
          valorParcelaInput.style.backgroundColor = '';
          valorParcelaInput.style.pointerEvents = '';
        }
        if (valorVendaAvistaInput) valorVendaAvistaInput.value = '';
        if (valorVendaAvistaInput) valorVendaAvistaInput.readOnly = true;
      }
    } else {
      condicoesVendaContainer.style.display = 'none';
      campoValorVenda.style.display = 'none';
      campoEntrada.style.display = '';
      campoParcela.style.display = '';
      if (valorVendaAvistaInput) valorVendaAvistaInput.value = '';
      if (valorVendaAvistaInput) valorVendaAvistaInput.readOnly = true;
      if (valorParcelaInput) {
        valorParcelaInput.readOnly = false;
        valorParcelaInput.tabIndex = 0;
        valorParcelaInput.style.backgroundColor = '';
        valorParcelaInput.style.pointerEvents = '';
      }
    }
    atualizarValorRealEditar();
  }

  // Função para atualizar valor real conforme campos
  function atualizarValorRealEditar() {
    const condicaoSelect = document.getElementById('condicoes');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorEntradaInput = document.getElementById('valor_entrada_editar');
    const valorRealInput = document.getElementById('valor_real');
    const condicoesVendaSelect = document.getElementById('condicoes-venda-select-editar');
    const valorVendaAvistaInput = document.getElementById('valor_venda_avista_editar');

    let valorEntrada = parseFloat((valorEntradaInput && valorEntradaInput.value) ? valorEntradaInput.value.replace(',', '.') : '0');
    let valorParcela = parseFloat((valorParcelaInput && valorParcelaInput.value) ? valorParcelaInput.value.replace(',', '.') : '0');
    let total = 0

    if (condicaoSelect && condicaoSelect.value === 'A/C | 1+1') {
      if (condicoesVendaSelect && condicoesVendaSelect.value === 'avista') {
        total = parseFloat((valorVendaAvistaInput && valorVendaAvistaInput.value) ? valorVendaAvistaInput.value.replace(',', '.') : '0');
      } else if (condicoesVendaSelect && condicoesVendaSelect.value === 'entrada_parcela') {
        const parcelas =  1;
        total = valorEntrada + (valorParcela * parcelas);
      }
    } else if (condicaoSelect) {
      const parcelas = extrairParcelas(condicaoSelect.value) || 1;
      total = valorEntrada + (valorParcela * parcelas);
    }

    valorRealInput.value = (total > 0 ? total.toFixed(2) : '');
  }

  // Eventos
  if (condicaoSelect) {
    condicaoSelect.addEventListener('change', function () {
      atualizarCamposCondicoesVendaEditar();
    });
  }
  if (condicoesVendaSelect) {
    condicoesVendaSelect.addEventListener('change', function () {
      atualizarCamposCondicoesVendaEditar();
    });
  }
  if (valorVendaAvistaInput) {
    valorVendaAvistaInput.addEventListener('input', atualizarValorRealEditar);
  }
  if (valorEntradaInput) {
    valorEntradaInput.addEventListener('input', atualizarValorRealEditar);
  }
  if (valorParcelaInput) {
    valorParcelaInput.addEventListener('input', atualizarValorRealEditar);
  }

  // Inicialização com valores do banco
  function inicializarCamposCondicoesVendaEditar() {
    // Se veio do banco como A/C | 1+1, mostra os campos extras
    if (condicaoSelect && condicaoSelect.value === 'A/C | 1+1') {
      condicoesVendaContainer.style.display = '';
      // Preenche o select de condições da venda
      if (window.condicoesVendaBanco) {
        condicoesVendaSelect.value = window.condicoesVendaBanco;
      }
      // Preenche valor avista e entrada se existirem
      if (window.valorVendaAvistaBanco && valorVendaAvistaInput) {
        valorVendaAvistaInput.value = window.valorVendaAvistaBanco;
      }
      if (window.valorEntradaBanco && valorEntradaInput) {
        valorEntradaInput.value = window.valorEntradaBanco;
      }
      atualizarCamposCondicoesVendaEditar();
    }
  }
  inicializarCamposCondicoesVendaEditar();

  // Função para extrair número de parcelas de uma condição
  function extrairParcelas(condicaoTexto) {
    if (!condicaoTexto) return null;
    const matchX = condicaoTexto.match(/(\d+)[xX]/);
    if (matchX) return parseInt(matchX[1]);
    const matchMais = condicaoTexto.match(/(\d+)\s*\+\s*(\d+)/);
    if (matchMais) return parseInt(matchMais[1]) + parseInt(matchMais[2]);
    return null;
  }

  // --- RESTAURAÇÃO E AJUSTE DO MIX DE FUNCIONALIDADES ---

  // Função para preencher campos ao selecionar produto (comum ou personalizado)
  function preencherCamposAoSelecionarProduto(limparCampos = true) {
    const produtoSelect = document.getElementById('produto');
    const condicaoSelect = document.getElementById('condicoes');
    const valorTabelaInput = document.getElementById('valor_tabela');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorRealInput = document.getElementById('valor_real');
    const produtosJsonDiv = document.getElementById("produtos-json");
    const produtosDados = JSON.parse(produtosJsonDiv.dataset.produtos);

    // Se for produto personalizado do banco (Personalizado:...)
    if (produtoSelect.value && produtoSelect.value.startsWith('Personalizado:')) {
      // Preenche campos com valores do banco (mantém edição bloqueada)
      if (window.valoresPersonalizadoBanco) {
        condicaoSelect.innerHTML = '';
        if (window.valoresPersonalizadoBanco.condicao) {
          const opt = document.createElement('option');
          opt.value = window.valoresPersonalizadoBanco.condicao;
          opt.textContent = window.valoresPersonalizadoBanco.condicao;
          condicaoSelect.appendChild(opt);
          condicaoSelect.value = window.valoresPersonalizadoBanco.condicao;
        }
        // --- GARANTE QUE O VALOR DA TABELA É PREENCHIDO SEMPRE ---
        valorTabelaInput.value = window.valoresPersonalizadoBanco.valorTabela || '';
        valorParcelaInput.value = window.valoresPersonalizadoBanco.valorParcelas || '';
        valorRealInput.value = window.valoresPersonalizadoBanco.valorReal || '';
      }
      valorTabelaInput.readOnly = true;
      valorRealInput.readOnly = true;
      return;
    }

    // Se for personalizado editável (Personalizado)
    if (produtoSelect.value === 'Personalizado') {
      // Não preenche nada, pois depende da seleção dos produtos personalizados
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      valorTabelaInput.value = '';
      valorParcelaInput.value = '';
      valorRealInput.value = '';
      valorTabelaInput.readOnly = true;
      valorRealInput.readOnly = true;
      return;
    }

    // Produto comum
    if (produtosDados[produtoSelect.value]) {
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      produtosDados[produtoSelect.value].forEach(item => {
        const option = document.createElement('option');
        option.value = item.condicao;
        option.textContent = item.condicao;
        option.dataset.valor = item.valor;
        condicaoSelect.appendChild(option);
      });
      condicaoSelect.disabled = false;
      valorTabelaInput.value = '';
      if (limparCampos) {
        valorParcelaInput.value = '';
        valorRealInput.value = '';
      }
      valorTabelaInput.readOnly = true;
      valorRealInput.readOnly = true;
    } else {
      condicaoSelect.innerHTML = '<option value="">Selecione uma condição</option>';
      valorTabelaInput.value = '';
      if (limparCampos) {
        valorParcelaInput.value = '';
        valorRealInput.value = '';
      }
      valorTabelaInput.readOnly = true;
      valorRealInput.readOnly = true;
    }
  }

  // Função para ocultar e limpar campos de Valor da venda e Condições da Venda
  function ocultarELimparCamposCondicoesVendaEditar() {
    const condicoesVendaContainer = document.getElementById('condicoes-venda-container-editar');
    const campoValorVenda = document.getElementById('campo-valor-venda-editar');
    const valorVendaAvistaInput = document.getElementById('valor_venda_avista_editar');
    const condicoesVendaSelect = document.getElementById('condicoes-venda-select-editar');
    const campoEntrada = document.getElementById('campo-entrada-editar');
    const campoParcela = document.getElementById('campo-parcela-editar');
    const valorEntradaInput = document.getElementById('valor_entrada_editar');
    const valorParcelaInput = document.getElementById('valor_parcelas');
    const valorRealInput = document.getElementById('valor_real');

    if (condicoesVendaContainer) condicoesVendaContainer.style.display = 'none';
    if (campoValorVenda) campoValorVenda.style.display = 'none';
    if (campoEntrada) campoEntrada.style.display = 'none';
    if (campoParcela) campoParcela.style.display = 'none';
    if (valorVendaAvistaInput) valorVendaAvistaInput.value = '';
    if (valorEntradaInput) valorEntradaInput.value = '';
    if (valorParcelaInput) valorParcelaInput.value = '';
    if (valorRealInput) valorRealInput.value = '';
    if (condicoesVendaSelect) condicoesVendaSelect.selectedIndex = 0;
  }

  // Evento ao trocar produto
  document.getElementById('produto').addEventListener('change', function () {
    ocultarELimparCamposCondicoesVendaEditar();
    preencherCamposAoSelecionarProduto(true); // limpa campos
    // ...demais lógicas já existentes, como renderListaProdutos, atualizarCondicoesPersonalizadoEditar etc...
  });

  // Evento ao selecionar condição (produto comum ou personalizado)
  document.getElementById('condicoes').addEventListener('change', function () {
    const produtoSelect = document.getElementById('produto');
    const condicaoSelect = document.getElementById('condicoes');
    const valorTabelaInput = document.getElementById('valor_tabela');
    // Produto personalizado do banco: não faz nada (já está preenchido)
    if (produtoSelect.value && produtoSelect.value.startsWith('Personalizado:')) return;
    // Produto personalizado editável: lógica já existente
    if (produtoSelect.value === 'Personalizado') {
      // ...lógica personalizada já existente...
      return;
    }
    // Produto comum: preenche valor da tabela
    const selectedOption = condicaoSelect.options[condicaoSelect.selectedIndex];
    const valor = selectedOption && selectedOption.dataset.valor ? selectedOption.dataset.valor : '';
    valorTabelaInput.value = valor;
  });

  // Evento ao digitar valor da parcela (sempre recalcula valor real)
  document.getElementById('valor_parcelas').addEventListener('input', function () {
  });

  // --- GARANTE QUE O BOTÃO SALVAR ESTÁ HABILITADO PARA POS_VENDAS ---
  document.addEventListener('DOMContentLoaded', function() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const tipo = user.tipo;
    const btnSalvar = document.getElementById('btn-salvar-editar');
    if (btnSalvar) {
      if (tipo === 'faturamento') {
        btnSalvar.disabled = false;
        btnSalvar.style.backgroundColor = '';
        btnSalvar.style.cursor = 'pointer';
      }
    }
  });

  // Padroniza a largura do select de condições ao carregar e ao atualizar opções
  function padronizarLarguraCondicoesSelect() {
    const condicaoSelect = document.getElementById('condicoes');
    if (condicaoSelect) {
      condicaoSelect.style.minWidth = '220px'; // ajuste conforme desejado
      condicaoSelect.style.width = 'auto';
      condicaoSelect.style.maxWidth = '100%';
    }
  }

  // Chame ao carregar a página
  document.addEventListener('DOMContentLoaded', function() {
    padronizarLarguraCondicoesSelect();
    // ...existing code...
  });


  // E sempre que trocar produto
  document.getElementById('produto').addEventListener('change', function () {
    // ...existing code...
    padronizarLarguraCondicoesSelect();
    // ...existing code...
  });

  // --- REGRA FINAL: Garante que o botão salvar está habilitado para FATURAMENTO ---
  if (tipo === 'faturamento' && btnSalvar) {
    btnSalvar.disabled = false;
    btnSalvar.style.backgroundColor = '';
    btnSalvar.style.cursor = 'pointer';
  }

  /**
 * Seleciona o produto e, após popular as condições, seleciona a condição do banco.
 * @param {string} produtoBanco
 * @param {string} condicaoBanco
 */
function selecionarProdutoECondicao(produtoBanco, condicaoBanco) {
  const produtoSelect = document.getElementById('produto');
  const condicaoSelect = document.getElementById('condicoes');
  const valorTabelaInput = document.getElementById('valor_tabela');
  // --- EXCEÇÃO PARA PERSONALIZADO: não altera valor_tabela, pois já está preenchido do banco ---
  if (
    produtoSelect &&
    (
      (typeof produtoBanco === 'string' && produtoBanco.startsWith('Personalizado:')) ||
      (produtoSelect.value && produtoSelect.value.startsWith('Personalizado:'))
    )
  ) {
    // Apenas seleciona o produto e condição, mas NÃO altera valor_tabela
    let produtoEncontrado = false;
    for (let i = 0; i < produtoSelect.options.length; i++) {
      if (produtoSelect.options[i].value === produtoBanco) {
        produtoSelect.selectedIndex = i;
        produtoEncontrado = true;
        break;
      }
    }
    if (!produtoEncontrado) return;

    // Dispara o evento change para popular as condições (mas não limpa campos)
    preencherCamposAoSelecionarProduto(false);

    // Aguarda o próximo tick para garantir que as condições foram populadas
    setTimeout(function () {
      for (let i = 0; i < condicaoSelect.options.length; i++) {
        if (condicaoSelect.options[i].value === condicaoBanco) {
          condicaoSelect.selectedIndex = i;
          condicaoSelect.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
      // NÃO altera valorTabelaInput.value aqui!
      // --- GARANTE QUE O VALOR DA TABELA ESTÁ CORRETO ---
      if (window.valoresPersonalizadoBanco && valorTabelaInput) {
        valorTabelaInput.value = window.valoresPersonalizadoBanco.valorTabela || '';
      }
    }, 0);
    return;
  }
  // ...existing code da função selecionarProdutoECondicao...
  // (mantém o comportamento padrão para produtos não personalizados)
  let produtoEncontrado = false;
  for (let i = 0; i < produtoSelect.options.length; i++) {
    if (produtoSelect.options[i].value === produtoBanco) {
      produtoSelect.selectedIndex = i;
      produtoEncontrado = true;
      break;
    }
  }
  if (!produtoEncontrado) return;

  preencherCamposAoSelecionarProduto(false);

  setTimeout(function () {
    for (let i = 0; i < condicaoSelect.options.length; i++) {
      if (condicaoSelect.options[i].value === condicaoBanco) {
        condicaoSelect.selectedIndex = i;
        condicaoSelect.dispatchEvent(new Event('change', { bubbles: true }));
        break;
      }
    }
  }, 0);
}

if (
  window.condicaoSelecionadaBanco &&
  document.getElementById('produto') &&
  !(document.getElementById('desconto_live') && document.getElementById('desconto_live').checked)
) {
  selecionarProdutoECondicao(
    document.getElementById('produto').value,
    window.condicaoSelecionadaBanco
  );
  // E aqui trava o campo:
  const valorTabelaInput = document.getElementById('valor_tabela');
  if (valorTabelaInput) {
    valorTabelaInput.readOnly = true;
  }
} else {
  // Se o desconto está marcado, libera:
  const valorTabelaInput = document.getElementById('valor_tabela');
  if (valorTabelaInput) {
    valorTabelaInput.readOnly = false;
  }
}
});
function escutarDesmarcarDescontoAutorizado() {
  // Garante que o checkbox já existe no DOM
  const descontoLive = document.getElementById('desconto_live');
  if (!descontoLive) {
    console.log('Checkbox desconto_live não encontrado');
    return;
  }
  let lastChecked = descontoLive.checked;
  descontoLive.addEventListener('change', function () {
    // Só chama ao DESMARCAR (quando checked vai de true para false)
    if (lastChecked && !descontoLive.checked) {
      console.log('Desmarcado desconto_live');
      if (window.condicaoSelecionadaBanco && document.getElementById('produto')) {
        selecionarProdutoECondicao(
          document.getElementById('produto').value,
          window.condicaoSelecionadaBanco

        );
      }
    }
    lastChecked = descontoLive.checked;
  });
}
  // Máscara para campos de valor: só números, ponto e vírgula
  function valorInputMask(input) {
      input.addEventListener('input', function () {
          let v = input.value.replace(/[^0-9.,]/g, '');
          const partes = v.split(/[.,]/);
          if (partes.length > 2) {
              v = partes[0] + '.' + partes.slice(1).join('');
          }
          input.value = v;
      });
      input.addEventListener('keypress', function (e) {
          if (!/[0-9.,]/.test(e.key)) {
              e.preventDefault();
          }
      });
      input.addEventListener('paste', function (e) {
          const pasted = (e.clipboardData || window.clipboardData).getData('text');
          if (/[^0-9.,]/.test(pasted)) {
              e.preventDefault();
          }
      });
  }
  const valorParcelaInput = document.getElementById('valor_parcelas');
  if (valorParcelaInput) valorInputMask(valorParcelaInput);

  const valorEntradaInput = document.getElementById('valor_entrada_editar');
  if (valorEntradaInput) valorInputMask(valorEntradaInput);

document.addEventListener('DOMContentLoaded', function() {
  // Busca e preenche endereço ao sair do campo CEP
  const cepInput = document.querySelector('input[name="cep"]');
  if (cepInput) {
    cepInput.addEventListener('blur', function() {
      const cep = cepInput.value.replace(/\D/g, '');
      if (cep.length !== 8) return;
      // Limpa os campos antes de buscar
      const rua = document.querySelector('input[name="endereco_rua"]');
      const bairro = document.querySelector('input[name="endereco_bairro"]');
      const cidade = document.querySelector('input[name="endereco_cidade"]');
      const estado = document.querySelector('input[name="endereco_estado"]');
      if (rua) rua.value = '';
      if (bairro) bairro.value = '';
      if (cidade) cidade.value = '';
      if (estado) estado.value = '';
      fetch(`https://viacep.com.br/ws/${cep}/json/`)
        .then(r => r.json())
        .then(data => {
          if (data.erro) return;
          if (rua) rua.value = data.logradouro || '';
          if (bairro) bairro.value = data.bairro || '';
          if (cidade) cidade.value = data.localidade || '';
          if (estado) estado.value = data.uf || '';
        });
    });
  }
});