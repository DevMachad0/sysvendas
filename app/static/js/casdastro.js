document.addEventListener('DOMContentLoaded', function () {
    const tipoSelect = document.getElementById('tipo');
    const meioForm = document.querySelector('.container-meio-form');

    function toggleMeioForm() {
        if (tipoSelect.value === 'vendedor') {
            meioForm.style.display = 'grid';
        } else {
            meioForm.style.display = 'none';
        }
    }

    // Inicializa o estado ao carregar
    toggleMeioForm();

    // Atualiza ao mudar o select
    tipoSelect.addEventListener('change', toggleMeioForm);

    // Função para botão cancelar
    const btnCancelar = document.querySelector('.btn-cancelar');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function (e) {
            e.preventDefault();
            window.location.href = btnCancelar.getAttribute('href') || '/';
        });
    }

    // Adicione este bloco se houver um formulário de cadastro com id="form-cadastro-usuario"
    const formCadastro = document.getElementById('form-cadastro-usuario');
    if (formCadastro) {
        formCadastro.addEventListener('submit', function(e) {
            // Aguarda o submit normal, depois do backend responder com sucesso, envie o log:
            setTimeout(function() {
                // Tenta pegar o usuário do localStorage (quem está logado)
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                const now = new Date();
                // Pega o username do novo usuário do campo do formulário
                const usernameNovo = formCadastro.querySelector('[name="username"]')?.value || '';
                fetch('/api/inserir_log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        data: now.toLocaleDateString('pt-BR'),
                        hora: now.toLocaleTimeString('pt-BR'),
                        modificacao: 'Cadastro de usuário: ' + usernameNovo,
                        usuario: user.username || ''
                    })
                });
            }, 500); // Pequeno delay para garantir que o backend já processou
        });
    }
});
document.addEventListener('DOMContentLoaded', function () {
  // Pós-vendas dinâmica
  const select = document.getElementById('pos-vendas-select');
  const btnAdd = document.getElementById('btn-add-pos-vendas');
  const lista = document.getElementById('lista-pos-vendas');
  const hidden = document.getElementById('pos_vendas-hidden');
  let selecionados = [];

  function renderLista() {
    lista.innerHTML = '';
    selecionados.forEach((pv, idx) => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.gap = '6px';
      li.style.marginBottom = '2px';
      li.textContent = pv.label;
      const btnRemove = document.createElement('button');
      btnRemove.textContent = '✖';
      btnRemove.type = 'button';
      btnRemove.style.background = 'none';
      btnRemove.style.border = 'none';
      btnRemove.style.color = '#e74c3c';
      btnRemove.style.cursor = 'pointer';
      btnRemove.style.fontSize = '16px';
      btnRemove.title = 'Remover';
      btnRemove.onclick = function () {
        selecionados.splice(idx, 1);
        renderLista();
      };
      li.appendChild(btnRemove);
      lista.appendChild(li);
    });
    hidden.value = selecionados.map(pv => pv.value).join(',');
  }

  btnAdd.addEventListener('click', function () {
    const value = select.value;
    const label = select.options[select.selectedIndex]?.textContent.trim();
    if (!value || selecionados.some(pv => pv.value === value)) return;
    selecionados.push({ value, label });
    renderLista();
    select.value = '';
  });

  // Permite remover com tecla Delete ao focar na lista
  lista.addEventListener('keydown', function(e) {
    if (e.key === 'Delete' && document.activeElement.tagName === 'LI') {
      const idx = Array.from(lista.children).indexOf(document.activeElement);
      if (idx >= 0) {
        selecionados.splice(idx, 1);
        renderLista();
      }
    }
  });

  // Inicializa lista vazia
  renderLista();
});