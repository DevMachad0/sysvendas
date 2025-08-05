document.addEventListener('DOMContentLoaded', function () {
  const container = document.getElementById('usuarios-cards');
  const paginacaoDiv = document.querySelector('.usuarios-paginacao');
  let usuarios = [];
  let paginaAtual = 1;
  const porPagina = 10;

  function renderUsuariosPagina() {
    container.innerHTML = '';
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isPosVendas = user.tipo === 'pos_vendas';
    const inicio = (paginaAtual - 1) * porPagina;
    const fim = inicio + porPagina;

    // Se não há usuários, mostra mensagem
    if (usuarios.length === 0) {
      const msg = document.createElement('div');
      msg.className = 'nenhum-usuario';
      msg.textContent = 'Nenhum usuário encontrado.';
      container.appendChild(msg);
      return;
    }

    usuarios.slice(inicio, fim).forEach(usuario => {
      // Exibir apenas vendedores atribuídos ao pos_vendas logado
      if (isPosVendas) {
        if (usuario.tipo !== 'vendedor') return;
        // pos_vendas pode ser string separada por vírgula
        const posVendasList = (usuario.pos_vendas || '').split(',').map(s => s.trim()).filter(Boolean);
        if (!posVendasList.includes(user.username)) return;
      }

      const card = document.createElement('div');
      card.className = 'card-usuario';

      // Foto
      const fotoDiv = document.createElement('div');
      fotoDiv.className = 'foto-usuario';
      if (usuario.foto) {
        const img = document.createElement('img');
        img.src = usuario.foto.startsWith('data:') ? usuario.foto : `data:image/png;base64,${usuario.foto}`;
        img.alt = usuario.username;
        img.style.width = '70px';
        img.style.height = '70px';
        img.style.borderRadius = '50%';
        fotoDiv.appendChild(img);
      } else {
        fotoDiv.textContent = 'Foto';
      }

      // Dados
      const dadosDiv = document.createElement('div');
      dadosDiv.className = 'dados-usuario';
      dadosDiv.innerHTML = `
        <p><strong>${usuario.username}</strong></p>
        <p>${usuario.tipo ? usuario.tipo.charAt(0).toUpperCase() + usuario.tipo.slice(1) : ''}</p>
        <p>Status: ${usuario.status ? (usuario.status.charAt(0).toUpperCase() + usuario.status.slice(1)) : ''}</p>
      `;

      card.appendChild(fotoDiv);
      card.appendChild(dadosDiv);

      // Clique para editar
      card.style.cursor = 'pointer';
      card.addEventListener('click', function() {
        fetch('/usuario_edicao', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: usuario.username })
        })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            // Log de movimentação: Acesso à edição de usuário
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            const now = new Date();
            fetch('/api/inserir_log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    data: now.toLocaleDateString('pt-BR'),
                    hora: now.toLocaleTimeString('pt-BR'),
                    modificacao: 'Acesso à edição de usuário: ' + usuario.username,
                    usuario: user.username || ''
                })
            });

            window.location.href = '/usuario_edicao';
          }
        });
      });

      container.appendChild(card);
    });
  }

function renderPaginacao() {
  paginacaoDiv.innerHTML = '';
  const totalPaginas = Math.ceil(usuarios.length / porPagina);

  // Só mostra paginação se precisar de mais de uma página
  if (totalPaginas <= 1) return;

  // Botão anterior
  const btnAnt = document.createElement('button');
  btnAnt.innerHTML = '&laquo;';
  btnAnt.disabled = paginaAtual === 1;
  btnAnt.onclick = () => {
    if (paginaAtual > 1) {
      paginaAtual--;
      atualizar();
    }
  };
  paginacaoDiv.appendChild(btnAnt);

  // Botões de página
  for (let p = 1; p <= totalPaginas; p++) {
    const btn = document.createElement('button');
    btn.textContent = p;
    if (p === paginaAtual) btn.className = 'ativo';
    btn.onclick = () => {
      paginaAtual = p;
      atualizar();
    };
    paginacaoDiv.appendChild(btn);
  }

  // Botão próximo
  const btnProx = document.createElement('button');
  btnProx.innerHTML = '&raquo;';
  btnProx.disabled = paginaAtual === totalPaginas || totalPaginas === 0;
  btnProx.onclick = () => {
    if (paginaAtual < totalPaginas) {
      paginaAtual++;
      atualizar();
    }
  };
  paginacaoDiv.appendChild(btnProx);
}
  function fetchUsuariosComFiltro(nome, tipo, status, pos_vendas) {
    const params = new URLSearchParams();
    if (nome) params.append('nome', nome);
    if (tipo) params.append('tipo', tipo);
    if (status) params.append('status', status);
    if (pos_vendas) params.append('pos_vendas', pos_vendas);

    return fetch('/api/usuarios?' + params.toString())
      .then(r => r.json());
  }

  function atualizar() {
    renderUsuariosPagina();
    renderPaginacao();
  }

  // Atualiza a busca ao enviar o filtro
  const form = document.getElementById('filtro-form');
  const inputBusca = document.getElementById('busca');
  const selectTipo = document.getElementById('tipo');
  const selectStatus = document.getElementById('status');

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const busca = (inputBusca.value || '').trim();
    const tipo = selectTipo.value;
    const status = selectStatus.value;

    fetchUsuariosComFiltro(busca, tipo, status).then(data => {
      usuarios = data;
      // Garante que a página sempre seja 1, ou última possível após filtro
      paginaAtual = 1;
      if (usuarios.length > 0) {
        const totalPaginas = Math.ceil(usuarios.length / porPagina);
        if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;
      }
      atualizar();
    });
  });

  // Carrega todos ao iniciar
  fetchUsuariosComFiltro('', '', '').then(data => {
    usuarios = data;
    paginaAtual = 1;
    atualizar();
  });
});