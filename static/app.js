(function () {
  const retiradaInput = document.getElementById('id_data_retirada');
  const previsao = document.getElementById('previsao');

  function atualizarPrevisao() {
    if (!retiradaInput || !previsao) {
      return;
    }

    if (!retiradaInput.value) {
      previsao.textContent = '';
      return;
    }

    const data = new Date(retiradaInput.value + 'T00:00:00');
    data.setDate(data.getDate() + 30);
    previsao.textContent = `Previsao de devolucao: ${data.toLocaleDateString('pt-BR')}`;
  }

  if (retiradaInput) {
    retiradaInput.addEventListener('change', atualizarPrevisao);
    atualizarPrevisao();
  }

  const filtroForm = document.getElementById('filtro-admin-form');
  ['id_status', 'id_serie', 'id_ordenacao'].forEach(function (id) {
    const campo = document.getElementById(id);
    if (campo && filtroForm) {
      campo.addEventListener('change', function () {
        filtroForm.submit();
      });
    }
  });

  const sidebar = document.getElementById('sidebar');
  const menuToggle = document.getElementById('menu-toggle');
  if (sidebar && menuToggle) {
    menuToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }
})();
