#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генерує index.html — хаб усіх сторінок Fil-m на github.io."""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# name -> (category, опис)
CATS = {
    "games": ("Ігри", "#7c9cff"),
    "community": ("Спільнота", "#4fd1a5"),
    "kids": ("Анімація й діти", "#ffb454"),
    "creative": ("Творчість", "#e07bff"),
    "tools": ("Інструменти", "#5ec8e5"),
}

PAGES = {
    "pixel-flow": ("games", "Головоломка в стилі Pixel Flow: заливаєш клітинки кольором, поки не збереш малюнок. Плюс генератор рівнів із власних фото."),
    "element-game": ("games", "Element World — пісочниця, де з чотирьох стихій збираються нові елементи."),
    "context": ("games", "CONTEXT v3 «Тіло»: три слоти, збірка як рух, довгий тап — розібрати."),
    "ReGo": ("games", "SYNERGY: PHASE SHIFT — 3D-шутер у браузері на Node + WebSocket, із живими кімнатами."),
    "recoil-game": ("games", "Recoil Gun — аркада, де пістолетом керує фізика віддачі: лети, крутись, збивай ворогів."),
    "bitsprite": ("games", "КАБАЛОК — Кристал: маленький піксельний експеримент."),
    "kids-games": ("games", "Дитячі навчальні ігри: абетка, цифри, рахунок, кольори. Великі кнопки, без реклами."),
    "mine-avatar-hub": ("games", "Mine & Craft Avatar Hub — безсерверна ігрова екосистема з аватарами й локальним збереженням."),
    "habitat-os-test": ("games", "Habitat OS — тестовий майданчик платформи: Match-3, чат через Git, магазин, скіни."),
    "habitat-os-workshop": ("games", "Майстерня Habitat OS — робоча версія платформи для збірки й експериментів."),
    "aim-lab-scientist": ("games", "NeuroAim Lab — тренажер прицілювання з науковим підходом: заміри, серії, статистика."),

    "spilnota": ("community", "Спільнота — соцмережа в стилі ВК 2013. Без сервера: дані живуть у JSON-файлах репозиторію."),
    "--braves": ("community", "Infinity Braves — група підтримки для нейровідмінних дорослих. Скринінг трьома мовами."),
    "WUW": ("community", "Кіноразом — дивимось відео разом: синхронний перегляд і чат."),
    "art-picnic": ("community", "Арт Пікнік — щомісячна безкоштовна зустріч для родин: знімаємо кліп або стопмоушен."),
    "diya-do-mriyi": ("community", "Дія до мрії — «Ходімо. Зараз перевіримо»: путівник від наміру до першого кроку."),

    "animation-workshop": ("kids", "Безкоштовна stop-motion майстерня для батьків і дітей у Карлсруе, дві суботи на місяць."),
    "animation-trial": ("kids", "Пробне заняття: за 60–90 хвилин дитина з батьками придумує історію, героїв і знімає перші кадри."),
    "animation_mentors": ("kids", "Менторство з анімації для дітей 7–18 років: підготовка до фестивалів, ADHD-friendly підхід."),

    "flow-path": ("creative", "Шлях Потоку — світогляд, що бачить світ як процес: без бога-творця, без догм."),
    "flow-editor": ("creative", "Flow Edit — міні-редактор відео для «Шляху Потоку»: таймлайн і CSS-візуали."),
    "portfolio-page": ("creative", "Персональна сторінка Тараса Москаленка: хто я, що роблю, як зв'язатися."),
    "Memology-Website-UA": ("creative", "МЕМОЛОГІЯ: Сингулярність — пентологія про майбутнє, людей і машини."),

    "exchange-scanner": ("tools", "Аналіз валютних пар і торгових стратегій в одному екрані."),
    "exchange-scanner-beta": ("tools", "Бета Exchange Scanner — нові пари й експериментальні стратегії."),
    "akira-mental-math": ("tools", "Akira — генератор вправ з ментальної арифметики на абакусі."),
    "hermonoid": ("tools", "Hermonoid — веб-чат для Hermes Agent на Android."),
    "stina-3d": ("tools", "Стіна 3D — бюджетна волонтерська ферма 3D-друку в Карлсруе."),
}

TITLES_FALLBACK = {
    "--braves": "Infinity Braves",
    "context": "CONTEXT v3 — Тіло",
    "diya-do-mriyi": "Дія до мрії",
    "ReGo": "SYNERGY: PHASE SHIFT 3D",
}

