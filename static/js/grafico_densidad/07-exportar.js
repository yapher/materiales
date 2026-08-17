(function () {
"use strict";

const GD = window.GraficoDensidad;
if (!GD) {
    return;
}

/*
Exportación del gráfico:
- descarga como PNG (usa el canvas actual, respeta los filtros)
- exportación a PDF (generado por el backend)
*/

GD.descargarPNG = function () {
    if (!GD.state.chartInstance) {
        return;
    }
    const url = GD.state.chartInstance.toBase64Image("image/png", 1.0);
    const a = document.createElement("a");
    a.href = url;
    a.download = `densidad_vs_temperatura_${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    if (window.mostrarToast) {
        window.mostrarToast(
            "Imagen descargada",
            "Gráfico guardado como PNG."
        );
    }
};

GD.exportarPDF = async function () {
    const mix = GD.getMezclaActual();
    if (!mix || mix.length === 0) {
        if (window.mostrarToast) {
            window.mostrarToast(
                "Error",
                "Necesitás una mezcla válida para exportar.",
                true
            );
        }
        return;
    }
    const total = mix.reduce((acc, e) => acc + (e.pct || 0), 0);
    if (Math.abs(total - 100) > 0.01) {
        if (window.mostrarToast) {
            window.mostrarToast(
                "Error",
                "La mezcla debe sumar 100% para exportar.",
                true
            );
        }
        return;
    }
    const { tempMin, tempMax, intervalo } = GD.getFormularioValores();
    if (isNaN(tempMin) || isNaN(tempMax) || isNaN(intervalo)) {
        if (window.mostrarToast) {
            window.mostrarToast(
                "Error",
                "Completá los parámetros del rango.",
                true
            );
        }
        return;
    }

    const btnPDF = GD.$("gdBtnPDF");
    if (btnPDF) {
        btnPDF.disabled = true;
    }
    if (window.mostrarToast) {
        window.mostrarToast(
            "Generando PDF",
            "Creando documento PDF...",
            false
        );
    }
    try {
        const respuesta = await fetch("/mezclas/grafico_densidad/pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mix,
                temp_min: tempMin,
                temp_max: tempMax,
                intervalo,
            }),
        });
        if (!respuesta.ok) {
            const data = await respuesta.json().catch(() => ({}));
            throw new Error(
                data.error || `Error ${respuesta.status}`
            );
        }
        const blob = await respuesta.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `densidad_vs_temperatura_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        if (window.mostrarToast) {
            window.mostrarToast(
                "PDF descargado",
                "El documento PDF fue generado correctamente."
            );
        }
    } catch (error) {
        if (window.mostrarToast) {
            window.mostrarToast(
                "Error al generar PDF",
                error.message,
                true
            );
        }
    } finally {
        if (btnPDF) {
            btnPDF.disabled = false;
        }
    }
};
})();