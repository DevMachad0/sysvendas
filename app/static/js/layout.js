function enviarStorageParaVendas() {
  const user = JSON.parse(localStorage.getItem('user'));
  
  if (!user) {
      console.warn("Nenhum dado encontrado no localStorage.");
      return;
  }

  // Envia apenas o username
  fetch('/receber-dados-localstorage', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user._id, tipo: user.tipo, username: user.username })
  })
  .then(response => {
      if (!response.ok) throw new Error('Erro ao enviar dados');
      return response.json();
  })
  .then(data => {
      console.log('Dados recebidos pelo Flask:', data);
      // Agora você pode redirecionar ou chamar outra rota
      window.location.href = '/vendas'; // por exemplo
  })
  .catch(error => console.error('Erro:', error));
}
function enviarStorage() {
  const user = JSON.parse(localStorage.getItem('user'));
  
  if (!user) {
      console.warn("Nenhum dado encontrado no localStorage.");
      return;
  }

  // Envia apenas o username
  fetch('/receber-dados-localstorage', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user._id, tipo: user.tipo, username: user.username })
  })
  .then(response => {
      if (!response.ok) throw new Error('Erro ao enviar dados');
      return response.json();
  })
  .then(data => {
      console.log('Dados recebidos pelo Flask:', data);
      // Agora você pode redirecionar ou chamar outra rota
      window.location.href = '/'; // por exemplo
  })
  .catch(error => console.error('Erro:', error));
}


