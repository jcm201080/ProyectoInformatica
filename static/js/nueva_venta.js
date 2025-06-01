
function agregarProducto() {
    // Obtener productos ya seleccionados
    const seleccionados = Array.from(document.querySelectorAll('select[name="producto_id[]"]'))
        .map(select => select.value);

    // Lista de productos disponibles (desde el backend en JSON)
    const productosDisponibles = {{ productos_json | tojson }};

    // Filtrar los productos que no han sido seleccionados
    const opcionesFiltradas = productosDisponibles
        .filter(p => !seleccionados.includes(p.id.toString()))
        .map(p => `<option value="${p.id}">${p.nombre} - $${p.precio.toFixed(2)}</option>`)
        .join("");

    if (!opcionesFiltradas) {
        alert("No quedan más productos disponibles para añadir.");
        return;
    }

    // Crear el contenedor del nuevo producto
    const div = document.createElement('div');
    div.classList.add('producto');

    div.innerHTML = `
        <select name="producto_id[]">${opcionesFiltradas}</select>
        <input type="number" name="cantidad[]" min="1" value="1">
        <button type="button" onclick="eliminarProducto(this)" class="btn btn-delete">🗑️ Producto</button>
    `;

    document.getElementById('productos').appendChild(div);
}

function eliminarProducto(btn) {
    btn.parentElement.remove();
}
