
**Desenvolvedores:**  
- Wellington Lima - Dev Jr  
- Deivid Machado - Dev Jr

---

## Visão Geral

**SysVendas** é um sistema completo para gestão e acompanhamento de vendas, equipes e metas comerciais. O sistema foi desenvolvido em Python utilizando Flask para o backend, MongoDB como banco de dados, e Plotly para geração de gráficos interativos e relatórios.

---

## Funcionalidades

- **Gestão de Usuários:**  
  Cadastro, edição e autenticação de usuários, incluindo diferentes perfis (admin, vendedor, pós-vendas, faturamento), com controle de permissões e edição de dados pessoais e metas.

- **Gestão de Produtos:**  
  Cadastro, edição e listagem de produtos com condições de pagamento personalizadas.

- **Gestão de Vendas:**  
  Cadastro, edição e listagem de vendas, incluindo campos completos do cliente, endereço, dados fiscais, produtos, condições e logs de alterações.

- **Metas e Limites:**  
  Cadastro e acompanhamento de metas diárias, semanais e mensais para vendedores, além de configuração de limites de desconto/condições especiais.

- **Dashboard Analítico:**  
  Diversos gráficos interativos com Plotly para acompanhamento de metas, vendas por período, status de vendas, resultados por vendedor, tipo de venda (nova ou atualização), e distribuição geográfica das vendas por estado.

- **Notificações Internas:**  
  Geração automática de notificações para eventos como cadastro ou edição de venda, alterações de status, envolvendo todos os perfis interessados (vendedor, pós-vendas, admin, faturamento).

- **Logs de Operações:**  
  Registro de logs detalhados de todas as modificações relevantes no sistema, com histórico acessível para auditoria.

- **Geração de Relatórios em PDF:**  
  Download de relatórios em PDF contendo os principais gráficos selecionados pelo usuário.

- **Segurança:**  
  - Autenticação por sessão (login_required)  
  - Hash de senha com bcrypt  
  - Controle de acesso por tipo de usuário  
  - Dados sensíveis e ações críticas devidamente protegidos

---

## Tecnologias & Técnicas

- **Backend:** Python (Flask)
- **Banco de Dados:** MongoDB (pymongo)
- **Frontend:** HTML + Jinja2 + JavaScript (com AJAX)
- **Visualização de Dados:** Plotly (Dashboards, gráficos interativos)
- **Relatórios:** ReportLab para geração de PDFs customizados
- **Emails:** Integração com SMTP para notificações e confirmações automáticas
- **Segurança:** Hash de senha (bcrypt), controle de sessão, validação de campos
- **Documentação e Organização:**  
  - Uso extensivo de docstrings e comentários em todo o código  
  - Separação clara entre camadas (rotas, serviços, modelos e gráficos)
  - Código modular e fácil de manter

---

## Observações

- O sistema é focado em empresas com equipes comerciais, facilitando o controle de metas, bonificações, acompanhamento de desempenho e transparência de informações.
- Todos os dados são estruturados para facilitar integrações futuras e análises gerenciais.
- Projeto construído com boas práticas de desenvolvimento Python/Flask e MongoDB.

---

*Para dúvidas técnicas, consulte os desenvolvedores ou leia as docstrings dentro dos arquivos do projeto.*

**SDG**
