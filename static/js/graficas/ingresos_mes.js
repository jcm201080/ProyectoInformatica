document.addEventListener("DOMContentLoaded", () => {
    fetch("/graficas/ingresos_por_mes")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("ingresosMesChart").getContext("2d");

            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.meses.map(mes => nombreMes(mes)),
                    datasets: [{
                        label: "Ingresos (€)",
                        data: data.ingresos,
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        })
        .catch(error => console.error("Error al cargar ingresos por mes:", error));
});

// Utilidad para traducir número de mes
function nombreMes(numero) {
    const meses = {
        "01": "Enero", "02": "Febrero", "03": "Marzo",
        "04": "Abril", "05": "Mayo", "06": "Junio",
        "07": "Julio", "08": "Agosto", "09": "Septiembre",
        "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    };
    return meses[numero] || numero;
}
