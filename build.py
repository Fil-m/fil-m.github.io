#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерує index.html — повний каталог Fil-m: живі сторінки GitHub Pages,
їхні підсторінки та репозиторії без опублікованої сторінки.

Джерело істини — GitHub API + живі сторінки. Нові репозиторії
підхоплюються автоматично (щотижневий Action).
"""
import datetime
import html
import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
USER = "Fil-m"
BASE = f"https://{USER.lower()}.github.io"
SELF_REPO = f"{USER.lower()}.github.io"

CATS = {
    "games": ("Ігри", "#7c9cff"),
    "community": ("Спільнота", "#4fd1a5"),
    "kids": ("Анімація й діти", "#ffb454"),
    "creative": ("Творчість", "#e07bff"),
    "tools": ("Інструменти", "#5ec8e5"),
}

# name -> (category, title, опис)
CURATED = {
    "pixel-flow": ("games", "Pixel Flow", "Головоломка в стилі Pixel Flow: заливаєш клітинки кольором, поки не збереш малюнок. Плюс генератор рівнів із власних фото."),
    "element-game": ("games", "Element World", "Element World — пісочниця, де з чотирьох стихій збираються нові елементи."),
    "context": ("games", "CONTEXT v3 — Тіло", "CONTEXT v3 «Тіло»: три слоти, збірка як рух, довгий тап — розібрати."),
    "ReGo": ("games", "SYNERGY: PHASE SHIFT 3D", "SYNERGY: PHASE SHIFT — 3D-шутер у браузері на Node + WebSocket, із живими кімнатами."),
    "recoil-game": ("games", "Recoil Gun", "Recoil Gun — аркада, де пістолетом керує фізика віддачі: лети, крутись, збивай ворогів."),
    "bitsprite": ("games", "КАБАЛОК — Кристал", "КАБАЛОК — Кристал: маленький піксельний експеримент."),
    "kids-games": ("games", "Дитячі ігри", "Дитячі навчальні ігри: абетка, цифри, рахунок, кольори. Великі кнопки, без реклами."),
    "mine-avatar-hub": ("games", "Mine & Craft Avatar Hub", "Mine & Craft Avatar Hub — безсерверна ігрова екосистема з аватарами й локальним збереженням."),
    "habitat-os-test": ("games", "Habitat OS — тест", "Habitat OS — тестовий майданчик платформи: Match-3, чат через Git, магазин, скіни."),
    "habitat-os-workshop": ("games", "Habitat OS — майстерня", "Майстерня Habitat OS — робоча версія платформи для збірки й експериментів."),
    "aim-lab-scientist": ("games", "NeuroAim Lab", "NeuroAim Lab — тренажер прицілювання з науковим підходом: заміри, серії, статистика."),

    "spilnota": ("community", "Спільнота", "Спільнота — соцмережа в стилі ВК 2013. Без сервера: дані живуть у JSON-файлах репозиторію."),
    "--braves": ("community", "Infinity Braves", "Infinity Braves — група підтримки для нейровідмінних дорослих. Скринінг трьома мовами."),
    "WUW": ("community", "Кіноразом", "Кіноразом — дивимось відео разом: синхронний перегляд і чат."),
    "art-picnic": ("community", "Арт Пікнік", "Арт Пікнік — щомісячна безкоштовна зустріч для родин: знімаємо кліп або стопмоушен."),
    "diya-do-mriyi": ("community", "Дія до мрії", "Дія до мрії — «Ходімо. Зараз перевіримо»: путівник від наміру до першого кроку."),

    "animation-workshop": ("kids", "Анімаційна майстерня", "Безкоштовна stop-motion майстерня для батьків і дітей у Карлсруе, дві суботи на місяць."),
    "animation-trial": ("kids", "Пробне заняття з анімації", "За 60–90 хвилин дитина з батьками придумує історію, героїв і знімає перші кадри."),
    "animation_mentors": ("kids", "Менторство з анімації", "Менторство для дітей 7–18 років: підготовка до фестивалів, ADHD-friendly підхід."),

    "flow-path": ("creative", "Шлях Потоку", "Шлях Потоку — світогляд, що бачить світ як процес: без бога-творця, без догм."),
    "flow-editor": ("creative", "Flow Edit", "Flow Edit — міні-редактор відео для «Шляху Потоку»: таймлайн і CSS-візуали."),
    "portfolio-page": ("creative", "Портфоліо", "Персональна сторінка Тараса Москаленка: хто я, що роблю, як зв'язатися."),
    "Memology-Website-UA": ("creative", "МЕМОЛОГІЯ", "МЕМОЛОГІЯ: Сингулярність — пентологія про майбутнє, людей і машини."),

    "exchange-scanner": ("tools", "Exchange Scanner", "Аналіз валютних пар і торгових стратегій в одному екрані."),
    "exchange-scanner-beta": ("tools", "Exchange Scanner BETA", "Бета Exchange Scanner — нові пари й експериментальні стратегії."),
    "akira-mental-math": ("tools", "Akira — ментальна арифметика", "Akira — генератор вправ з ментальної арифметики на абакусі."),
    "hermonoid": ("tools", "Hermonoid", "Hermonoid — веб-чат для Hermes Agent на Android."),
    "stina-3d": ("tools", "Стіна 3D", "Стіна 3D — бюджетна волонтерська ферма 3D-друку в Карлсруе."),
}

SKIP_EXT = re.compile(r"\.(css|js|png|jpe?g|svg|ico|webp|woff2?|ttf|mp3|mp4|json|xml|txt|pdf|zip|webmanifest)$", re.I)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Fil-m-pages-hub"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch(url, limit=200000):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.geturl(), r.read(limit).decode("utf-8", "ignore")


def subpages(final, raw):
    """Внутрішні сторінки, на які веде головна (глибина 1)."""
    base = final if final.endswith("/") else final.rsplit("/", 1)[0] + "/"
    out = []
    for m in re.finditer(r'''href=["']([^"'#?]+)["']''', raw, re.I):
        u = urllib.parse.urljoin(final, m.group(1)).split("?")[0].split("#")[0]
        if not u.startswith(base) or u == final or SKIP_EXT.search(u):
            continue
        if u.rstrip("/") == base.rstrip("/"):
            continue
        if u not in out:
            out.append(u)
    return out[:8]


def probe(repo):
    name = repo["name"]
    urls = [u for u in [repo.get("homepage")] if u] + [f"{BASE}/{name}/"]
    last = None
    for u in urls:
        try:
            code, final, raw = fetch(u)
            title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
            desc = (
                re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', raw, re.S | re.I)
                or re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']', raw, re.S | re.I)
                or re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', raw, re.S | re.I)
            )
            clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip() if s else ""
            return {
                "name": name, "url": final, "status": code,
                "title": clean(title.group(1)) if title else "",
                "meta": clean(desc.group(1)) if desc else "",
                "repo_desc": repo.get("description") or "",
                "updated": (repo.get("updated_at") or "")[:10],
                "subs": subpages(final, raw),
            }
        except Exception as e:
            last = {"name": name, "url": u, "status": 0, "err": type(e).__name__,
                    "title": "", "meta": "", "repo_desc": repo.get("description") or "",
                    "updated": (repo.get("updated_at") or "")[:10], "subs": []}
    return last


def collect():
    repos = get_json(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
    repos = [r for r in repos if r["name"] != SELF_REPO]
    cand = [r for r in repos if r.get("has_pages") or r.get("homepage")]
    with ThreadPoolExecutor(max_workers=10) as ex:
        probed = [p for p in ex.map(probe, cand) if p]
    by_name = {p["name"]: p for p in probed}
    live, dead = [], []
    for r in repos:
        p = by_name.get(r["name"])
        if p and p.get("status") == 200:
            live.append(p)
        else:
            dead.append({
                "name": r["name"],
                "desc": r.get("description") or "Без опису",
                "updated": (r.get("updated_at") or "")[:10],
                "lang": r.get("language") or "",
            })
    return live, dead


def short(url, base):
    tail = url[len(base):] if url.startswith(base) else url
    return tail.rstrip("/") or "index"


def build(live, dead):
    cards = []
    for p in live:
        name = p["name"]
        if name in CURATED:
            cat, title, desc = CURATED[name]
        else:
            cat = "tools"
            title = p.get("title") or name
            desc = p.get("repo_desc") or p.get("meta") or "Сторінка проєкту на GitHub Pages."
        cards.append({
            "name": name, "title": title, "desc": desc, "cat": cat,
            "url": p.get("url") or f"{BASE}/{name}/",
            "repo": f"https://github.com/{USER}/{name}",
            "upd": p.get("updated", ""), "subs": p.get("subs") or [],
        })

    order = {k: i for i, k in enumerate(CATS)}
    cards.sort(key=lambda c: (order.get(c["cat"], 99), c["name"].lower()))
    dead.sort(key=lambda d: d["name"].lower())

    esc = lambda s: html.escape(str(s), quote=True)
    blocks = []
    for c in cards:
        cat_name, color = CATS.get(c["cat"], CATS["tools"])
        subs = ""
        if c["subs"]:
            links = " · ".join(
                f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(short(u, c["url"]))}</a>'
                for u in c["subs"]
            )
            subs = f'<div class="subs">ще сторінки: {links}</div>'
        blocks.append(f"""
    <article class="card" data-cat="{c['cat']}" data-search="{esc((c['title'] + ' ' + c['desc'] + ' ' + c['name']).lower())}">
      <div class="top"><span class="dot" style="--c:{color}"></span>
        <span class="cat" style="color:{color}">{esc(cat_name)}</span>
        <span class="upd">{esc(c['upd'])}</span></div>
      <h2>{esc(c['title'])}</h2>
      <p>{esc(c['desc'])}</p>
      {subs}
      <div class="links">
        <a class="open" href="{esc(c['url'])}" target="_blank" rel="noopener">Відкрити →</a>
        <a class="gh" href="{esc(c['repo'])}" target="_blank" rel="noopener" title="Репозиторій">git</a>
      </div>
    </article>""")

    dead_rows = []
    for d in dead:
        dead_rows.append(f"""
      <a class="row" href="https://github.com/{USER}/{esc(d['name'])}" target="_blank" rel="noopener"
         data-search="{esc((d['name'] + ' ' + d['desc']).lower())}">
        <span class="rname">{esc(d['name'])}</span>
        <span class="rdesc">{esc(d['desc'])}</span>
        <span class="rmeta">{esc(d['lang'])} · {esc(d['updated'])}</span>
      </a>""")

    chips = [f'<button class="chip active" data-f="all">Усі · {len(cards)}</button>']
    for key, (nm, color) in CATS.items():
        n = sum(1 for c in cards if c["cat"] == key)
        chips.append(f'<button class="chip" data-f="{key}" style="--c:{color}">{esc(nm)} · {n}</button>')

    total_subs = sum(len(c["subs"]) for c in cards)
    today = datetime.date.today().isoformat()
    return f"""<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{USER} — усі сторінки</title>
