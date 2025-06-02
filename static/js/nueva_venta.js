function agregarProducto() {
    const seleccionados = Array.from(document.querySelectorAll('select[name="producto_id[]"]'))
        .map(select => select.value);

    const productosDisponibles = window.productos_json || [];

    const opcionesFiltradas = productosDisponibles
        .filter(p => !seleccionados.includes(p.id.toString()))
        .map(p => `<option value="${p.id}">${p.nombre} - $${p.precio.toFixed(2)}</option>`)
        .join("");

    if (!opcionesFiltradas) {
        alert("No quedan más productos disponibles para añadir.");
        return;
    }

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