probe = {p["name"]: p for p in json.load(open(os.path.join(HERE, "probe.json"), encoding="utf-8"))}

cards = []
for name, (cat, desc) in PAGES.items():
    p = probe.get(name, {})
    title = TITLES_FALLBACK.get(name) or p.get("title") or name
    title = re.sub(r"\s*[|—–]\s*$", "", title).strip()
    # прибираємо довгі хвости типу "— сторінка ..."
    if len(title) > 70:
        title = title[:67].rstrip() + "…"
    upd = (p.get("updated") or "")[:10]
    cards.append({
        "name": name, "title": title, "desc": desc, "cat": cat,
        "url": f"https://fil-m.github.io/{name}/",
        "repo": f"https://github.com/Fil-m/{name}",
        "upd": upd,
    })

order = {k: i for i, k in enumerate(CATS)}
cards.sort(key=lambda c: (order[c["cat"]], c["name"].lower()))

data_json = json.dumps(cards, ensure_ascii=False)


def esc(s):
    return html.escape(s, quote=True)


cards_html = []
for c in cards:
    cat_name, color = CATS[c["cat"]]
    cards_html.append(f"""
    <article class="card" data-cat="{c['cat']}" data-search="{esc((c['title'] + ' ' + c['desc'] + ' ' + c['name']).lower())}">
      <div class="top"><span class="dot" style="--c:{color}"></span>
        <span class="cat" style="color:{color}">{esc(cat_name)}</span>
        <span class="upd">{esc(c['upd'])}</span></div>
      <h2>{esc(c['title'])}</h2>
      <p>{esc(c['desc'])}</p>
      <div class="links">
        <a class="open" href="{c['url']}" target="_blank" rel="noopener">Відкрити →</a>
        <a class="gh" href="{c['repo']}" target="_blank" rel="noopener" title="Репозиторій">git</a>
      </div>
    </article>""")

filters = ['<button class="chip active" data-f="all">Усі · %d</button>' % len(cards)]
for key, (nm, color) in CATS.items():
    n = sum(1 for c in cards if c["cat"] == key)
    filters.append(f'<button class="chip" data-f="{key}" style="--c:{color}">{esc(nm)} · {n}</button>')

HTML = f"""<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fil-m — усі сторінки</title>
<meta name="description" content="Хаб усіх проєктів і сторінок Тараса Москаленка на github.io: ігри, спільнота, анімація, творчість, інструменти.">
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
  .upd {{ margin-left:auto; color:#5f6879; }}
  h2 {{ font-size:19px; margin:12px 0 6px; line-height:1.25; }}
  .card p {{ color:#aab2c4; margin:0; flex:1; font-size:14.5px; }}
  .links {{ display:flex; align-items:center; gap:10px; margin-top:14px; }}
  .open {{ color:var(--acc); text-decoration:none; font-weight:600; font-size:14px; }}
  .open:hover {{ text-decoration:underline; }}
  .gh {{ margin-left:auto; color:#6d768a; text-decoration:none; font-size:12px; border:1px solid #2a3140;
        padding:4px 8px; border-radius:8px; }}
  .gh:hover {{ color:var(--fg); }}
  .empty {{ display:none; color:var(--mut); padding:40px 4px; grid-column:1/-1; text-align:center; }}
  footer {{ max-width:1100px; margin:0 auto; padding:0 20px 50px; color:#5f6879; font-size:13px; }}
  footer a {{ color:#7d879c; }}
</style>
</head>
<body>
<header>
  <div class="kicker">github.io</div>
  <h1>Усі сторінки Філа</h1>
  <p class="sub">{len(cards)} живих проєктів: ігри, спільнота, анімація для дітей, творчість та інструменти.
  Усе — статичні сторінки на GitHub Pages, без бекенду.</p>
  <div class="search"><input id="q" type="search" placeholder="Пошук: назва, опис, тема…" autocomplete="off"></div>
  <div class="chips">{''.join(filters)}</div>
</header>
<main id="grid">
{''.join(cards_html)}
  <div class="empty" id="empty">Нічого не знайдено. Спробуй інше слово.</div>
</main>
<footer>
  <p>Оновлено {__import__('datetime').date.today().isoformat()} · <a href="https://github.com/Fil-m">github.com/Fil-m</a> ·
  репозиторій цієї сторінки: <a href="https://github.com/Fil-m/fil-m.github.io">fil-m.github.io</a></p>
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

open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(HTML)
open(os.path.join(HERE, ".nojekyll"), "w").write("")
print("index.html", len(HTML), "байт ·", len(cards), "сторінок")
