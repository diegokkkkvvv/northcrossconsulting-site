// ========================================================
// North Cross Consulting — App Logic
// Handles: Verificador de Aviso Automático, Form, Animations
// Includes Google Analytics event tracking
// ========================================================

// --- Selectors ---
const selOrigen = document.getElementById("origen");
const selIndustria = document.getElementById("industria");
const inpCodigo = document.getElementById("codigo");
const boxResultado = document.getElementById("resultado");
const btnCheck = document.getElementById("btnCheck");

// --- API Endpoint (Render backend) ---
const API_URL = "https://api.northcrossconsulting.com/consulta";

// --- Helper Functions ---
function setLoading(state) {
  btnCheck.disabled = state;
  btnCheck.innerHTML = state ? '<span class="loading"></span>' : "Verificar requisitos";
}

function setResult({ type, text }) {
  boxResultado.textContent = text;
  boxResultado.className = `result-box ${type} show`;
}

function clearResult() {
  boxResultado.className = "result-box";
  boxResultado.textContent = "";
}

// --- Handle Origin Selection ---
selOrigen.addEventListener("change", () => {
  const label = document.getElementById("labelCodigo");
  if (selOrigen.value === "us") {
    label.textContent = "HTSUS (10 dígitos)";
    inpCodigo.placeholder = "Ej. 7208.10.00.30";
  } else {
    label.textContent = "Fracción TIGIE";
    inpCodigo.placeholder = "Ej. 7208.10.01";
  }
});

// --- Core Functionality: Consulta API ---
async function consultarAviso({ origin, industria, code }) {
  const url = `${API_URL}?origin=${encodeURIComponent(origin)}&industria=${encodeURIComponent(
    industria
  )}&code=${encodeURIComponent(code)}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error("Error en la conexión");
  return await response.json();
}

// --- Click Event: Verificar Requisitos ---
btnCheck.addEventListener("click", async () => {
  const origin = selOrigen?.value || "mx";
  const industria = selIndustria?.value || "";
  const code = inpCodigo?.value?.trim() || "";

  clearResult();

  if (!industria || industria === "Selecciona una industria") {
    setResult({ type: "neutral", text: "⚠️ Por favor selecciona una industria." });
    return;
  }

  if (!code) {
    setResult({ type: "neutral", text: "⚠️ Por favor ingresa un código TIGIE o HTSUS." });
    return;
  }

  try {
    setLoading(true);
    const data = await consultarAviso({ origin, industria, code });

    if (data?.requiere_aviso_automatico === true) {
      setResult({
        type: "ok",
        text: "✅ Sí requiere aviso automático. Podemos gestionarlo de inmediato.",
      });

      // --- Google Analytics custom event ---
      if (typeof gtag === "function") {
        gtag("event", "verificacion_exitosa", {
          event_category: "API",
          event_label: "Consulta Aviso Automático",
          value: 1,
          origin: origin,
          industria: industria,
          code: code,
        });
      }
    } else if (data?.requiere_aviso_automatico === false) {
      setResult({
        type: "bad",
        text: "❌ No requiere aviso automático para esta fracción.",
      });
    } else {
      setResult({
        type: "neutral",
        text: "⚠️ No se encontró información. Contáctanos para una consulta personalizada.",
      });
    }
  } catch (error) {
    console.error("Error:", error);
    setResult({
      type: "bad",
      text: "❌ Error al conectar con el servidor. Intenta nuevamente.",
    });
  } finally {
    setLoading(false);
  }
});

// --- Smooth Scroll for Internal Links ---
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (e) => {
    e.preventDefault();
    const target = document.querySelector(anchor.getAttribute("href"));
    if (target) {
      const headerOffset = 80;
      const elementPosition = target.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
      window.scrollTo({ top: offsetPosition, behavior: "smooth" });
    }
  });
});

// --- Intersection Observer for Fade-in Animations ---
const fadeElements = document.querySelectorAll(".advantage-card, .feature-item, .process-step, .mini-card");

const fadeObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  },
  { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
);

fadeElements.forEach((element) => {
  element.style.opacity = "0";
  element.style.transform = "translateY(30px)";
  element.style.transition = "opacity 0.6s ease, transform 0.6s ease";
  fadeObserver.observe(element);
});

// --- Hero Stats Counter Animation ---
const observerOptions = { threshold: 0.5 };
const heroStats = document.querySelector(".hero-stats");

const animateCounter = (element, target, suffix = "") => {
  const duration = 2000;
  const increment = target / (duration / 16);
  let current = 0;

  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target + suffix;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current) + suffix;
    }
  }, 16);
};

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting && !entry.target.classList.contains("counted")) {
      entry.target.classList.add("counted");
      const stats = entry.target.querySelectorAll(".stat-number");

      stats.forEach((stat) => {
        const text = stat.textContent;
        if (text.includes("+")) animateCounter(stat, 500, "+");
        else if (text.includes("%")) animateCounter(stat, 95, "%");
      });
    }
  });
}, observerOptions);

if (heroStats) statsObserver.observe(heroStats);

// --- Parallax Effect (Hero Section) ---
window.addEventListener("scroll", () => {
  const scrolled = window.pageYOffset;
  const heroContent = document.querySelector(".hero-content");
  if (heroContent && scrolled < window.innerHeight) {
    heroContent.style.transform = `translateY(${scrolled * 0.2}px)`;
    heroContent.style.opacity = Math.max(0.7, 1 - scrolled / 1200);
  }
});

// --- Scroll to Top Button ---
const scrollTop = document.getElementById("scrollTop");
window.addEventListener("scroll", () => {
  if (window.scrollY > 500) scrollTop.classList.add("show");
  else scrollTop.classList.remove("show");
});
scrollTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

// --- Contact Form Feedback Message ---
const contactForm = document.getElementById("contactForm");
const contactMsg = document.getElementById("contactMsg");

if (contactForm && contactMsg) {
  contactForm.addEventListener("submit", () => {
    contactMsg.textContent = "Enviando mensaje...";
    contactMsg.className = "form-message show";

    setTimeout(() => {
      contactMsg.textContent = "✓ ¡Gracias! Tu mensaje ha sido enviado.";
      contactMsg.className = "form-message success show";
    }, 1200);
  });
}

// --- Debug Branding ---
console.log("%c🚀 North Cross Consulting", "font-size: 22px; font-weight: bold; color: #0078D7;");
console.log("%cOptimización y automatización en comercio exterior México-USA", "font-size: 14px; color: #666;");
