document.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.target.id === 'progress-status') {
    const container = event.detail.target;

    // Efecto visual: parpadeo cambio rápido de color
    container.style.transition = 'background-color 0.4s ease';
    container.style.backgroundColor = '#e0f7fa';  // color claro para el flash
    setTimeout(() => {
      container.style.backgroundColor = ''; // vuelve a normal
    }, 400);

    const completed = container.querySelector('.completed-message');

    if (completed) {
      clearInterval(pollingInterval);
      console.log('Polling detenido: tarea completada');

      const stopMsg = document.createElement('div');
      stopMsg.textContent = '✅ Polling detenido: tarea completada';
      stopMsg.style.color = 'green';
      stopMsg.style.fontWeight = 'bold';
      stopMsg.style.marginTop = '0.5rem';
      container.appendChild(stopMsg);
    }
  }
});