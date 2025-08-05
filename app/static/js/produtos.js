document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.form-produto');
  let produtoSelecionadoCodigo = null;

  function preencherFormulario(produto) {
    form.querySelector('[name="codigo"]').value = produto.codigo || '';
    form.querySelector('[name="nome"]').value = produto.nome || '';
    if (produto.formas_pagamento && Array.isArray(produto.formas_pagamento)) {
      produto.formas_pagamento.forEach((fp, idx) => {
        const i = idx + 1;
        if (i > 13) return;
        form.querySelector(`[name="valor_total_${i}"]`).value = fp.valor_total || '';
        form.querySelector(`[name="parcelas_${i}"]`).value = fp.parcelas || '';
        form.querySelector(`[name="valor_parcela_${i}"]`).value = fp.valor_parcela || '';
      });
      // Limpa campos extras se o produto tiver menos de 13 formas
      for (let i = produto.formas_pagamento.length + 1; i <= 12; i++) {
        form.querySelector(`[name="valor_total_${i}"]`).value = '';
        form.querySelector(`[name="parcelas_${i}"]`).value = '';
        form.querySelector(`[name="valor_parcela_${i}"]`).value = '';
      }
    }
  }

  function alternarBotoesEdicao(modoEdicao) {
    form.querySelector('.btn-cadastrar').style.display = modoEdicao ? 'none' : '';
    form.querySelector('.btn-cancelar').style.display = modoEdicao ? '' : 'none';
    form.querySelector('.btn-salvar').style.display = modoEdicao ? '' : 'none';
  }

  function mostrarBotaoEditar(mostrar) {
    let btnEditar = document.getElementById('btn-editar-produto');
    if (!btnEditar) {
      btnEditar = document.createElement('button');
      btnEditar.id = 'btn-editar-produto';
      btnEditar.type = 'button';
      btnEditar.textContent = 'Editar';
      btnEditar.className = 'btn-editar-venda';
      btnEditar.style.marginTop = '10px';
      btnEditar.style.width = '150px';
      btnEditar.style.display = 'none';
      form.insertAdjacentElement('afterend', btnEditar);

      btnEditar.addEventListener('click', function () {
        if (!produtoSelecionadoCodigo) return;
        fetch(`/api/produto_detalhe/${encodeURIComponent(produtoSelecionadoCodigo)}`)
          .then(r => r.json())
          .then(produto => {
            preencherFormulario(produto);
            alternarBotoesEdicao(true);
            form.dataset.editando = produto.codigo;
          });
      });
    }
    btnEditar.style.display = mostrar ? '' : 'none';
  }

  function renderTabelaProdutos() {
    fetch('/api/lista_produtos')
      .then(r => r.json())
      .then(produtos => {
        const tbody = document.getElementById('produtos-tbody');
        tbody.innerHTML = '';
        produtos.forEach(produto => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${produto.codigo}</td><td>${produto.nome}</td>`;
          tr.style.cursor = 'pointer';
          tr.addEventListener('click', function () {
            document.querySelectorAll('#produtos-tbody tr').forEach(el => el.classList.remove('selecionada'));
            tr.classList.add('selecionada');
            produtoSelecionadoCodigo = produto.codigo;
            mostrarBotaoEditar(true);
          });
          tbody.appendChild(tr);
        });
        mostrarBotaoEditar(false);
        produtoSelecionadoCodigo = null;
      });
  }

  // Botão Cancelar
  form.querySelector('.btn-cancelar').addEventListener('click', function () {
    form.reset();
    alternarBotoesEdicao(false);
    produtoSelecionadoCodigo = null;
    delete form.dataset.editando;
    document.querySelectorAll('#produtos-tbody tr').forEach(el => el.classList.remove('selecionada'));
    mostrarBotaoEditar(false);
  });

  // Botão Salvar
  form.querySelector('.btn-salvar').addEventListener('click', function (e) {
    e.preventDefault();
    const codigoOriginal = form.dataset.editando;
    if (!codigoOriginal) return;

    const data = {
      codigo: form.querySelector('[name="codigo"]').value,
      nome: form.querySelector('[name="nome"]').value,
      formas_pagamento: []
    };
    for (let i = 1; i <= 12; i++) {
      const valor_total = form.querySelector(`[name="valor_total_${i}"]`).value;
      const parcelas = form.querySelector(`[name="parcelas_${i}"]`).value;
      const valor_parcela = form.querySelector(`[name="valor_parcela_${i}"]`).value;
      if (valor_total && parcelas && valor_parcela) {
        // Validação do campo Parcelas
        if (i === 1) {
          if (parcelas !== '1+1') {
            alert('Na linha A/C, o campo Parcelas deve ser exatamente "1+1".');
            return;
          }
        } else {
          if (!/^\d+x$/.test(parcelas)) {
            alert('O campo Parcelas deve ser preenchido com um número seguido de "x" minúsculo (ex: 3x) nas linhas B/C.');
            return;
          }
        }
        data.formas_pagamento.push({
          tipo: i === 1 ? 'A/C' : 'B/C',
          valor_total,
          parcelas,
          valor_parcela
        });
      }
    }

    fetch(`/api/produto_update/${encodeURIComponent(codigoOriginal)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Log de movimentação: Edição de produto
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const now = new Date();
        fetch('/api/inserir_log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                data: now.toLocaleDateString('pt-BR'),
                hora: now.toLocaleTimeString('pt-BR'),
                modificacao: 'Edição de produto: ' + data.codigo,
                usuario: user.username || ''
            })
        });

        alert('Produto atualizado!');
        form.reset();
        alternarBotoesEdicao(false);
        delete form.dataset.editando;
        renderTabelaProdutos();
      } else {
        alert(resp.erro || 'Erro ao atualizar!');
      }
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const payload = {
      codigo: form.querySelector('[name="codigo"]').value,
      nome: form.querySelector('[name="nome"]').value,
      formas_pagamento: []
    };
    for (let i = 1; i <= 12; i++) {
      const valor_total = form.querySelector(`[name="valor_total_${i}"]`).value;
      const parcelas = form.querySelector(`[name="parcelas_${i}"]`).value;
      const valor_parcela = form.querySelector(`[name="valor_parcela_${i}"]`).value;
      if (valor_total && parcelas && valor_parcela) {
        // Validação do campo Parcelas
        if (i === 1) {
          if (parcelas !== '1+1') {
            alert('Na linha A/C, o campo Parcelas deve ser exatamente "1+1".');
            return;
          }
        } else {
          if (!/^\d+x$/.test(parcelas)) {
            alert('O campo Parcelas deve ser preenchido com um número seguido de "x" minúsculo (ex: 3x) nas linhas B/C.');
            return;
          }
        }
        payload.formas_pagamento.push({
          tipo: i === 1 ? 'A/C' : 'B/C',
          valor_total,
          parcelas,
          valor_parcela
        });
      }
    }

    fetch('/produtos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Log de movimentação: Cadastro de produto
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const now = new Date();
        fetch('/api/inserir_log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                data: now.toLocaleDateString('pt-BR'),
                hora: now.toLocaleTimeString('pt-BR'),
                modificacao: 'Cadastro de produto: ' + payload.codigo,
                usuario: user.username || ''
            })
        });

        alert('Produto cadastrado com sucesso!');
        form.reset(); // Limpa os campos do formulário
        alternarBotoesEdicao(false);
        renderTabelaProdutos(); // Atualiza a tabela de produtos
      } else {
        alert(resp.erro || 'Erro ao cadastrar produto!');
      }
    });
  });

  // Inicializa
  renderTabelaProdutos();
  alternarBotoesEdicao(false);
});