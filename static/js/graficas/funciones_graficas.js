function obtenerColorAleatorio() {
    const r = Math.floor(Math.random() * 155);
    const g = Math.floor(Math.random() * 155);
    const b = Math.floor(Math.random() * 155);
    return `rgba(${r}, ${g}, ${b}, 0.5)`; // Transparencia de 0.5 para mejor visualización
}

function coloresAleatorios(n) {
  const colores = [];
  for (let i = 0; i < n; i++) {
    const color = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
    colores.push(color);
  }
  return colores;
}

// variables globales
let graficaMensual = null;

// función para inicializar los selectores
function inicializarSelectoresGrafica() {
  const selectorAnio = document.getElementById('selectorAnio');
  const selectorMes = document.getElementById('selectorMes');

  // Solo inicializar si los elementos existen (para páginas que no usan la gráfica)
  if (!selectorAnio || !selectorMes) return;

  // Generar opciones de años
  const anioActual = new Date().getFullYear();
  for (let i = 0; i <= 4; i++) {
    const anio = anioActual - i;
    const option = document.createElement('option');
    option.value = anio;
    option.textContent = anio;
    selectorAnio.appendChild(option);
  }

  // Establecer valores por defecto
  selectorAnio.value = anioActual;
  selectorMes.value = ('0' + (new Date().getMonth() + 1)).slice(-2);

  // Cargar datos iniciales
  cargarDatosGrafica();
}

// función principal para cargar los datos
async function cargarDatosGrafica() {
  const anio = document.getElementById('selectorAnio')?.value;
  const mes = document.getElementById('selectorMes')?.value;

  if (!anio || !mes) {
    console.log("Selecciona año y mes");
    return;
  }

  try {
    console.log(`Solicitando datos para ${mes}/${anio}`);

    const response = await fetch(`/api/ventas_por_mes?anio=${anio}&mes=${mes}`);
    if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

    const data = await response.json();

    if (!data.productos || !data.cantidades) {
      throw new Error("Datos incompletos en la respuesta");
    }

    // Destruir gráfica anterior si existe
    if (graficaMensual) {
      graficaMensual.destroy();
    }

    const ctx = document.getElementById('graficaMensual')?.getContext('2d');
    if (!ctx) return;

    graficaMensual = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.productos,
        datasets: [{
          label: `Ventas - ${mes}/${anio}`,
          data: data.cantidades,
          backgroundColor: data.productos.map(() =>
            `hsl(${Math.random() * 360}, 70%, 60%)`),
          borderColor: 'rgba(0,0,0,0.1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.parsed.y} unidades`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        }
      }
    });
  } catch (error) {
    console.error("Error al cargar datos:", error);
    // Puedes mostrar el error en un div en lugar de usar alert
    const errorDiv = document.getElementById('error-grafica');
    if (errorDiv) {
      errorDiv.textContent = `Error: ${error.message}`;
      errorDiv.style.display = 'block';
    }
  }
}

// Evento cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
  inicializarSelectoresGrafica();

  // Asignar eventos (por si acaso el HTML se carga dinámicamente)
  document.getElementById('selectorAnio')?.addEventListener('change', cargarDatosGrafica);
  document.getElementById('selectorMes')?.addEventListener('change', cargarDatosGrafica);
});


function cargarVentasPorMes(mes) {
  if (!mes) return;

  fetch(`/api/ventas_por_mes?mes=${mes}`)
    .then(res => res.json())
    .then(data => {
      if (!data.productos || !data.cantidades) {
        console.warn("No se recibieron datos válidos:", data);
        return;
      }

      // Destruir gráfica previa si existe
      if (window.graficaMensual) {
        window.graficaMensual.destroy();
      }

      const ctx = document.getElementById('graficaMensual').getContext('2d');
      window.graficaMensual = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.productos,
          datasets: [{
            label: 'Unidades Vendidas',
            data: data.cantidades,
            backgroundColor: coloresAleatorios(data.productos.length)
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: context => `${context.parsed.y} unidades`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error("❌ Error al obtener datos de ventas:", error);
    });
}
