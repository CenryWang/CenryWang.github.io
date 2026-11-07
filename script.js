// ===== 减少动态效果（尊重系统设置）=====
// CSS 已关闭过渡/动画，这里同步停掉粒子循环、打字机与光标光晕，
// 避免 prefers-reduced-motion 下 CPU 仍在每帧空转。
const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ===== 自定义光标光晕 =====
const glow = document.createElement("div");
glow.className = "cursor-glow";
document.body.appendChild(glow);
if (reduceMotion) glow.style.display = "none";
window.addEventListener("mousemove", (e) => {
  if (reduceMotion) return;
  glow.style.left = e.clientX + "px";
  glow.style.top = e.clientY + "px";
});
document.querySelectorAll("a, .btn, .social, .skill").forEach((el) => {
  el.addEventListener("mouseenter", () => {
    glow.style.width = "44px";
    glow.style.height = "44px";
  });
  el.addEventListener("mouseleave", () => {
    glow.style.width = "24px";
    glow.style.height = "24px";
  });
});

// ===== 主题切换（明暗）=====
const themeToggle = document.getElementById("themeToggle");
function getParticleRGB() {
  const v = getComputedStyle(document.documentElement).getPropertyValue("--particle").trim();
  const m = v.match(/rgba?\(([^)]+)\)/);
  if (!m) return { r: 120, g: 180, b: 255 };
  const p = m[1].split(",").map((s) => parseFloat(s));
  return { r: p[0], g: p[1], b: p[2] };
}
let particleColor = getComputedStyle(document.documentElement).getPropertyValue("--particle").trim() || "rgba(120,180,255,0.7)";
let PRGB = getParticleRGB();
function updateParticleColor() {
  particleColor = getComputedStyle(document.documentElement).getPropertyValue("--particle").trim() || particleColor;
  PRGB = getParticleRGB();
  if (reduceMotion) drawParticles();
}
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const next = isLight ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
    updateParticleColor();
  });
}

// ===== 粒子背景 =====
const canvas = document.getElementById("particles");
// 404 / digest 等生成页没有粒子画布：不判空会在这些页面直接抛错，
// 导致后面的 IntersectionObserver、页脚年份等逻辑全部中断。
const ctx = canvas ? canvas.getContext("2d") : null;
let particles = [];

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function initParticles() {
  if (!canvas) return;
  particles = [];
  const count = Math.min(90, Math.floor(window.innerWidth / 16));
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
    });
  }
}

function drawParticles() {
  if (!canvas || !ctx) return;
  // 标签页不可见时跳过绘制，但保留 rAF 以便切回来继续
  if (document.hidden) {
    if (!reduceMotion) requestAnimationFrame(drawParticles);
    return;
  }
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    if (!reduceMotion) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    }

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = particleColor;
    ctx.fill();

    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j];
      const dx = p.x - q.x;
      const dy = p.y - q.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 120) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.strokeStyle = "rgba(" + PRGB.r + ", " + PRGB.g + ", " + PRGB.b + ", " + 0.12 * (1 - dist / 120) + ")";
        ctx.lineWidth = 0.6;
        ctx.stroke();
      }
    }
  }
  if (!reduceMotion) requestAnimationFrame(drawParticles);
}

resizeCanvas();
initParticles();
drawParticles();
window.addEventListener("resize", () => {
  resizeCanvas();
  initParticles();
  if (reduceMotion) drawParticles();
});

// ===== 打字机 =====
const typedEl = document.getElementById("typed");
if (typedEl && reduceMotion) {
  typedEl.textContent = "创作者 · 开发者 · 开拓者";
  const c = document.querySelector(".cursor");
  if (c) c.style.display = "none";
}
if (typedEl && !reduceMotion) {
  const words = ["创作者", "开发者", "开拓者"];
  let wi = 0;
  let ci = 0;
  let deleting = false;

  function typeLoop() {
    const w = words[wi];
    if (!deleting) {
      typedEl.textContent = w.slice(0, ++ci);
      if (ci === w.length) {
        deleting = true;
        setTimeout(typeLoop, 1400);
        return;
      }
    } else {
      typedEl.textContent = w.slice(0, --ci);
      if (ci === 0) {
        deleting = false;
        wi = (wi + 1) % words.length;
      }
    }
    setTimeout(typeLoop, deleting ? 60 : 110);
  }
  typeLoop();
}

// ===== 顶部滚动进度条 =====
window.addEventListener("scroll", () => {
  const bar = document.getElementById("scrollProgress");
  if (!bar) return;
  const h = document.documentElement;
  const scrolled = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
  bar.style.width = scrolled + "%";
});

// ===== 页脚年份自动更新（跨年不用手工改）=====
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ===== 滚动揭示动画 =====
const io = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) e.target.classList.add("visible");
    });
  },
  { threshold: 0.15 }
);
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
