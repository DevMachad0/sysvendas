// Paginação em JS
  document.addEventListener('DOMContentLoaded', function() {
    const linhas = Array.from(document.querySelectorAll('#tabela-vendas-body tr'));
    const linhasPorPagina = 8;
    let paginaAtual = 1;
    const totalPaginas = Math.ceil(linhas.length / linhasPorPagina);
    const paginacaoDiv = document.getElementById('paginacao-vendas');

    function renderTabela() {
      linhas.forEach((linha, idx) => {
        linha.style.display = (
          idx >= (paginaAtual-1)*linhasPorPagina && idx < paginaAtual*linhasPorPagina
        ) ? '' : 'none';
      });

      // Preencher linhas vazias para manter 5 linhas
      let tbody = document.getElementById('tabela-vendas-body');
      // Removes linhas vazias antigas
      Array.from(tbody.querySelectorAll('tr.linha-vazia')).forEach(tr => tr.remove());
      let linhasVisiveis = linhas.filter((_, idx) =>
        idx >= (paginaAtual-1)*linhasPorPagina && idx < paginaAtual*linhasPorPagina
      ).length;
      for (let i = linhasVisiveis; i < linhasPorPagina; i++) {
        let tr = document.createElement('tr');
        tr.className = 'linha-vazia';
        tr.innerHTML = '<td colspan="9" style="visibility:hidden;">&nbsp;</td>';
        tbody.appendChild(tr);
      }
    }

    function renderPaginacao() {
      paginacaoDiv.innerHTML = '';
      // Botão anterior
      let btnAnt = document.createElement('button');
      btnAnt.innerHTML = '&laquo;';
      btnAnt.disabled = paginaAtual === 1;
      btnAnt.onclick = () => { paginaAtual--; atualizar(); };
      paginacaoDiv.appendChild(btnAnt);

      // Lógica de paginação compacta
      // Exemplo: (1) ... (10)(11)(12) ... (26)
      if (totalPaginas <= 5) {
        // Poucas páginas: mostra todas
        for (let p = 1; p <= totalPaginas; p++) {
          let btn = document.createElement('button');
          btn.textContent = p;
          if (p === paginaAtual) btn.className = 'ativo';
          btn.onclick = () => { paginaAtual = p; atualizar(); };
          paginacaoDiv.appendChild(btn);
        }
      } else {
        // Sempre mostra o primeiro botão
        let btnPrimeiro = document.createElement('button');
        btnPrimeiro.textContent = 1;
        if (paginaAtual === 1) btnPrimeiro.className = 'ativo';
        btnPrimeiro.onclick = () => { paginaAtual = 1; atualizar(); };
        paginacaoDiv.appendChild(btnPrimeiro);

        // Reticências após o primeiro, se necessário
        if (paginaAtual > 3) {
          let span = document.createElement('span');
          span.textContent = '...';
          span.style.margin = '0 4px';
          paginacaoDiv.appendChild(span);
        }

        // Botões centrais dinâmicos
        let start = Math.max(2, paginaAtual - 1);
        let end = Math.min(totalPaginas - 1, paginaAtual + 1);
        if (paginaAtual <= 2) {
          end = 4;
        }
        if (paginaAtual >= totalPaginas - 1) {
          start = totalPaginas - 3;
        }
        for (let p = start; p <= end; p++) {
          if (p <= 1 || p >= totalPaginas) continue;
          let btn = document.createElement('button');
          btn.textContent = p;
          if (p === paginaAtual) btn.className = 'ativo';
          btn.onclick = () => { paginaAtual = p; atualizar(); };
          paginacaoDiv.appendChild(btn);
        }

        // Reticências antes do último, se necessário
        if (paginaAtual < totalPaginas - 2) {
          let span = document.createElement('span');
          span.textContent = '...';
          span.style.margin = '0 4px';
          paginacaoDiv.appendChild(span);
        }

        // Sempre mostra o último botão
        let btnUltimo = document.createElement('button');
        btnUltimo.textContent = totalPaginas;
        if (paginaAtual === totalPaginas) btnUltimo.className = 'ativo';
        btnUltimo.onclick = () => { paginaAtual = totalPaginas; atualizar(); };
        paginacaoDiv.appendChild(btnUltimo);
      }

      // Botão próximo
      let btnProx = document.createElement('button');
      btnProx.innerHTML = '&raquo;';
      btnProx.disabled = paginaAtual === totalPaginas;
      btnProx.onclick = () => { paginaAtual++; atualizar(); };
      paginacaoDiv.appendChild(btnProx);
    }

    function atualizar() {
      renderTabela();
      renderPaginacao();
    }

    atualizar();
  });

  // Seleção unitária de venda
  document.addEventListener('DOMContentLoaded', function() {
    let vendaSelecionadaNumero = null;
    const tabelaBody = document.getElementById('tabela-vendas-body');
    const btnEditar = document.querySelector('.btn-editar-venda');

    function atualizarSelecao() {
      Array.from(tabelaBody.querySelectorAll('tr')).forEach(tr => {
        if (tr.dataset.numeroVenda === vendaSelecionadaNumero) {
          tr.classList.add('selecionada');
        } else {
          tr.classList.remove('selecionada');
        }
      });
      if (btnEditar) {
        btnEditar.disabled = !vendaSelecionadaNumero;
        btnEditar.style.backgroundColor = vendaSelecionadaNumero ? '#2980f2' : '#7f8c8d';
        btnEditar.style.cursor = vendaSelecionadaNumero ? 'pointer' : 'not-allowed';
      }
    }

    Array.from(tabelaBody.querySelectorAll('tr')).forEach(tr => {
      const numeroVenda = tr.dataset.numeroVenda;
      tr.addEventListener('click', function() {
        if (vendaSelecionadaNumero === numeroVenda) {
          vendaSelecionadaNumero = null;
        } else {
          vendaSelecionadaNumero = numeroVenda;
        }
        atualizarSelecao();
      });
    });

    if (btnEditar) {
      btnEditar.disabled = true;
      btnEditar.style.backgroundColor = '#7f8c8d';
      btnEditar.style.cursor = 'not-allowed';
      btnEditar.addEventListener('click', function() {
        if (vendaSelecionadaNumero) {
          fetch('/editar_venda', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_da_venda: vendaSelecionadaNumero })
          })
          .then(r => r.json())
          .then(data => {
            if (data.success) {
              window.location.href = '/editar_venda';
            } else {
              alert('Venda não encontrada!');
            }
          });
        }
      });
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    // Controle do botão Reabrir: só vendedor ou admin pode reabrir venda cancelada
    var btnReabrir = document.getElementById('btn-reabrir-venda');
    var tabela = document.getElementById('tabela-vendas-body');
    var btnEditar = document.getElementById('btn-editar-venda');
    let vendaSelecionada = null;
    var user = JSON.parse(localStorage.getItem('user') || '{}');

    if (btnReabrir) {
      btnReabrir.style.display = 'none'; // sempre inicia oculto
      btnReabrir.disabled = true;
      btnReabrir.style.backgroundColor = '#7f8c8d';
      btnReabrir.style.cursor = 'not-allowed';
      btnReabrir.onclick = function(e) { e.preventDefault(); }; // bloqueia por padrão
    }

    if (tabela && btnEditar && btnReabrir) {
      tabela.addEventListener('click', function (e) {
        let tr = e.target.closest('tr[data-numero-venda]');
        if (!tr) return;
        Array.from(tabela.querySelectorAll('tr')).forEach(row => row.classList.remove('selecionada'));
        tr.classList.add('selecionada');
        vendaSelecionada = {
          numero_da_venda: tr.getAttribute('data-numero-venda'),
          status: tr.getAttribute('data-status')
        };
        // Só mostra o botão reabrir se for vendedor OU admin e status cancelada
        if (
          vendaSelecionada.status === 'cancelada' &&
          (user.tipo === 'vendedor' || user.tipo === 'admin')
        ) {
          btnEditar.disabled = true;
          btnEditar.style.display = 'none';
          btnReabrir.disabled = false;
          btnReabrir.style.display = '';
          btnReabrir.style.backgroundColor = '#2980f2';
          btnReabrir.style.cursor = 'pointer';
          btnReabrir.onclick = function () {
            if (!vendaSelecionada || btnReabrir.disabled) return;
            fetch('/editar_venda', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ numero_da_venda: vendaSelecionada.numero_da_venda })
            })
            .then(r => r.json())
            .then(data => {
              if (data.success) {
                fetch('/editar_venda')
                  .then(resp => resp.text())
                  .then(html => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = html;
                    const venda = {};
                    tempDiv.querySelectorAll('input, select, textarea').forEach(el => {
                      if (el.name) {
                        if (el.type === 'checkbox' || el.type === 'radio') {
                          venda[el.name] = el.checked;
                        } else {
                          venda[el.name] = el.value;
                        }
                      }
                    });
                    localStorage.setItem('venda_reabrir', JSON.stringify(venda));
                    window.location.href = '/cadastrar_vendas';
                  });
              } else {
                alert('Venda não encontrada!');
              }
            });
          };
        } else {
          btnEditar.disabled = false;
          btnEditar.style.display = '';
          btnReabrir.disabled = true;
          btnReabrir.style.display = 'none';
          btnReabrir.style.backgroundColor = '#7f8c8d';
          btnReabrir.style.cursor = 'not-allowed';
          btnReabrir.onclick = function(e) { e.preventDefault(); };
        }
      });
    }

    // Botão Nova venda só para vendedor e admin
    var btnNovaVenda = document.getElementById('btn-nova-venda');
    var user = JSON.parse(localStorage.getItem('user') || '{}');
    if (btnNovaVenda && !(user.tipo === 'vendedor' || user.tipo === 'admin')) {
      btnNovaVenda.style.backgroundColor = '#7f8c8d';
      btnNovaVenda.style.color = '#eee';
      btnNovaVenda.style.cursor = 'not-allowed';
      btnNovaVenda.onclick = function(e) { e.preventDefault(); };
      btnNovaVenda.setAttribute('tabindex', '-1');
      btnNovaVenda.classList.add('disabled');
    }
  });

  document.addEventListener('DOMContentLoaded', function() {
    var filtroStatus = document.getElementById('filtro-status');
    if (filtroStatus) {
      filtroStatus.addEventListener('change', function() {
        this.form.submit();
      });
    }
  });

  document.addEventListener('DOMContentLoaded', function() {
    // Evento para o botão Fim do expediente
    const btnFimExpediente = document.querySelector('.btn-fim-expediente');
    if (btnFimExpediente) {
      btnFimExpediente.addEventListener('click', function() {
        if (!confirm('Deseja registrar o fim do expediente?')) return;
        fetch('/api/fim_expediente', {
          method: 'POST'
        })
        .then(r => r.json())
        .then(resp => {
          if (resp.success) {
            alert('Fim do expediente registrado!');
          } else {
            alert('Erro ao registrar fim do expediente: ' + (resp.msg || ''));
          }
        })
        .catch(() => alert('Erro ao registrar fim do expediente.'));
      });
    }
  });