document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('btn-menu-mobile');
    const menuLateral = document.querySelector('.menu-lateral');
    let aberto = false;
    let animando = false;

    function abrirMenu() {
        menuLateral.classList.remove('menu-mobile-saindo');
        menuLateral.classList.add('menu-mobile-ativo');
        aberto = true;
    }

    function fecharMenu() {
        if (!aberto || animando) return;
        animando = true;
        menuLateral.classList.remove('menu-mobile-ativo');
        menuLateral.classList.add('menu-mobile-saindo');
        setTimeout(() => {
            menuLateral.classList.remove('menu-mobile-saindo');
            animando = false;
        }, 300); // tempo igual ao da animação CSS
        aberto = false;
    }

    function toggleMenu() {
        if (aberto) {
            fecharMenu();
        } else {
            abrirMenu();
        }
    }

    if (menuBtn) {
        menuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
    }

    // Fecha o menu ao clicar fora dele (opcional)
    document.addEventListener('click', function (e) {
        if (aberto && !menuLateral.contains(e.target) && e.target !== menuBtn) {
            fecharMenu();
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const nomeUsuario = document.getElementById('nome-usuario');
    const iconeUsuario = document.getElementById('icone-usuario');
    if (nomeUsuario && user.username) {
      nomeUsuario.textContent = user.username;
    }
    if (iconeUsuario) {
      if (user.foto) {
        iconeUsuario.textContent = '';
        iconeUsuario.style.backgroundImage = `url('data:image/png;base64,${user.foto}')`;
        iconeUsuario.style.backgroundSize = 'cover';
        iconeUsuario.style.backgroundPosition = 'center';
      } else {
        iconeUsuario.textContent = '👤';
        iconeUsuario.style.backgroundImage = '';
      }
    }

    // Função de logout
    const btnSair = document.querySelector('.btn-sair button');
    if (btnSair) {
        btnSair.addEventListener('click', function () {
            localStorage.removeItem('user');
            window.location.href = '/index.html';
        });
    }

    // Exibe o botão sair no menu mobile, se existir
    const btnSairMobile = document.querySelector('.btn-sair-mobile button');
    if (btnSairMobile) {
        btnSairMobile.addEventListener('click', function () {
            localStorage.removeItem('user');
            window.location.href = '/index.html';
        });
        // Garante que o botão fique visível no mobile
        btnSairMobile.parentElement.style.display = '';
    }
});
  // Adiciona evento para abrir edição do usuário ao clicar no topo
    document.addEventListener('DOMContentLoaded', function () {
      const usuarioTopbar = document.getElementById('usuario-topbar');
      if (usuarioTopbar) {
        usuarioTopbar.addEventListener('click', function () {
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          if (!user.username) return;
          fetch('/usuario_edicao', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: user.username })
          })
          .then(r => r.json())
          .then(function(data) {
            if (data.success) {
              window.location.href = '/usuario_edicao';
            }
          });
        });
      }
    });
    // Proteção de rota: redireciona para login se não estiver logado
    if (!localStorage.getItem('user')) {
      window.location.href = "/index.html";
    }

    // Oculta todos os links do menu imediatamente para evitar acesso indevido
    document.addEventListener('DOMContentLoaded', function () {
      var menu = document.querySelector('.menu-lateral');
      if (menu) {
        var links = menu.querySelectorAll('a');
        links.forEach(function(link) {
          link.style.display = 'none';
        });
      }
    });

    // Redireciona vendedor para /vendas ao acessar /
    (function() {
      var path = window.location.pathname;
      var user = JSON.parse(localStorage.getItem('user') || '{}');
      // Só redireciona se não estiver já em /vendas e não for iframe
      if (
        user.tipo === 'vendedor' &&
        (path === '/' || path === '/index.html') &&
        window.top === window.self &&
        !window.location.pathname.startsWith('/vendas')
      ) {
        if (typeof enviarStorageParaVendas === 'function') {
          enviarStorageParaVendas();
        } else {
          window.location.href = '/vendas';
        }
      }
    })();

    // Controle de acesso por tipo de usuário
    document.addEventListener('DOMContentLoaded', function () {
      var user = JSON.parse(localStorage.getItem('user') || '{}');
      var tipo = user.tipo || '';
      var menu = document.querySelector('.menu-lateral');
      if (!menu) return;
      var links = Array.from(menu.querySelectorAll('a'));
      var rotasPorTipo = {
        'admin': ['Inicio', 'Vendas', 'Produtos', 'Cadastrar', 'Usuários', 'Configs', 'Logs'],
        'vendedor': ['Vendas', 'Cadastrar vendas'],
        'pos_vendas': ['Inicio', 'Vendas', 'Usuários'],
        'faturamento': ['Inicio', 'Vendas']
      };
      var nomesPermitidos = (rotasPorTipo[tipo] || []).map(s => s.toLowerCase());
      links.forEach(function(link) {
        var texto = (link.textContent || '').replace(/[^a-zA-ZçÇáéíóúãõâêôüÁÉÍÓÚÃÕÂÊÔÜ ]/g, '').trim().toLowerCase();
        if (tipo === 'admin') {
          link.style.display = '';
          return;
        }
        if (nomesPermitidos.includes(texto)) {
          link.style.display = '';
        } else {
          link.style.display = 'none';
        }
      });

      // Redireciona apenas se NÃO estiver na página de edição de usuário ou cadastrar vendas
      var path = window.location.pathname;
      function estaNaRotaPermitida() {
        if (tipo === 'admin') return true;
        if (tipo === 'vendedor') {
          return (
            path.startsWith('/vendas') ||
            path === '/' ||
            path === '/index.html' ||
            path.startsWith('/cadastrar_vendas') ||
            path.startsWith('/editar')
          );
        }
        if (tipo === 'pos_vendas') {
          return (
            path === '/' ||
            path.startsWith('/usuarios') ||
            path.startsWith('/editar') ||
            path.startsWith('/vendas') ||
            path === '/index.html'
          );
        }
        if (tipo === 'faturamento') {
          // Libera acesso à edição de vendas
          return (
            path === '/' ||
            path.startsWith('/vendas') ||
            path.startsWith('/editar_venda') ||
            path === '/index.html'
          );
        }
        return true;
      }
      // Só redireciona se NÃO estiver em /usuario_edicao ou /cadastrar_vendas
      if (
        !estaNaRotaPermitida() &&
        !path.startsWith('/usuario_edicao') &&
        !path.startsWith('/cadastrar_vendas')
      ) {
        window.location.href = '/vendas';
      }
    });

    document.addEventListener('DOMContentLoaded', function () {
      window.onload = function () {
        // Pequeno delay para suavizar, pode ajustar ou remover
        setTimeout(function () {
          const loader = document.getElementById('page-loader');
          if (loader) {
            loader.classList.add('fade-out');
            setTimeout(() => loader.style.display = 'none', 400); // 400ms = mesmo do CSS
          }
        }, 400);
      };
    });

