document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("mostrar-opcoes-pdf");
  const downloadDiv = document.getElementById("download");

  function isMobile() {
    return window.innerWidth <= 768;
  }

  if (btn && downloadDiv) {
    btn.addEventListener("click", function () {
      if (isMobile()) {
        downloadDiv.classList.toggle("mostrar");
      } else {
        // desktop: comportamento antigo
        downloadDiv.style.display = (downloadDiv.style.display === "block") ? "none" : "block";
      }
    });

    // Garante que ao redimensionar, o form só aparece se a classe estiver presente
    window.addEventListener("resize", function () {
      if (isMobile()) {
        if (!downloadDiv.classList.contains("mostrar")) {
          downloadDiv.style.display = "";
        }
      } else {
        downloadDiv.classList.remove("mostrar");
        downloadDiv.style.display = "none";
      }
    });
  }
});

document.getElementById("form-graficos").addEventListener("submit", function(event) {
  const checkboxes = document.querySelectorAll('input[name="graficos"]:checked');
  if (checkboxes.length === 0) {
    alert("Por favor, selecione pelo menos um gráfico antes de baixar o relatório.");
    event.preventDefault();
  }
});

function registrarLogDownloadPDF() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const now = new Date();
  fetch('/api/inserir_log', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      data: now.toLocaleDateString('pt-BR'),
      hora: now.toLocaleTimeString('pt-BR'),
      modificacao: 'Download do relatório PDF',
      usuario: user.username || user.nome_vendedor || ''
    })
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const botao = document.getElementById("mostrar-opcoes-pdf");
  const formContainer = document.getElementById("download");

  const botaoDownload = document.getElementById("botao-download");
  if (botaoDownload) {
    botaoDownload.addEventListener("click", registrarLogDownloadPDF);
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const tabs = document.querySelectorAll('.tab-menu');
  const graphTabs = document.querySelectorAll('.grafico-tab');
  const nomeGrafico = document.getElementById('nome-grafico-ativo');
  // Mapeamento para mostrar o nome do gráfico ativo
  const nomes = {
    vendas_geral: 'Vendas Geral',
    vendas_vendedor: 'Vendas Mensais por Vendedor',
    vendas_diarias: 'Vendas Diárias por Vendedor',
    vendas_diarias_linhas: 'Vendas Diárias Linhas',
    quantidade_vendas_diarias: 'Quantidade de Vendas Diárias',
    vendas_fim_de_semana: 'Vendas no Fim de Semana por Vendedor',
    quantidade_vendas_fim_de_semana: 'Quantidade de Vendas no Fim de Semana por Vendedor',
    metas_vendedor: 'Metas Mensais dos Vendedores',
    metas_semanais_vendedor: 'Metas Semanais dos Vendedores',
    metas_diarias_vendedor: 'Metas Diárias dos Vendedores',
    banco_vendedores: 'Banco dos Vendedores',
    status_vendas_vendedor: 'Status das Vendas',
    prazo_vendas_vendedor: 'Vendas por Prazo e Vendedor',
    verdes_vermelhos_geral: 'Tipos de Clientes Geral',
    verdes_vermelhos_vendedor: 'Tipos de Clientes por Vendedor',
    tipo_vendas_geral: 'Tipo Vendas Geral',
    tipo_vendas_por_vendedor: 'Tipo Vendas por Vendedor',
    produtos_mais_vendidos: 'Produtos mais Vendidos',
    mapa_vendas_por_estado: 'Mapa Vendas por Estado'
  };

  const carregarGrafico = (idGrafico) => {
    const container = document.querySelector(`.grafico-tab.${idGrafico} .grafico-conteudo`);
    if (!container || container.dataset.carregado === "true") return;
  
    const params = new URLSearchParams(window.location.search);
  
    fetch(`/grafico/${idGrafico}?${params}`)
      .then(res => res.json())
      .then(data => {
        container.innerHTML = data.grafico_html;

        // Força execução dos <script> dentro do HTML inserido
        const scripts = container.querySelectorAll("script");
        scripts.forEach(oldScript => {
          const newScript = document.createElement("script");
          if (oldScript.src) {
            newScript.src = oldScript.src;
          } else {
            newScript.textContent = oldScript.textContent;
          }
          oldScript.parentNode.replaceChild(newScript, oldScript);
        });

        container.dataset.carregado = "true";
      })
      .catch(() => {
        container.innerHTML = "<p>Erro ao carregar gráfico.</p>";
      });
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      const tabId = this.getAttribute('data-tab');
      carregarGrafico(tabId);
      tabs.forEach(t => t.classList.remove('active'));
      graphTabs.forEach(g => g.classList.remove('active'));
      this.classList.add('active');
      document.querySelector('.grafico-tab.' + tabId).classList.add('active');
      if (nomeGrafico) nomeGrafico.textContent = nomes[tabId] || '';
      // Força o Plotly a redimensionar (corrige bug de gráfico achatado)
      setTimeout(() => {
        const plot = document.querySelector('.grafico-tab.' + tabId + ' .js-plotly-plot');
        if (plot && window.Plotly && typeof Plotly.Plots.resize === 'function') {
          Plotly.Plots.resize(plot);
        }
      }, 100);
    });

    const abaAtiva = document.querySelector('.tab-menu.active');
    if (abaAtiva) carregarGrafico(abaAtiva.getAttribute('data-tab'));
  });

  // Força resize do gráfico ativo ao carregar (corrige bug inicial)
  setTimeout(() => {
    const activeTab = document.querySelector('.grafico-tab.active .js-plotly-plot');
    if (activeTab && window.Plotly && typeof Plotly.Plots.resize === 'function') {
      Plotly.Plots.resize(activeTab);
    }
  }, 200);

});

setTimeout(function() {
  window.location.reload();
}, 10 * 60 * 1000);

document.addEventListener("DOMContentLoaded", function () {
  // Script para selecionar/desmarcar todos os checkboxes de gráficos
  const btnSelecionar = document.getElementById('selecionar-todos-graficos');
  const btnDesmarcar = document.getElementById('desmarcar-todos-graficos');
  if (btnSelecionar && btnDesmarcar) {
    btnSelecionar.addEventListener('click', function() {
      document.querySelectorAll('input[name="graficos"]').forEach(cb => cb.checked = true);
    });
    btnDesmarcar.addEventListener('click', function() {
      document.querySelectorAll('input[name="graficos"]').forEach(cb => cb.checked = false);
    });
  }
});
