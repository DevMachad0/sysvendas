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
}



document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('usuario').value;
        const senha = document.getElementById('senha').value;
        const resp = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({username, senha})
        });
        const data = await resp.json();
        if (data.success) {
            // Salva apenas os campos solicitados no localStorage
            const user = data.user;
            const userData = {
                _id: user._id, // Salva o id do usuário
                username: user.username,
                nome_vendedor: user.nome_vendedor,
                tipo: user.tipo,
                foto: user.foto,
                email: user.email,
                fone_vendedor: user.fone_vendedor,
                pos_vendas: user.pos_vendas,
                meta: user.meta_mes
            };
            localStorage.setItem('user', JSON.stringify(userData));

            // Envia log de login para o backend
            const now = new Date();
            const dataLog = now.toLocaleDateString('pt-BR');
            const hora = now.toLocaleTimeString('pt-BR');
            fetch('/api/inserir_log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                            },
                body: JSON.stringify({
                    data: dataLog,
                    hora: hora,
                    modificacao: 'Login realizado',
                    usuario: user.username
                })
            });
            enviarStorage(); // Envia os dados para o Flask
            if (user.tipo && user.tipo.toLowerCase() === 'vendedor') {
                window.location.href = '/vendas';
            } else {
                window.location.href = '/';
            }
        } else {
            alert(data.message || 'Login inválido');
        }
    });
});