<meta name="description" content="Повний каталог {USER}: живі сторінки GitHub Pages, підсторінки та репозиторії без опублікованої сторінки.">
<style>
  :root {{ --bg:#0c0e13; --card:#151922; --card2:#1b202b; --fg:#e9ecf3; --mut:#8b93a7; --acc:#7c9cff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:radial-gradient(1200px 600px at 20% -10%, #1a2340 0%, transparent 55%), var(--bg);
         color:var(--fg); font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif; }}
  header {{ padding:44px 20px 18px; max-width:1100px; margin:0 auto; }}
  .kicker {{ color:var(--mut); font-size:13px; letter-spacing:.14em; text-transform:uppercase; }}
  h1 {{ font-size:clamp(28px,6vw,44px); margin:8px 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--mut); max-width:680px; }}
  .stats {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
  .stat {{ background:var(--card); border:1px solid #232937; border-radius:12px; padding:10px 14px; font-size:14px; }}
  .stat b {{ color:var(--acc); font-size:18px; }}
  .search {{ margin:22px 0 10px; }}
  input {{ width:100%; padding:14px 16px; border-radius:14px; border:1px solid #262c3a; background:#0f131b;
           color:var(--fg); font-size:16px; outline:none; }}
  input:focus {{ border-color:var(--acc); }}
  .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 4px; }}
  .chip {{ background:var(--card); color:var(--fg); border:1px solid #232937; border-radius:999px;
           padding:8px 13px; font-size:14px; cursor:pointer; }}
  .chip.active {{ background:var(--card2); border-color:var(--acc); }}
  main {{ max-width:1100px; margin:0 auto; padding:14px 20px 30px;
          display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }}
  .card {{ background:linear-gradient(180deg,#161b24,#131720); border:1px solid #212836; border-radius:18px;
           padding:18px; display:flex; flex-direction:column; min-height:190px; transition:.15s; }}
  .card:hover {{ transform:translateY(-2px); border-color:#2f3a52; }}
  .top {{ display:flex; align-items:center; gap:8px; font-size:12px; }}
  .dot {{ width:8px; height:8px; border-radius:50%; background:var(--c); }}
  .cat {{ font-weight:600; }}
  .upd {{ margin-left:auto; color:#77839a; }}
  h2 {{ font-size:19px; margin:12px 0 6px; line-height:1.25; }}
  .card p {{ color:#aab2c4; margin:0; flex:1; font-size:14.5px; }}
  .subs {{ margin-top:10px; font-size:12.5px; color:#7d879c; line-height:1.7; }}
  .subs a {{ color:#9fb0d0; text-decoration:none; border-bottom:1px dotted #3a4459; }}
  .subs a:hover {{ color:var(--fg); }}
  .links {{ display:flex; align-items:center; gap:10px; margin-top:14px; }}
  .open {{ color:var(--acc); text-decoration:none; font-weight:600; font-size:14px; }}
  .open:hover {{ text-decoration:underline; }}
  .gh {{ margin-left:auto; color:#6d768a; text-decoration:none; font-size:12px; border:1px solid #2a3140;
        padding:4px 8px; border-radius:8px; }}
  .gh:hover {{ color:var(--fg); }}
  .empty {{ display:none; color:var(--mut); padding:40px 4px; grid-column:1/-1; text-align:center; }}
  .section {{ max-width:1100px; margin:0 auto; padding:26px 20px 0; }}
  .section h3 {{ font-size:18px; margin:0 0 4px; }}
  .section p.hint {{ color:var(--mut); margin:0 0 12px; font-size:14px; }}
  .rows {{ display:flex; flex-direction:column; gap:8px; }}
  .row {{ display:grid; grid-template-columns:220px 1fr auto; gap:12px; align-items:center;
          background:var(--card); border:1px solid #1f2532; border-radius:12px; padding:12px 14px;
          text-decoration:none; color:var(--fg); }}
  .row:hover {{ border-color:#2f3a52; }}
  .rname {{ font-weight:600; font-size:14px; }}
  .rdesc {{ color:#98a1b5; font-size:13.5px; }}
  .rmeta {{ color:#5f6879; font-size:12px; white-space:nowrap; }}
  footer {{ max-width:1100px; margin:0 auto; padding:30px 20px 50px; color:#77839a; font-size:13px; }}
  footer a {{ color:#7d879c; }}
  @media (max-width:640px) {{
    .row {{ grid-template-columns:1fr; gap:4px; }}
    .rmeta {{ display:none; }}
  }}
</style>
</head>
<body>
<header>
  <div class="kicker">github.io</div>
  <h1>Усі сторінки</h1>
  <p class="sub">Повний каталог: живі сайти на GitHub Pages, їхні внутрішні сторінки
  і репозиторії, які ще не опубліковані як сторінка.</p>
  <div class="stats">
    <div class="stat"><b>{len(cards)}</b> живих сайтів</div>
    <div class="stat"><b>{len(cards) + total_subs}</b> сторінок усього</div>
    <div class="stat"><b>{len(dead)}</b> репо без сторінки</div>
  </div>
  <div class="search"><input id="q" type="search" placeholder="Пошук: назва, опис, тема…" autocomplete="off"></div>
  <div class="chips">{''.join(chips)}</div>
</header>
<main id="grid">
{''.join(blocks)}
  <div class="empty" id="empty">Нічого не знайдено. Спробуй інше слово.</div>
</main>

<section class="section" id="dead">
  <h3>Репозиторії без опублікованої сторінки · {len(dead)}</h3>
  <p class="hint">Код є, GitHub Pages не увімкнений (або сторінка не збирається). Клік веде в репозиторій.</p>
  <div class="rows" id="deadrows">
{''.join(dead_rows)}
  </div>
</section>

<footer>
  <p>Оновлено {today} · <a href="https://github.com/{USER}">github.com/{USER}</a> ·
  <a href="https://github.com/{USER}/{SELF_REPO}">код цієї сторінки</a></p>
</footer>
<script>
const cards=[...document.querySelectorAll('.card')];
const rows=[...document.querySelectorAll('.row')];
const q=document.getElementById('q'), empty=document.getElementById('empty'), dead=document.getElementById('dead');
let cat='all';
function apply(){{
  const s=q.value.trim().toLowerCase(); let n=0;
  cards.forEach(c=>{{
    const okCat = cat==='all' || c.dataset.cat===cat;
    const okQ = !s || c.dataset.search.includes(s);
    const show = okCat && okQ; c.style.display = show?'':'none'; if(show) n++;
  }});
  let m=0;
  rows.forEach(r=>{{
    const show = (!s || r.dataset.search.includes(s)) && cat==='all';
    r.style.display = show?'':'none'; if(show) m++;
  }});
  dead.style.display = m?'block':'none';
  empty.style.display = (n||m)?'none':'block';
}}
q.addEventListener('input',apply);
document.querySelectorAll('.chip').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.chip').forEach(x=>x.classList.remove('active'));
  b.classList.add('active'); cat=b.dataset.f; apply();
}}));
</script>
</body>
</html>
"""


def main():
    live, dead = collect()
    out = build(live, dead)
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(out)
    open(os.path.join(HERE, ".nojekyll"), "w").write("")
    json.dump({"live": live, "dead": dead}, open(os.path.join(HERE, "pages.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"index.html: {len(out)} байт · {len(live)} сайтів · {len(dead)} без сторінки")


if __name__ == "__main__":
    main()