const user = JSON.parse(localStorage.getItem('user'));
const notificacoes = document.getElementById('notificacoes')
if (['vanessa.rocha', 'douglas.bessa'].includes(user.username)) {
  notificacoes.style.display = 'none'
}
if (!['vanessa.rocha', 'douglas.bessa'].includes(user.username)) {
  // Função para tocar som de notificação por status
  function tocarSomNotificacao(status) {
    try {
      let audioId = 'notificacao-audio';
      let audioSrc = '/static/audio/notificacao.mp3';
      if (status === 'aprovada') {
        audioId = 'notificacao-audio-aprovada';
        audioSrc = '/static/audio/vendas_aprovadas.mp3';
      } else if (status === 'refazer') {
        audioId = 'notificacao-audio-refazer';
        audioSrc = '/static/audio/vendas_refazer.mp3';
      }
      let audio = document.getElementById(audioId);
      if (!audio) {
        audio = document.createElement('audio');
        audio.id = audioId;
        audio.src = audioSrc;
        audio.preload = 'auto';
        document.body.appendChild(audio);
      }
      audio.currentTime = 0;
      audio.play();
    } catch (e) {}
  }

  // Função para notificação do navegador com status
  function notificarNavegador(titulo, mensagem, status) {
    if (window.Notification && Notification.permission === "granted") {
      new Notification(titulo, { body: mensagem });
      tocarSomNotificacao(status);
    }
  }

  // Solicita permissão para notificação assim que o usuário interagir (primeiro clique)
  (function() {
    let jaSolicitou = false;
    function solicitarPermissaoNotificacao() {
      if (
        window.Notification &&
        Notification.permission !== "granted" &&
        Notification.permission !== "denied" &&
        !jaSolicitou
      ) {
        Notification.requestPermission().then(function(permission) {
          jaSolicitou = true;
          // Opcional: pode exibir um aviso ou logar o resultado
          // console.log("Permissão de notificação:", permission);
        });
      }
    }
    // Solicita ao primeiro clique do usuário na página
    document.addEventListener('click', solicitarPermissaoNotificacao, { once: true });
  })();

  // Controle de notificações já exibidas (evita repetir)
  let notificacoesExibidas = new Set();

  function atualizarNotificacoes() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!user.username) return;
    fetch('/api/notificacoes')
      .then(r => r.json())
      .then(notifs => {
        const badge = document.querySelector('.notificacoes .badge');
        if (badge) {
          badge.textContent = notifs.length > 0 ? notifs.length : '';
          badge.style.display = notifs.length > 0 ? '' : 'none';
        }
        // Exibe lista ao clicar no sino
        const icone = document.querySelector('.notificacoes .icone-notificacao');
        if (icone) {
          icone.onclick = function() {
            let lista = document.getElementById('notificacoes-lista');
            if (!lista) {
              lista = document.createElement('div');
              lista.id = 'notificacoes-lista';
              lista.style.position = 'absolute';
              lista.style.top = '30px';
              lista.style.right = '0';
              lista.style.background = '#fff';
              lista.style.border = '1px solid #ccc';
              lista.style.zIndex = 9999;
              lista.style.minWidth = '250px';
              lista.style.maxWidth = '350px';
              lista.style.maxHeight = '350px';
              lista.style.overflowY = 'auto';
              lista.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
              document.querySelector('.notificacoes').appendChild(lista);
            }
            lista.innerHTML = '';
            if (notifs.length === 0) {
              lista.innerHTML = '<div style="padding:12px;">Sem notificações novas.</div>';
            } else {
              notifs.forEach(n => {
                const div = document.createElement('div');
                div.style.padding = '10px';
                div.style.borderBottom = '1px solid #eee';
                div.style.cursor = 'pointer';
                div.innerHTML = `<b>${n.mensagem}</b><br><small>${n.data_hora}</small>`;
                lista.appendChild(div);
              });
              // Marca todas como lidas ao abrir a lista
              const ids = notifs.map(n => n._id);
              if (ids.length > 0) {
                fetch('/api/notificacoes/marcar_lida', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({id: ids})
                }).then(() => {
                  setTimeout(atualizarNotificacoes, 300); // Atualiza badge após marcar lidas
                });
              }
            }
            // Fecha ao clicar fora
            document.addEventListener('click', function handler(e) {
              if (!lista.contains(e.target) && !icone.contains(e.target)) {
                lista.remove();
                document.removeEventListener('click', handler);
              }
            });
          };
        }

        // Notificação navegador + som para novas notificações
        if (window.Notification && Notification.permission === "granted") {
          notifs.forEach(n => {
            if (!notificacoesExibidas.has(n._id)) {
              // Detecta status da mensagem
              let status = '';
              if (n.mensagem && typeof n.mensagem === 'string') {
                const msg = n.mensagem.toLowerCase();
                if (msg.includes('status: aprovada')) status = 'aprovada';
                else if (msg.includes('status: marcada para refazer') || msg.includes('status: refazer')) status = 'refazer';
              }
              notificarNavegador("Nova notificação", n.mensagem, status);
              notificacoesExibidas.add(n._id);
            }
          });
        }
      });
  }

  // Atualiza a cada 1s
  setInterval(atualizarNotificacoes, 1000);
  document.addEventListener('DOMContentLoaded', atualizarNotificacoes);
}
