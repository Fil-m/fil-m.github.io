#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерує index.html — хаб усіх сторінок Fil-m на github.io.

Джерело істини — GitHub API + живі сторінки. Нові репозиторії з увімкненим
Pages підхоплюються автоматично; для відомих є ручні назви й описи.
Запускається локально або щотижня через .github/workflows/update.yml.
"""
import datetime
import html
import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
USER = "Fil-m"
BASE = f"https://{USER.lower()}.github.io"

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


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Fil-m-pages-hub"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def probe(repo):
    name = repo["name"]
    urls = [u for u in [repo.get("homepage")] if u] + [f"{BASE}/{name}/"]
    last = None
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                code, final = r.status, r.geturl()
                raw = r.read(150000).decode("utf-8", "ignore")
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
            }
        except Exception as e:
            last = {"name": name, "url": u, "status": 0, "err": type(e).__name__,
                    "title": "", "meta": "", "repo_desc": repo.get("description") or "",
                    "updated": (repo.get("updated_at") or "")[:10]}
    return last


def collect():
    repos = get_json(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
    self_repo = f"{USER.lower()}.github.io"
    todo = [r for r in repos if (r.get("has_pages") or r.get("homepage")) and r["name"] != self_repo]
    with ThreadPoolExecutor(max_workers=10) as ex:
        got = [x for x in ex.map(probe, todo) if x and x.get("status") == 200]
    return got


def build(pages):
    cards = []
    for p in pages:
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
            "upd": p.get("updated", ""),
        })

    order = {k: i for i, k in enumerate(CATS)}
    cards.sort(key=lambda c: (order.get(c["cat"], 99), c["name"].lower()))

    esc = lambda s: html.escape(str(s), quote=True)
    blocks = []
    for c in cards:
        cat_name, color = CATS.get(c["cat"], CATS["tools"])
        blocks.append(f"""
    <article class="card" data-cat="{c['cat']}" data-search="{esc((c['title'] + ' ' + c['desc'] + ' ' + c['name']).lower())}">
      <div class="top"><span class="dot" style="--c:{color}"></span>
        <span class="cat" style="color:{color}">{esc(cat_name)}</span>
        <span class="upd">{esc(c['upd'])}</span></div>
      <h2>{esc(c['title'])}</h2>
      <p>{esc(c['desc'])}</p>
      <div class="links">
        <a class="open" href="{esc(c['url'])}" target="_blank" rel="noopener">Відкрити →</a>
        <a class="gh" href="{esc(c['repo'])}" target="_blank" rel="noopener" title="Репозиторій">git</a>
      </div>
    </article>""")

    chips = [f'<button class="chip active" data-f="all">Усі · {len(cards)}</button>']
    for key, (nm, color) in CATS.items():
        n = sum(1 for c in cards if c["cat"] == key)
        chips.append(f'<button class="chip" data-f="{key}" style="--c:{color}">{esc(nm)} · {n}</button>')

    today = datetime.date.today().isoformat()
    return f"""<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{USER} — усі сторінки</title>
<meta name="description" content="Хаб усіх проєктів і сторінок {USER} на github.io: ігри, спільнота, анімація, творчість, інструменти.">
<style>
  :root {{ --bg:#0c0e13; --card:#151922; --card2:#1b202b; --fg:#e9ecf3; --mut:#8b93a7; --acc:#7c9cff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:radial-gradient(1200px 600px at 20% -10%, #1a2340 0%, transparent 55%), var(--bg);
         color:var(--fg); font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif; }}
  header {{ padding:44px 20px 18px; max-width:1100px; margin:0 auto; }}
  .kicker {{ color:var(--mut); font-size:13px; letter-spacing:.14em; text-transform:uppercase; }}
  h1 {{ font-size:clamp(28px,6vw,44px); margin:8px 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--mut); max-width:640px; }}
  .search {{ margin:22px 0 10px; }}
  input {{ width:100%; padding:14px 16px; border-radius:14px; border:1px solid #262c3a; background:#0f131b;
           color:var(--fg); font-size:16px; outline:none; }}
  input:focus {{ border-color:var(--acc); }}
  .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 4px; }}
  .chip {{ background:var(--card); color:var(--fg); border:1px solid #232937; border-radius:999px;
           padding:8px 13px; font-size:14px; cursor:pointer; }}
  .chip.active {{ background:var(--card2); border-color:var(--acc); }}
  main {{ max-width:1100px; margin:0 auto; padding:14px 20px 60px;
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
  .links {{ display:flex; align-items:center; gap:10px; margin-top:14px; }}
  .open {{ color:var(--acc); text-decoration:none; font-weight:600; font-size:14px; }}
  .open:hover {{ text-decoration:underline; }}
  .gh {{ margin-left:auto; color:#6d768a; text-decoration:none; font-size:12px; border:1px solid #2a3140;
        padding:4px 8px; border-radius:8px; }}
  .gh:hover {{ color:var(--fg); }}
  .empty {{ display:none; color:var(--mut); padding:40px 4px; grid-column:1/-1; text-align:center; }}
  footer {{ max-width:1100px; margin:0 auto; padding:0 20px 50px; color:#77839a; font-size:13px; }}
  footer a {{ color:#7d879c; }}
</style>
</head>
<body>
<header>
  <div class="kicker">github.io</div>
  <h1>Усі сторінки</h1>
  <p class="sub">{len(cards)} живих проєктів: ігри, спільнота, анімація для дітей, творчість та інструменти.
  Усе — статичні сторінки на GitHub Pages, без бекенду.</p>
  <div class="search"><input id="q" type="search" placeholder="Пошук: назва, опис, тема…" autocomplete="off"></div>
  <div class="chips">{''.join(chips)}</div>
</header>
<main id="grid">
{''.join(blocks)}
  <div class="empty" id="empty">Нічого не знайдено. Спробуй інше слово.</div>
</main>
<footer>
  <p>Оновлено {today} · <a href="https://github.com/{USER}">github.com/{USER}</a> ·
  <a href="https://github.com/{USER}/{USER.lower()}.github.io">код цієї сторінки</a></p>
</footer>
<script>
const cards=[...document.querySelectorAll('.card')];
const q=document.getElementById('q'), empty=document.getElementById('empty');
let cat='all';
function apply(){{
  const s=q.value.trim().toLowerCase(); let n=0;
  cards.forEach(c=>{{
    const okCat = cat==='all' || c.dataset.cat===cat;
    const okQ = !s || c.dataset.search.includes(s);
    const show = okCat && okQ; c.style.display = show?'':'none'; if(show) n++;
  }});
  empty.style.display = n?'none':'block';
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
    pages = collect()
    out = build(pages)
    path = os.path.join(HERE, "index.html")
    open(path, "w", encoding="utf-8").write(out)
    open(os.path.join(HERE, ".nojekyll"), "w").write("")
    json.dump(pages, open(os.path.join(HERE, "pages.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"index.html: {len(out)} байт · {len(pages)} сторінок")


if __name__ == "__main__":
    main()
