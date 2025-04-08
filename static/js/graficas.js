function obtenerColorAleatorio() {
    const r = Math.floor(Math.random() * 155);
    const g = Math.floor(Math.random() * 155);
    const b = Math.floor(Math.random() * 155);
    return `rgba(${r}, ${g}, ${b}, 0.5)`; // Transparencia de 0.5 para mejor visualización
}
