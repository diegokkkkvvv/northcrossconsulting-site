/* ===== North Cross — Front logic ===== */

// 1) Cambia esto por tu API pública (Render, Railway o Codespaces)
const API_BASE_URL = "https://northcross-api.onrender.com/consulta"; 
// Ej. Codespaces: "https://8000-xxxxx-xxxxx.githubpreview.dev/consulta"

const $ = (sel) => document.querySelector(sel);
const byId = (id) => document.getElementById(id);

byId("year").textContent = new Date().getFullYear();

function formatFraccion(value) {
  const digits = value.replace(/\D/g, "");
  if (digits.length === 8) return `${digits.slice(0,4)}.${digits.slice(4,6)}.${digits.slice(6,8)}`;
  // Permitir ####.##.## también
  const m = value.match(/^(\d{4})\.(\d{2})\.(\d{2})$/);
  return m ? value : value;
}

async function verificar(industria, fraccion) {
  const params = new URLSearchParams({ industria, fraccion: formatFraccion(fraccion) });
  const url = `${API_BASE_URL}?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Error HTTP ${res.status}`);
  return res.json();
}

byId("checkForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const industria = byId("industria").value.trim();
  const fraccion = byId("fraccion").value.trim();
  const resultBox = byId("resultBox");
  const resultPill = byId("resultPill");
  const resultNote = byId("resultNote");

  resultBox.classList.remove("hidden");
  resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-slate-200 text-slate-700";
  resultPill.textContent = "Consultando…";
  resultNote.textContent = "";

  if (!industria || !fraccion) {
    resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-yellow-100 text-yellow-800";
    resultPill.textContent = "Faltan datos";
    resultNote.textContent = "Selecciona industria e ingresa una fracción válida.";
    return;
  }

  try {
    const data = await verificar(industria, fraccion);

    if (data.requiere_aviso_automatico === true) {
      resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-red-100 text-red-800";
      resultPill.textContent = "✅ Requiere Aviso Automático";
      resultNote.textContent = "Podemos ayudarte a gestionarlo y liberar tu importación.";
    } else if (data.requiere_aviso_automatico === false) {
      resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-emerald-100 text-emerald-800";
      resultPill.textContent = "❌ No requiere Aviso Automático";
      resultNote.textContent = "Aun así, si tu importación está detenida, contáctanos.";
    } else {
      resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-slate-100 text-slate-700";
      resultPill.textContent = "⚠️ No encontrado";
      resultNote.textContent = "Revisa la fracción o contáctanos para verificarla manualmente.";
    }
  } catch (err) {
    resultPill.className = "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-orange-100 text-orange-800";
    resultPill.textContent = "Error de conexión";
    resultNote.textContent = "No pudimos consultar la API. Verifica tu URL pública en app.js.";
  }
});

// Contacto: fallback mailto si no usas Formspree
byId("mailtoFallback").addEventListener("click", (e) => {
  e.preventDefault();
  const f = byId("contactForm");
  const nombre = f.nombre.value || "";
  const ape = f.apellido.value || "";
  const empresa = f.empresa.value || "";
  const email = f.email.value || "";
  const msg = f.mensaje.value || "";
  const subject = encodeURIComponent(`Contacto — North Cross Consulting`);
  const body = encodeURIComponent(
    `Nombre: ${nombre} ${ape}\nEmpresa: ${empresa}\nEmail: ${email}\n\nMensaje:\n${msg}`
  );
  window.location.href = `mailto:management@northcrossconsulting.com?subject=${subject}&body=${body}`;
});
