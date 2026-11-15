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

// ===== 你的人生一万天 =====
// 全程用 UTC 午夜做日历加减，避免本地时区夏令时导致结果差一天。
// 本脚本被全站多页复用，因此先判空：没有这个表单的页面直接跳过。
(function () {
  const form = document.getElementById("daysForm");
  if (!form) return;

  const input = document.getElementById("daysInput");
  const errorEl = document.getElementById("daysError");
  const resultEl = document.getElementById("daysResult");
  const byId = (id) => document.getElementById(id);
  const DAY = 86400000;
  const WEEKDAYS = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];

  // 以用户所在时区的「今天」为准，转成 UTC 午夜时间戳
  function todayUTC() {
    const n = new Date();
    return Date.UTC(n.getFullYear(), n.getMonth(), n.getDate());
  }
  function fmtDate(d) {
    return d.getUTCFullYear() + " 年 " + (d.getUTCMonth() + 1) + " 月 " + d.getUTCDate() + " 日";
  }
  function fmtNum(n) {
    return n.toLocaleString("zh-CN");
  }

  // 返回值：成功 { date, time }，失败 { error: 提示语 }
  function parseBirth(raw) {
    const s = String(raw || "").trim().replace(/\s+/g, "");
    if (!s) return { error: "请输入出生日期，例如 2000-01-01" };

    // 允许 2000-01-01 / 2000/1/1 / 2000.1.1 / 2000年1月1日 / 20000101
    let m = s.match(/^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$/);
    if (!m) m = s.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (!m) return { error: "日期格式不正确，请按 2000-01-01 这样的格式输入" };

    const y = +m[1], mo = +m[2], d = +m[3];
    if (y < 1900) return { error: "请输入 1900 年之后的出生日期" };
    if (mo < 1 || mo > 12 || d < 1 || d > 31) {
      return { error: "这个日期不存在，请检查月份和日期" };
    }

    const t = Date.UTC(y, mo - 1, d);
    const date = new Date(t);
    // Date.UTC 会自动把 2023-02-30 滚到 3 月，用回读比对挡掉这种「假日期」
    if (date.getUTCFullYear() !== y || date.getUTCMonth() !== mo - 1 || date.getUTCDate() !== d) {
      return { error: "这个日期不存在，请检查月份和日期（例如没有 2 月 30 日）" };
    }
    if (t > todayUTC()) {
      return { error: "出生日期不能晚于今天（" + fmtDate(new Date(todayUTC())) + "）" };
    }
    return { date: date, time: t };
  }

  function clearError() {
    errorEl.textContent = "";
    errorEl.hidden = true;
    input.removeAttribute("aria-invalid");
    input.classList.remove("days-input--invalid");
  }
  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = false;
    input.setAttribute("aria-invalid", "true");
    input.classList.add("days-input--invalid");
    resultEl.hidden = true;
  }

  function render(parsed) {
    const birth = parsed.date;
    // 出生当天记为第 1 天，则第 10000 天 = 出生 + 9999 天
    const target = new Date(parsed.time + 9999 * DAY);
    const alt = new Date(parsed.time + 10000 * DAY);

    // 届时年龄：按日历整年整月估算
    let years = target.getUTCFullYear() - birth.getUTCFullYear();
    let months = target.getUTCMonth() - birth.getUTCMonth();
    if (target.getUTCDate() < birth.getUTCDate()) months -= 1;
    if (months < 0) { years -= 1; months += 12; }

    const nowDay = Math.floor((todayUTC() - parsed.time) / DAY) + 1; // 今天是第几天
    const left = 10000 - nowDay;
    const pct = Math.max(0, Math.min(100, (nowDay / 10000) * 100));

    byId("daysDate").textContent = fmtDate(target);
    byId("daysSub").textContent = WEEKDAYS[target.getUTCDay()] + " · 届时约 " + years + " 岁 " + months + " 个月";
    byId("daysProgressLabel").textContent = "今天是第 " + fmtNum(nowDay) + " 天 / 共 10,000 天";
    byId("daysProgressPct").textContent = pct.toFixed(1) + "%";
    byId("daysFill").style.width = pct + "%";
    byId("daysCaption").textContent =
      left > 0 ? "距离那一天还有 " + fmtNum(left) + " 天" :
      left < 0 ? "那一天已经过去 " + fmtNum(-left) + " 天" :
      "就是今天，第 10000 天快乐！";
    byId("daysAlt").textContent = fmtDate(alt);
    resultEl.hidden = false;
  }

  // 输入过程中：格式合法就即时出结果，没写完时静默等待，不闪错误提示
  input.addEventListener("input", () => {
    clearError();
    const parsed = parseBirth(input.value);
    if (parsed.date) render(parsed);
    else resultEl.hidden = true;
  });
  // 失焦时若已输入内容但仍不合法，给出明确提示
  input.addEventListener("blur", () => {
    if (!input.value.trim()) return;
    const parsed = parseBirth(input.value);
    if (!parsed.date) showError(parsed.error);
  });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const parsed = parseBirth(input.value);
    if (!parsed.date) {
      showError(parsed.error);
      input.focus();
      return;
    }
    clearError();
    render(parsed);
  });
})();
