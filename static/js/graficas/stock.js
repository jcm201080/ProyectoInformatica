document.addEventListener("DOMContentLoaded", () => {
    fetch("/graficas/stock_productos")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("stockChart").getContext("2d");

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.nombres,
                    datasets: [{
                        label: "Stock actual",
                        data: data.stocks,
                        backgroundColor: data.nombres.map(() => obtenerColorAleatorio()),
                        borderColor: "rgba(75, 192, 192, 1)",
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
        .catch(error => console.error("Error al cargar gráfica de stock:", error));
});
