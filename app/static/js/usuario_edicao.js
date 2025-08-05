// Exemplo: adicionar lógica de confirmação ao salvar ou cancelar
document.addEventListener('DOMContentLoaded', function () {
  const btnCancelar = document.querySelector('.botoes-edicao .cancelar');
  if (btnCancelar) {
    btnCancelar.addEventListener('click', function () {
      window.location.href = "/usuarios";
    });
  }

  // Clique na foto para abrir o input de arquivo
  const fotoDiv = document.getElementById('foto-usuario-edicao');
  const fotoInput = document.getElementById('input-foto');
  if (fotoDiv && fotoInput) {
    fotoDiv.addEventListener('click', function () {
      fotoInput.click();
    });
  }

  // Preview da foto ao selecionar arquivo
  if (fotoInput) {
    fotoInput.addEventListener('change', function () {
      const file = fotoInput.files && fotoInput.files[0];
      const fotoDiv = document.getElementById('foto-usuario-edicao');
      let img = document.getElementById('img-foto-usuario-edicao');
      if (file) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          // Remove tudo do fotoDiv e coloca a imagem nova
          fotoDiv.innerHTML = '';
          img = document.createElement('img');
          img.id = 'img-foto-usuario-edicao';
          img.style.width = '100%';
          img.style.height = '100%';
          img.style.borderRadius = '50%';
          img.src = evt.target.result;
          fotoDiv.appendChild(img);
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Envio do formulário de edição via AJAX
  const form = document.getElementById('form-edicao-usuario');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      const fotoInput = document.getElementById('input-foto');
      // Ajuste: pega o valor do campo hidden de pós-vendas (caso exista)
      let posVendasValue = '';
      const posVendasHidden = document.getElementById('pos_vendas-edicao-hidden');
      if (posVendasHidden) {
        posVendasValue = posVendasHidden.value;
      } else {
        // fallback para campo antigo
        const posVendasInput = document.getElementById('input-pos-vendas');
        if (posVendasInput) posVendasValue = posVendasInput.value;
      }

      const data = {
        nome: document.getElementById('input-nome').value,
        email: document.getElementById('input-email').value,
        contato: document.getElementById('input-contato').value,
        pos_vendas: posVendasValue,
        username: document.getElementById('input-username').value,
        senha: document.getElementById('input-senha').value,
        tipo: document.getElementById('input-tipo').value,
        status: document.getElementById('input-status').value,
        meta_mes: document.getElementById('input-meta-mes').value
      };

      // Se o usuário selecionou uma nova foto, converte para base64
      if (fotoInput && fotoInput.files && fotoInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(evt) {
          data.foto = evt.target.result.split(',')[1]; // só base64 puro
          enviarAtualizacao(data);
        };
        reader.readAsDataURL(fotoInput.files[0]);
      } else {
        enviarAtualizacao(data);
      }

      function enviarAtualizacao(data) {
        fetch('/atualizar_usuario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        })
        .then(r => r.json())
        .then(resp => {
          if (resp.success) {
            // Log de movimentação: Edição de usuário
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const now = new Date();
            fetch('/api/inserir_log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    data: now.toLocaleDateString('pt-BR'),
                    hora: now.toLocaleTimeString('pt-BR'),
                    modificacao: 'Edição de usuário: ' + data.username,
                    usuario: user.username || ''
                })
            });

            alert('Usuário atualizado com sucesso!');
            window.location.href = '/usuarios';
          } else {
            alert('Erro ao atualizar: ' + (resp.erro || ''));
          }
        })
        .catch(() => alert('Erro ao atualizar usuário!'));
      }
    });
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const tipoSelect = document.getElementById('input-tipo');
  const campoPosvendas = document.getElementById('campo-posvendas-edicao');
  const campoMeta = document.getElementById('campo-meta-edicao');
  function toggleCamposVendedor() {
    const isVendedor = tipoSelect.value === 'vendedor';
    campoPosvendas.style.display = isVendedor ? '' : 'none';
    campoMeta.style.display = isVendedor ? '' : 'none';
  }
  tipoSelect.addEventListener('change', toggleCamposVendedor);
  toggleCamposVendedor();

  const select = document.getElementById('pos-vendas-edicao-select');
  const btnAdd = document.getElementById('btn-add-pos-vendas-edicao');
  const lista = document.getElementById('lista-pos-vendas-edicao');
  const hidden = document.getElementById('pos_vendas-edicao-hidden');

  // ✅ Inicializa os selecionados a partir do backend
  const posVendasRaw = document.getElementById('pos_vendas-json').dataset.posvendas;
  const selecionados = posVendasRaw
    .split(',')
    .map(pv => pv.trim())
    .filter(pv => pv !== '')
    .map(pv => ({ value: pv, label: pv }));

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

  renderLista();

  // Se NÃO for admin, desabilita todos os campos do formulário e oculta botão salvar
  var user = JSON.parse(localStorage.getItem('user') || '{}');
  var isAdmin = user.tipo === 'admin';

  var form = document.getElementById('form-edicao-usuario');
  var btnSalvar = document.querySelector('.botoes-edicao .salvar');
  var btnCancelar = document.querySelector('.botoes-edicao .cancelar');
  if (!isAdmin) {
    if (form) {
      Array.from(form.elements).forEach(function(el) {
        // Não desabilita botão voltar para o início
        if (
          el.type !== 'button' &&
          el.type !== 'hidden' &&
          !el.classList.contains('voltar-inicio')
        ) {
          el.disabled = true;
        }
      });
    }
    // Oculta botões salvar e cancelar
    if (btnSalvar) btnSalvar.style.display = 'none';
    if (btnCancelar) btnCancelar.style.display = 'none';
    // Opcional: desabilita clique na foto
    var fotoDiv = document.getElementById('foto-usuario-edicao');
    if (fotoDiv) {
      fotoDiv.style.pointerEvents = 'none';
      fotoDiv.style.opacity = '0.7';
    }
  }


});