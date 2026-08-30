// ===== 自定义光标光晕 =====
const glow = document.createElement("div");
glow.className = "cursor-glow";
document.body.appendChild(glow);
window.addEventListener("mousemove", (e) => {
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

// ===== 粒子背景 =====
const canvas = document.getElementById("particles");
const ctx = canvas.getContext("2d");
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function initParticles() {
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
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(120, 180, 255, 0.7)";
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
        ctx.strokeStyle = "rgba(120, 180, 255, " + 0.12 * (1 - dist / 120) + ")";
        ctx.lineWidth = 0.6;
        ctx.stroke();
      }
    }
  }
  requestAnimationFrame(drawParticles);
}

resizeCanvas();
initParticles();
drawParticles();
window.addEventListener("resize", () => {
  resizeCanvas();
  initParticles();
});

// ===== 打字机 =====
const typedEl = document.getElementById("typed");
const words = ["浙大26届", "农业具身智能", "农业机器人", "ENTJ"];
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

// ===== 顶部滚动进度条 =====
window.addEventListener("scroll", () => {
  const h = document.documentElement;
  const scrolled = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
  document.getElementById("scrollProgress").style.width = scrolled + "%";
});

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
