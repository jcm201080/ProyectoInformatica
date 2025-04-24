document.addEventListener("DOMContentLoaded", () => {
    fetch("/graficas/ventas_por_cliente")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("ventasClienteChart").getContext("2d");

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.clientes,
                    datasets: [{
                        label: "Ventas totales (€)",
                        data: data.totales,
                        backgroundColor: data.clientes.map(() => obtenerColorAleatorio()),
                        borderColor: "rgba(255, 159, 64, 1)",
                        borderWidth: 1
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
        .catch(error => console.error("Error al cargar ventas por cliente:", error));
});
