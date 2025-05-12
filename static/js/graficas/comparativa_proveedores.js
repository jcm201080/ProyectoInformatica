document.addEventListener("DOMContentLoaded", () => {
    fetch("/graficas/comparativa_proveedores")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("comparativaProveedoresChart").getContext("2d");

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.proveedores,
                    datasets: [
                        {
                            label: 'Comprado',
                            data: data.compras,
                            backgroundColor: "rgba(255, 99, 132, 0.6)"
                        },
                        {
                            label: 'Vendido',
                            data: data.ventas,
                            backgroundColor: "rgba(54, 162, 235, 0.6)"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
});
