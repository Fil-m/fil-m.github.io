
// Живе доповнення каталогу: підтягує репозиторії, яких ще немає у статичному зліпку.
(() => {
  const API = "https://api.github.com/users/Fil-m/repos?per_page=100&sort=updated";
  const SELF = "fil-m.github.io";
  const COLORS = {games:["#7c9cff","Ігри"], community:["#4fd1a5","Спільнота"],
                  kids:["#ffb454","Анімація й діти"], creative:["#e07bff","Творчість"],
                  tools:["#5ec8e5","Інструменти"], code:["#8b93a7","Без сторінки"]};
  const grid = document.getElementById("grid"), empty = document.getElementById("empty");
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

  function addCard(r, pages) {
    const cat = pages && pages.length ? "tools" : (r.has_pages ? "tools" : "code");
    const [color, name] = COLORS[cat] || COLORS.tools;
    const title = r.name, desc = r.description || "Новий репозиторій";
    const url = r.has_pages ? `https://fil-m.github.io/${r.name}/` : r.homepage || `https://github.com/Fil-m/${r.name}`;
    const art = document.createElement("article");
    art.className = "card";
    art.dataset.cat = cat;
    art.dataset.search = (title + " " + desc + " " + r.name).toLowerCase();
    let pagesHtml = "";
    if (pages && pages.length) {
      pagesHtml = '<div class="pages"><span class="plabel">сторінки:</span> ' +
        pages.slice(0, 8).map(p => `<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.path)}</a>`).join(" ") + "</div>";
    }
    art.innerHTML =
      `<div class="top"><span class="dot" style="--c:${color}"></span>` +
      `<span class="cat" style="color:${color}">${esc(name)}</span>` +
      `<span class="badge">нове в GitHub</span><span class="upd">щойно</span></div>` +
      `<h2>${esc(title)}</h2><p>${esc(desc)}</p>${pagesHtml}` +
      `<div class="links"><a class="open" href="${esc(url)}" target="_blank" rel="noopener">` +
      `${pages && pages.length ? "Відкрити →" : "Репозиторій →"}</a></div>`;
    grid.insertBefore(art, empty);
    return art;
  }

  async function pagesOf(name) {
    try {
      const t = await fetch(`https://api.github.com/repos/Fil-m/${name}/git/trees/HEAD?recursive=1`).then(r => r.ok ? r.json() : null);
      if (!t || !t.tree) return [];
      return t.tree.filter(x => x.type === "blob" && /\.html$/i.test(x.path) && !/(^|\/)(node_modules|build|dist)(\/|$)/.test(x.path))
        .map(x => ({path: x.path, url: `https://fil-m.github.io/${name}/` + x.path.replace(/index\.html$/i, "")}));
    } catch (e) { return []; }
  }

  async function merge(fresh, max = 4) {
    for (const r of fresh.slice(0, max)) {
      const pages = r.has_pages ? await pagesOf(r.name) : [];
      addCard(r, pages);
    }
    document.getElementById("q").dispatchEvent(new Event("input"));
    window.__hubAdded = (window.__hubAdded || 0) + fresh.length;
  }

  async function run() {
    let state;
    try { state = await fetch("pages.json", {cache: "no-store"}).then(r => r.json()); }
    catch (e) { return; }
    const known = new Set([...(state.live || []).map(x => x.name), ...(state.dead || []).map(x => x.name), SELF]);
    let repos;
    const key = "hub_live_v1";
    try {
      const c = JSON.parse(sessionStorage.getItem(key) || "null");
      if (c && Date.now() - c.t < 5 * 60 * 1000) repos = c.d;
    } catch (e) {}
    if (!repos) {
      try {
        const r = await fetch(API, {headers: {Accept: "application/vnd.github+json"}});
        if (!r.ok) return;
        repos = await r.json();
        sessionStorage.setItem(key, JSON.stringify({t: Date.now(), d: repos}));
      } catch (e) { return; }
    }
    const fresh = repos.filter(r => !known.has(r.name) && r.name !== SELF);
    if (fresh.length) await merge(fresh);
  }

  window.__hubMerge = merge;   // для перевірки
  run();
})();
