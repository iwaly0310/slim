/* 宏謙健康減重指南 — site.js */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const hdr = $("[data-hdr]");
  const onScroll = () => hdr && hdr.classList.toggle("is-stuck", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  const btn = $("[data-menu]"), drawer = $("[data-drawer]");
  if (btn && drawer) {
    const icon = btn.innerHTML;
    const set = (open) => {
      btn.setAttribute("aria-expanded", String(open));
      drawer.hidden = !open;
      document.body.classList.toggle("menu-open", open);
      btn.innerHTML = open ? '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg><span class="sr">關閉選單</span>' : icon;
    };
    btn.addEventListener("click", () => set(btn.getAttribute("aria-expanded") !== "true"));
    addEventListener("keydown", (e) => { if (e.key === "Escape") set(false); });
    matchMedia("(min-width: 901px)").addEventListener("change", (m) => m.matches && set(false));
  }

  /* 文章目錄：三個以上小標才顯示 */
  const prose = $(".prose");
  if (prose) {
    const hs = $$("h2", prose);
    if (hs.length >= 3) {
      hs.forEach((h, i) => { if (!h.id) h.id = "s" + (i + 1); });
      const toc = document.createElement("nav");
      toc.className = "toc";
      toc.setAttribute("aria-label", "本文目錄");
      toc.innerHTML = `<p class="toc-t">本文內容</p><ol>${hs.map((h) => `<li><a href="#${h.id}">${h.textContent}</a></li>`).join("")}</ol>`;
      prose.parentNode.insertBefore(toc, prose);
    }
  }
})();
