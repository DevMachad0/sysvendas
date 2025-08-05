document.addEventListener('DOMContentLoaded', function () {
    const logs = window.logsData || [];
    const porPagina = 8;
    let paginaAtual = 1;
    let logsFiltrados = logs.slice();

    const tbody = document.getElementById('tabela-logs-body');
    const paginacao = document.getElementById('paginacao-logs');

    function renderTabela() {
      tbody.innerHTML = '';
      const inicio = (paginaAtual - 1) * porPagina;
      const fim = inicio + porPagina;
      logsFiltrados.slice(inicio, fim).forEach(log => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${log.data}</td>
          <td>${log.hora}</td>
          <td>${log.modificacao}</td>
          <td>${log.usuario}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function renderPaginacao() {
      paginacao.innerHTML = '';

      const totalPaginas = Math.ceil(logsFiltrados.length / porPagina);
      if (totalPaginas <= 1) return;

      const btnAnt = document.createElement('button');
      btnAnt.innerHTML = '&laquo;';
      btnAnt.disabled = paginaAtual === 1;
      btnAnt.onclick = () => {
        paginaAtual--;
        atualizar();
      };
      paginacao.appendChild(btnAnt);

      // Mostra sempre as 2 primeiras, 2 últimas e 1 antes/depois da atual (se necessário)
      let paginas = [];
      if (totalPaginas <= 5) {
        for (let p = 1; p <= totalPaginas; p++) paginas.push(p);
      } else {
        paginas = [1];
        if (paginaAtual > 3) paginas.push('...');
        let start = Math.max(2, paginaAtual - 1);
        let end = Math.min(totalPaginas - 1, paginaAtual + 1);
        for (let p = start; p <= end; p++) paginas.push(p);
        if (paginaAtual + 1 < totalPaginas - 1) paginas.push('...');
        paginas.push(totalPaginas);
      }

      paginas.forEach(p => {
        if (p === '...') {
          const span = document.createElement('span');
          span.textContent = '...';
          span.style.margin = '0 4px';
          paginacao.appendChild(span);
        } else {
          const btn = document.createElement('button');
          btn.textContent = p;
          if (p === paginaAtual) btn.classList.add('ativo');
          btn.onclick = () => {
            paginaAtual = p;
            atualizar();
          };
          paginacao.appendChild(btn);
        }
      });

      const btnProx = document.createElement('button');
      btnProx.innerHTML = '&raquo;';
      btnProx.disabled = paginaAtual === totalPaginas;
      btnProx.onclick = () => {
        paginaAtual++;
        atualizar();
      };
      paginacao.appendChild(btnProx);
    }

    function atualizar() {
      renderTabela();
      renderPaginacao();
    }

    // Filtro de busca
    document.getElementById('btn-buscar-log').addEventListener('click', function () {
      const termo = (document.getElementById('busca-log').value || '').toLowerCase();
      const dataFiltro = document.getElementById('data-log').value;
      logsFiltrados = logs.filter(log => {
        const usuarioMatch = log.usuario?.toLowerCase().includes(termo);
        const modMatch = log.modificacao?.toLowerCase().includes(termo);
        let dataOk = true;
        if (dataFiltro) {
          const [ano, mes, dia] = dataFiltro.split('-');
          const dataFormatada = `${dia}/${mes}/${ano}`;
          dataOk = log.data === dataFormatada;
        }
        return (!termo || usuarioMatch || modMatch) && dataOk;
      });
      paginaAtual = 1;
      atualizar();
    });

    document.getElementById('busca-log').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('btn-buscar-log').click();
      }
    });

    atualizar();
});
