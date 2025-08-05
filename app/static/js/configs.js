document.addEventListener('DOMContentLoaded', function () {
  // Carrega vendedores no select
  fetch('/api/configs/vendedores')
    .then(r => r.json())
    .then(vendedores => {
      const select = document.getElementById('select-vendedor-limite');
      vendedores.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v._id;
        opt.textContent = v.nome_completo;
        select.appendChild(opt);
      });
    });

  // E-mails cópia múltiplos
  let emailsCopia = [];
  const inputEmailCopia = document.getElementById('input-email-copia');
  const btnAddCopia = document.getElementById('btn-add-copia');
  const listaEmailsCopia = document.getElementById('lista-emails-copia');

  function renderEmailsCopia() {
    listaEmailsCopia.innerHTML = '';
    emailsCopia.forEach((mail, idx) => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.gap = '6px';
      li.style.marginBottom = '2px';
      li.textContent = mail;
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
        emailsCopia.splice(idx, 1);
        renderEmailsCopia();
        atualizarInputEmailCopia();
      };
      li.appendChild(btnRemove);
      listaEmailsCopia.appendChild(li);
    });
    atualizarInputEmailCopia();
    inputEmailCopia.value = '';
  }

  function atualizarInputEmailCopia() {
    // Atualiza o campo hidden ou o input para enviar todos os e-mails separados por vírgula
    inputEmailCopia.value = '';
    if (emailsCopia.length > 0) {
      inputEmailCopia.setAttribute('data-emails', emailsCopia.join(','));
    } else {
      inputEmailCopia.removeAttribute('data-emails');
    }
  }

  btnAddCopia.addEventListener('click', function () {
    const valor = (inputEmailCopia.value || '').trim();
    if (!valor) return;
    // Validação simples de e-mail
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
      alert('E-mail inválido!');
      return;
    }
    if (!emailsCopia.includes(valor)) {
      emailsCopia.push(valor);
      renderEmailsCopia();
    }
  });

  inputEmailCopia.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      btnAddCopia.click();
    }
  });

  // Carregar configurações gerais nos campos
  fetch('/api/configs/geral')
    .then(r => r.json())
    .then(config => {
      if (config) {
        document.querySelector('[name="smtp"]').value = config.smtp || '';
        document.querySelector('[name="porta"]').value = config.porta || '';
        // Carrega e-mails cópia múltiplos
        emailsCopia = [];
        if (config.email_copia) {
          config.email_copia.split(',').map(e => e.trim()).forEach(e => {
            if (e) emailsCopia.push(e);
          });
        }
        renderEmailsCopia();
        document.querySelector('[name="meta_empresa"]').value = config.meta_empresa || '';
      }
    });

  // Salvar limite do vendedor
  document.getElementById('btn-salvar-limite').onclick = function () {
    const select = document.getElementById('select-vendedor-limite');
    const vendedor_id = select.value;
    const vendedor_nome = select.options[select.selectedIndex].textContent;
    const limite = document.getElementById('input-limite').value;
    if (!vendedor_id || !limite) {
      alert('Selecione o vendedor e informe o limite.');
      return;
    }
    fetch('/api/configs/limite_vendedor', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ vendedor_id, vendedor_nome, limite })
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Log de movimentação: Limite de vendedor atualizado
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const now = new Date();
        fetch('/api/inserir_log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                data: now.toLocaleDateString('pt-BR'),
                hora: now.toLocaleTimeString('pt-BR'),
                modificacao: 'Limite de vendedor atualizado: ' + vendedor_nome,
                usuario: user.username || ''
            })
        });

        alert('Limite salvo!');
        document.getElementById('input-limite').value = '';
        carregarLimites();
      }
    });
  };

  // Salvar geral
  document.getElementById('btn-salvar-geral').onclick = function () {
    const smtp = document.querySelector('[name="smtp"]').value;
    const porta = document.querySelector('[name="porta"]').value;
    // Pega todos os e-mails cópia
    const email_copia = emailsCopia.join(',');
    const meta_empresa = document.querySelector('[name="meta_empresa"]').value;
    fetch('/api/configs/geral', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ smtp, porta, email_copia, meta_empresa })
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Log de movimentação: Configurações gerais salvas
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const now = new Date();
        fetch('/api/inserir_log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                data: now.toLocaleDateString('pt-BR'),
                hora: now.toLocaleTimeString('pt-BR'),
                modificacao: 'Configurações gerais salvas',
                usuario: user.username || ''
            })
        });
      }
    });
  };

  // Carregar limites cadastrados
  function carregarLimites() {
    fetch('/api/configs/limites_vendedores')
      .then(r => r.json())
      .then(limites => {
        const ul = document.getElementById('lista-limites-vendedores');
        ul.innerHTML = '';
        limites.forEach(l => {
          const li = document.createElement('li');
          li.textContent = `${l.vendedor_nome}: R$ ${l.limite}`;
          ul.appendChild(li);
        });
      });
  }
  carregarLimites();

  // Testar E-mail SMTP principal
  const btnTestarEmail = document.getElementById('btn-testar-email');
  if (btnTestarEmail) {
    btnTestarEmail.addEventListener('click', function() {
      const smtp = document.getElementById('input-smtp').value;
      const porta = document.getElementById('input-porta').value;
      const email_smtp = document.getElementById('input-email-smtp').value;
      const senha_email_smtp = document.getElementById('input-senha-email-smtp').value;
      const email_copia = document.getElementById('input-email-copia').value;
      const resultado = document.getElementById('resultado-teste-email');
      resultado.textContent = 'Enviando e-mail de teste...';

      fetch('/api/testar_email', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          smtp,
          porta,
          email_smtp,
          senha_email_smtp,
          email_copia
        })
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.success) {
          resultado.style.color = '#27ae60';
          resultado.textContent = 'E-mail de teste enviado com sucesso!';
        } else {
          resultado.style.color = '#e74c3c';
          resultado.textContent = 'Erro ao enviar e-mail de teste: ' + (resp.msg || resp.erro || 'Verifique as configurações.');
        }
      })
      .catch(() => {
        resultado.style.color = '#e74c3c';
        resultado.textContent = 'Erro ao enviar e-mail de teste.';
      });
    });
  }

  // Testar E-mail SMTP secundário
  const btnTestarEmailSec = document.getElementById('btn-testar-email-secundario');
  if (btnTestarEmailSec) {
    btnTestarEmailSec.addEventListener('click', function() {
      const smtp = document.getElementById('input-smtp').value;
      const porta = document.getElementById('input-porta').value;
      const email_smtp = document.getElementById('input-email-smtp-secundario').value;
      const senha_email_smtp = document.getElementById('input-senha-email-smtp').value;
      const email_copia = document.getElementById('input-email-copia').value;
      const resultado = document.getElementById('resultado-teste-email-secundario');
      resultado.textContent = 'Enviando e-mail de teste...';

      fetch('/api/testar_email', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          smtp,
          porta,
          email_smtp,
          senha_email_smtp,
          email_copia
        })
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.success) {
          resultado.style.color = '#27ae60';
          resultado.textContent = 'E-mail de teste enviado com sucesso!';
        } else {
          resultado.style.color = '#e74c3c';
          resultado.textContent = 'Erro ao enviar e-mail de teste: ' + (resp.msg || resp.erro || 'Verifique as configurações.');
        }
      })
      .catch(() => {
        resultado.style.color = '#e74c3c';
        resultado.textContent = 'Erro ao enviar e-mail de teste.';
      });
    });
  }

  // Preenche o select de vendedores para metas
  fetch('/api/configs/vendedores')
    .then(r => r.json())
    .then(vendedores => {
      const select = document.getElementById('select-vendedor-meta');
      vendedores.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v._id;
        opt.textContent = v.nome_completo;
        select.appendChild(opt);
      });
    });

  // Evento para cadastrar/atualizar meta do vendedor
  document.getElementById('btn-atualizar-meta-vendedor').onclick = function() {
    const vendedor_id = document.getElementById('select-vendedor-meta').value;
    const vendedor_nome = document.getElementById('select-vendedor-meta').selectedOptions[0]?.textContent || '';
    const meta_dia_quantidade = document.getElementById('meta-dia-quantidade').value;
    const meta_dia_valor = document.getElementById('meta-dia-valor').value;
    const meta_semana = document.getElementById('meta-semana').value;
    if (!vendedor_id) {
      alert('Selecione um vendedor');
      return;
    }
    fetch('/api/configs/metas_vendedor', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        vendedor_id,
        vendedor_nome,
        meta_dia_quantidade,
        meta_dia_valor,
        meta_semana
      })
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        alert('Meta cadastrada/atualizada com sucesso!');
      } else {
        alert('Erro ao salvar meta: ' + (resp.erro || ''));
      }
    });
  };

  // --- NOVO: Carregar valores de acesso extra ---
  fetch('/api/configs/valor_acesso')
    .then(r => r.json())
    .then(cfg => {
      document.getElementById('input-valor-acesso-nova-venda').value = cfg.valor_acesso_nova_venda || cfg.valor_acesso || '';
      document.getElementById('input-valor-acesso-atualizacao').value = cfg.valor_acesso_atualizacao || '';
    });

  // --- NOVO: Salvar valores de acesso extra ---
  document.getElementById('btn-salvar-valor-acesso').onclick = function () {
    const valorAcessoNovaVenda = document.getElementById('input-valor-acesso-nova-venda').value;
    const valorAcessoAtualizacao = document.getElementById('input-valor-acesso-atualizacao').value;
    fetch('/api/configs/valor_acesso', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        valor_acesso_nova_venda: valorAcessoNovaVenda,
        valor_acesso_atualizacao: valorAcessoAtualizacao
      })
    })
      .then(r => r.json())
      .then(resp => {
        if (resp.success) {
          alert('Valores de acesso salvos!');
        } else {
          alert('Erro ao salvar valores de acesso: ' + (resp.erro || ''));
        }
      });
  };
});