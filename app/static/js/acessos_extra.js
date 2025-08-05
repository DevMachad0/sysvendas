// =======================================
// INÍCIO: VARIÁVEIS GLOBAIS E FETCH API
// =======================================

let clicouSelectProduto = false;
let trocouProduto = false; // NOVO: controla troca de produto

let valorAcessoExtra = 0;
let valorAcessoAtualizacao = 0;

fetch('/api/configs/valor_acesso')
  .then(r => r.json())
  .then(cfg => {
    valorAcessoExtra = parseFloat(cfg.valor_acesso_nova_venda || cfg.valor_acesso || 0) || 0;
    valorAcessoAtualizacao = parseFloat(cfg.valor_acesso_atualizacao || 0) || 0;
  });

// =======================================
// Função utilitária global
// =======================================
function produtoEhPersonalizado(produtoSelect) {
  return produtoSelect && produtoSelect.value && produtoSelect.value.startsWith('Personalizado:');
}

// =======================================
// INÍCIO: EVENTOS PRINCIPAIS DO DOM
// =======================================
document.addEventListener('DOMContentLoaded', function() {
  const produtoSelect = document.getElementById('produto');
  const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
  const condicaoSelect = document.getElementById('condicoes');
  const minInfo = document.getElementById('min-acessos-info');

  // =======================================
  // EVENTOS DE PRODUTO E CONDIÇÃO
  // =======================================
  if (produtoSelect) {
    produtoSelect.addEventListener('focus', function() {
      clicouSelectProduto = true;
    });
    produtoSelect.addEventListener('change', function() {
      trocouProduto = true; // MARCA QUE TROCOU PRODUTO
      checarCondicaoLicencaExtra();
      atualizarValorTabelaPorCondicao();
    });
  }
  if (condicaoSelect) {
    condicaoSelect.addEventListener('change', function() {
      checarCondicaoLicencaExtra();
      atualizarValorTabelaPorCondicao();
    });
  }

  // =======================================
  // Listener para quantidade de acessos
  // =======================================
  if (qtdAcessosInput) {
    qtdAcessosInput.addEventListener('input', function() {
      if (
        produtoSelect &&
        produtoSelect.value &&
        produtoSelect.value.trim().toLowerCase() === 'licença extra - novo'
      ) {
        calcularValorLicencaExtraDinamico();
      } else {
        calcularValorProdutoNormal();
      }
    });
  }

  // =======================================
  // INÍCIO CONDIÇÃO ESPECIAL: "Licença Extra"
  // =======================================
  function checarCondicaoLicencaExtra() {
    const produtoEhLicencaExtra = (
      produtoSelect &&
      produtoSelect.value &&
      produtoSelect.value.trim().toLowerCase() === 'licença extra - novo'
    );

    if (clicouSelectProduto === true && produtoEhLicencaExtra) {
      logicaLicencaExtra();
    }
  }

  function logicaLicencaExtra() {
    const valorTabelaInput = document.getElementById('valor_tabela');
    const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
    const condicaoSelect = document.getElementById('condicoes');
    const minInfo = document.getElementById('min-acessos-info');

    if (!valorTabelaInput || !qtdAcessosInput || !condicaoSelect) return;

    // Força quantidade de acessos para 1 e min=1
    qtdAcessosInput.setAttribute('value', '1');
    qtdAcessosInput.setAttribute('min', '1');
    if (minInfo) {
      minInfo.textContent = 'Mínimo 1 acesso.';
    }

    // Busca o valor da condição selecionada (pelo atributo data-valor)
    const opt = condicaoSelect.options[condicaoSelect.selectedIndex];
    let valorCondicao = parseFloat(opt?.dataset.valor || 0) || 0;
    let valorFormatado = valorCondicao.toFixed(2);

    // Preenche input e atributo value
    valorTabelaInput.value = valorFormatado;
    valorTabelaInput.setAttribute('value', valorFormatado);

    // Após forçar 1, dispara cálculo inicial
    calcularValorLicencaExtraDinamico();
  }

  function calcularValorLicencaExtraDinamico() {
    const valorTabelaInput = document.getElementById('valor_tabela');
    const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
    const condicaoSelect = document.getElementById('condicoes');
    if (!valorTabelaInput || !qtdAcessosInput || !condicaoSelect) return;

    const opt = condicaoSelect.options[condicaoSelect.selectedIndex];
    let valorBase = parseFloat(opt?.dataset.valor || 0) || 0;

    let qtdAtual = parseInt(qtdAcessosInput.value, 10) || 1;
    let resultado = 0;
    if (qtdAtual >= 1) {
      resultado = valorBase * qtdAtual;
    } else {
      resultado = valorBase;
      qtdAcessosInput.value = 1;
    }

    valorTabelaInput.value = resultado.toFixed(2);
  }
  // =======================================
  // FIM CONDIÇÃO "Licença Extra"
  // =======================================

  // =======================================
  // INÍCIO CONDIÇÃO: Produto NORMAL
  // =======================================
  function calcularValorProdutoNormal() {
    const valorTabelaInput = document.getElementById('valor_tabela');
    const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
    const produtoSelect = document.getElementById('produto');
    if (!valorTabelaInput || !qtdAcessosInput || !produtoSelect) return;

    let qtdAtual = parseInt(qtdAcessosInput.value, 10) || 2;
    let qtdOriginal = 2;

    if (!trocouProduto) {
      if (typeof window.quantidadeAcessosBanco !== "undefined") {
        qtdOriginal = parseInt(window.quantidadeAcessosBanco, 10) || 2;
      } else if (qtdAcessosInput.defaultValue) {
        qtdOriginal = parseInt(qtdAcessosInput.defaultValue, 10) || 2;
      }
    }
    // Se trocouProduto==true, sempre será 2 (default)

    let valorTabelaBase = parseFloat(valorTabelaInput.getAttribute('value')?.replace(',', '.') || 0) || 0;

    // NOVO: verifica se é "Atualização" (case insensitive)
    let produtoEhAtualizacao = produtoSelect.value && produtoSelect.value.trim().toLowerCase() === 'produtoaaa';

    // Se for atualização, usa valorAcessoAtualizacao, senão valorAcessoExtra
    let valorAcesso = valorAcessoExtra;

    let resultado = valorTabelaBase + ((qtdAtual - qtdOriginal) * valorAcesso);

    valorTabelaInput.value = resultado > 0 ? resultado.toFixed(2) : '';
  }
  // =======================================
  // FIM CONDIÇÃO: Produto NORMAL
  // =======================================

  // =======================================
  // INÍCIO: Atualizar valor_tabela ao trocar condição/produto (produtos normais)
  // =======================================
  function atualizarValorTabelaPorCondicao() {
    const produtoSelect = document.getElementById('produto');
    const valorTabelaInput = document.getElementById('valor_tabela');
    const condicaoSelect = document.getElementById('condicoes');

    // Se for personalizado, não faz nada
    if (produtoSelect == 'Personalizado:' || produtoSelect == 'Personalizado' || produtoEhPersonalizado(produtoSelect)) {
      return;
    }
    if (!produtoSelect || !valorTabelaInput || !condicaoSelect) return;

    // Só executa para produtos NORMAIS (não "Licença Extra")
    if (produtoSelect.value.trim().toLowerCase() !== 'licença extra - novo') {
      const opt = condicaoSelect.options[condicaoSelect.selectedIndex];
      let valorCondicao = parseFloat(opt?.dataset.valor || 0) || 0;
      let valorFormatado = valorCondicao.toFixed(2);

      valorTabelaInput.value = valorFormatado;
      valorTabelaInput.setAttribute('value', valorFormatado);
    }
  }
  // =======================================
  // FIM: Atualizar valor_tabela ao trocar condição/produto
  // =======================================

  // ===============================
  // INÍCIO: AJUSTE ISOLADO PARA PRODUTO PERSONALIZADO
  // ===============================
  function setValorTabelaPersonalizado() {
    const produtoSelect = document.getElementById('produto');
    const valorTabelaInput = document.getElementById('valor_tabela');
    if (produtoEhPersonalizado(produtoSelect) && valorTabelaInput) {
      setTimeout(function() {
        if (produtoEhPersonalizado(produtoSelect)) {
          valorTabelaInput.value = valorTabelaInput.getAttribute('value') || '';
        }
      }, 2500);
    }
  }
  setValorTabelaPersonalizado();
  if (produtoSelect) {
    produtoSelect.addEventListener('change', setValorTabelaPersonalizado);
  }
  // ===============================
  // FIM: AJUSTE ISOLADO PARA PRODUTO PERSONALIZADO
  // ===============================

  
  // ===============================
  // BLOCO ISOLADO: FORÇA QTD ACESSOS = 2 PARA PRODUTO NORMAL
  // ===============================
  if (produtoSelect && qtdAcessosInput) {
    produtoSelect.addEventListener('change', function() {
      const v = produtoSelect.value ? produtoSelect.value.trim().toLowerCase() : '';

      if (
        v !== 'licença extra - novo' &&

        !v.startsWith('personalizado:') &&
        v !== ''
      ) {
        qtdAcessosInput.value = 2;
        qtdAcessosInput.setAttribute('value', '2');
        qtdAcessosInput.min = 2;
        qtdAcessosInput.setAttribute('min', '2');
        if (minInfo) minInfo.textContent = 'Mínimo 2 acessos.';
      }
    });
  }
  // ===============================
  // FIM BLOCO ISOLADO
  // ===============================
// =======================================
// FORÇA valor_tabela 1s após carregamento
// =======================================
setTimeout(function() {
    
  const valorTabelaInput = document.getElementById('valor_tabela');
  const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
  const valorTabelaCalculo = window.valor_tabela;
  if (valorTabelaInput) {
    // Usando Jinja2 (Flask), para garantir 2 casas decimais:
    const valorBackend = valorTabelaCalculo;
    valorTabelaInput.value = valorBackend;
    valorTabelaInput.setAttribute('value', valorBackend);
    
  }
}, 900);

});
document.addEventListener('DOMContentLoaded', function () {
  const produtoSelect = document.getElementById('produto');
  const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
  const minInfo = document.getElementById('min-acessos-info');
  const valorTabelaInput = document.getElementById('valor_tabela');
  const ulPersonalizados = document.getElementById('lista-produtos-personalizados-editar');

  if (!produtoSelect || !qtdAcessosInput || !ulPersonalizados) return;

  function getItensPersonalizados() {
    return Array.from(ulPersonalizados.querySelectorAll('li')).map(li => li.firstChild.nodeValue.trim());
  }

  function atualizarMinimoAcessosPersonalizado() {
    // Só executa se produto for personalizado
    if (!produtoSelect.value.toLowerCase().startsWith('personalizado')) return;

    const itens = getItensPersonalizados();
    const qtdAtualizacao = itens.filter(t => t.toLowerCase() === 'atualização').length;
    const qtdLicencaExtraAtualizacao = itens.filter(t => t.toLowerCase() === 'licença extra - atualização').length;

    // Só ativa a lógica se há pelo menos 1 de cada
    if (qtdAtualizacao > 0 && qtdLicencaExtraAtualizacao > 0) {
      const minAcessos = 3 + (qtdLicencaExtraAtualizacao - 1);

      // Ajusta campo de input e info do mínimo
      qtdAcessosInput.min = minAcessos;
      qtdAcessosInput.value = minAcessos;
      qtdAcessosInput.setAttribute('min', minAcessos.toString());
      if (minInfo) minInfo.textContent = `Mínimo ${minAcessos} acessos.`;

      // Calcula e atualiza valor_tabela dinamicamente
      function atualizarValor() {
        let qtd = parseInt(qtdAcessosInput.value, 10) || minAcessos;
        if (qtd < minAcessos) {
          qtd = minAcessos;
          qtdAcessosInput.value = minAcessos;
        }
        let valorBase = parseFloat(valorTabelaInput.getAttribute('value')?.replace(',', '.') || 0) || 0;
        let resultado = valorBase + ((qtd - minAcessos) * valorAcessoExtra);
        valorTabelaInput.value = resultado.toFixed(2);
      }

      // Remove event antigo para evitar sobreposição
      if (qtdAcessosInput._personalizadoListener) {
        qtdAcessosInput.removeEventListener('input', qtdAcessosInput._personalizadoListener);
      }
      qtdAcessosInput._personalizadoListener = atualizarValor;
      qtdAcessosInput.addEventListener('input', atualizarValor);

      // Roda cálculo inicial
      atualizarValor();
    }
  }

  // Observa mudanças nos <li> do <ul>
  const observer = new MutationObserver(function () {
    atualizarMinimoAcessosPersonalizado();
  });
  observer.observe(ulPersonalizados, { childList: true });

  // Executa ao carregar página
  atualizarMinimoAcessosPersonalizado();

  // Se trocar select, também revalida
  produtoSelect.addEventListener('change', function () {
    setTimeout(atualizarMinimoAcessosPersonalizado, 10); // pequeno delay para DOM atualizar
  });
});
document.addEventListener('DOMContentLoaded', function () {
  const produtoSelect = document.getElementById('produto');
  const qtdAcessosInput = document.getElementById('quantidade-acessos-editar');
  const minInfo = document.getElementById('min-acessos-info');
  const valorTabelaInput = document.getElementById('valor_tabela');
  const ulPersonalizados = document.getElementById('lista-produtos-personalizados-editar');

  if (!produtoSelect || !qtdAcessosInput || !ulPersonalizados) return;

  function getItensPersonalizados() {
    return Array.from(ulPersonalizados.querySelectorAll('li')).map(li => li.firstChild.nodeValue.trim());
  }

  function atualizarMinimoAcessosPersonalizado() {
    // Só executa se produto for personalizado
    if (!produtoSelect.value.toLowerCase().startsWith('personalizado')) return;

    const itens = getItensPersonalizados();
    const qtdAtualizacao = itens.filter(t => t.toLowerCase() === 'atualização').length;
    const qtdLicencaExtraAtualizacao = itens.filter(t => t.toLowerCase() === 'licença extra - atualização').length;

    // Só ativa a lógica se há pelo menos 1 de cada
    if (qtdAtualizacao > 0 && qtdLicencaExtraAtualizacao > 0) {
      const minAcessos = 3 + (qtdLicencaExtraAtualizacao - 1);

      // Ajusta campo de input e info do mínimo
      qtdAcessosInput.min = minAcessos;
      qtdAcessosInput.value = minAcessos;
      qtdAcessosInput.setAttribute('min', minAcessos.toString());
      if (minInfo) minInfo.textContent = `Mínimo ${minAcessos} acessos.`;

      // Calcula e atualiza valor_tabela dinamicamente
      function atualizarValor() {
        let qtd = parseInt(qtdAcessosInput.value, 10) || minAcessos;
        if (qtd < minAcessos) {
          qtd = minAcessos;
          qtdAcessosInput.value = minAcessos;
        }
        let valorBase = parseFloat(valorTabelaInput.getAttribute('value')?.replace(',', '.') || 0) || 0;
        let resultado = valorBase + ((qtd - minAcessos) * valorAcessoExtra);
        valorTabelaInput.value = resultado.toFixed(2);
      }

      // Remove event antigo para evitar sobreposição
      if (qtdAcessosInput._personalizadoListener) {
        qtdAcessosInput.removeEventListener('input', qtdAcessosInput._personalizadoListener);
      }
      qtdAcessosInput._personalizadoListener = atualizarValor;
      qtdAcessosInput.addEventListener('input', atualizarValor);

      // Roda cálculo inicial
      atualizarValor();
    }
  }

  // Observa mudanças nos <li> do <ul>
  const observer = new MutationObserver(function () {
    atualizarMinimoAcessosPersonalizado();
  });
  observer.observe(ulPersonalizados, { childList: true });

  // Executa ao carregar página
  atualizarMinimoAcessosPersonalizado();

  // Se trocar select, também revalida
  produtoSelect.addEventListener('change', function () {
    setTimeout(atualizarMinimoAcessosPersonalizado, 10); // pequeno delay para DOM atualizar
  });
});
