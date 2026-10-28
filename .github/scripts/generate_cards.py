#!/usr/bin/env python3
"""
Generate cyberpunk profile cards (SVG) straight from the GitHub API.
Standard library only -> no pip install, no third-party image services.

Output (default folder: assets/):
  stats.svg, streak.svg, languages.svg, activity.svg,
  achievements.svg, project-1.svg, project-2.svg, project-3.svg
"""
import datetime as dt
import html
import json
import math
import os
import urllib.request

USER = os.environ.get("GH_USER", "daffaharashtarizkypratama-commits")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT_DIR", "assets")
API = "https://api.github.com"

# Repo yang ingin ditampilkan sebagai kartu proyek (nama repo, deskripsi cadangan)
FEATURED = [
    ("GraphixCalculator", "Web-based graphing calculator built with HTML."),
    ("sistem-layanan-laundry", "Laundry service management system built with Java."),
    ("V3425053_Modul_8_Vue_Laravel", "Frontend project integrating Vue.js and Laravel."),
]

LANG_COLORS = {
    "PHP": "#8892BF", "JavaScript": "#F1E05A", "HTML": "#E34C26", "CSS": "#8B5CF6",
    "Java": "#F89820", "Vue": "#41B883", "Blade": "#F7523F", "Python": "#3776AB",
    "Dart": "#00B4AB", "C++": "#F34B7D", "C": "#9CA3AF", "TypeScript": "#3178C6",
    "Kotlin": "#A97BFF", "Shell": "#89E051", "SCSS": "#C6538C", "Jupyter Notebook": "#DA5B0B",
}

FONT = "'Fira Code','JetBrains Mono','Courier New',Consolas,monospace"

CSS = """
text{font-family:%s}
.t{font-size:13px;letter-spacing:3px;fill:#00E5FF;font-weight:700}
.tag{font-size:11px;letter-spacing:2px;fill:#8B5CF6}
.lbl{font-size:11px;letter-spacing:2px;fill:#9CA3AF}
.num{font-size:28px;font-weight:700;fill:#FFFFFF}
.big{font-size:40px;font-weight:700;fill:#FFFFFF}
.sm{font-size:12px;fill:#C4B5FD}
.name{font-size:15px;font-weight:700;fill:#FFFFFF}
.desc{font-size:12px;fill:#9CA3AF}
.in{animation:in .7s ease both}
@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
""" % FONT


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=True)


def get(url, payload=None):
    headers = {"User-Agent": "daffa-profile-cards", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", path)


def fmt(n):
    return f"{int(n):,}"


def wrap_text(s, width, lines):
    words, out, cur = (s or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w).strip()
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: max(0, width - 3)].rstrip() + "..."
    return out


def frame(w, h, title, tag, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B0F1A"/><stop offset="1" stop-color="#140022"/></linearGradient>
<linearGradient id="neon" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8B5CF6"/><stop offset=".5" stop-color="#00E5FF"/><stop offset="1" stop-color="#FF003C"/></linearGradient>
<linearGradient id="bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#4C0070"/><stop offset="1" stop-color="#00E5FF"/></linearGradient>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" opacity=".04"/></pattern>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>{CSS}</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="url(#bg)" stroke="url(#neon)" stroke-width="2"/>
<circle cx="26" cy="27" r="4" fill="#00FF9C"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>
<text x="40" y="31" class="t">{esc(title)}</text>
<text x="{w - 24}" y="31" class="tag" text-anchor="end">{esc(tag)}</text>
<line x1="24" y1="44" x2="{w - 24}" y2="44" stroke="#8B5CF6" stroke-opacity=".35"/>
{body}
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="url(#scan)"/>
</svg>
"""


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def fetch_repos():
    repos, page = [], 1
    while True:
        batch = get(f"{API}/users/{USER}/repos?per_page=100&type=owner&sort=updated&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_languages(repos):
    totals = {}
    for r in repos:
        if r.get("fork"):
            continue
        try:
            langs = get(r["languages_url"])
        except Exception:
            langs = {r["language"]: 1} if r.get("language") else {}
        for k, v in langs.items():
            totals[k] = totals.get(k, 0) + v
    return totals


def fetch_calendar():
    """Kalender kontribusi 1 tahun (butuh token; otomatis tersedia di GitHub Actions)."""
    if not TOKEN:
        return None
    query = (
        "query($login:String!){user(login:$login){contributionsCollection{"
        "contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"
    )
    try:
        d = get(API + "/graphql", {"query": query, "variables": {"login": USER}})
        weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = {x["date"]: x["contributionCount"] for w in weeks for x in w["contributionDays"]}
        return days, "LAST YEAR"
    except Exception as e:  # noqa
        print("graphql failed, using public events:", e)
        return None


def fetch_events():
    days = {}
    for page in (1, 2, 3):
        try:
            events = get(f"{API}/users/{USER}/events/public?per_page=100&page={page}")
        except Exception:
            break
        if not events:
            break
        for e in events:
            d = e["created_at"][:10]
            n = 1
            if e["type"] == "PushEvent":
                n = max(1, e["payload"].get("size") or len(e["payload"].get("commits", [])) or 1)
            days[d] = days.get(d, 0) + n
    return days, "RECENT"


def compute_streaks(days, today):
    def d_of(s):
        return dt.date.fromisoformat(s)

    # current streak (hari ini boleh masih 0)
    cur, cur_end = 0, None
    d = today
    if days.get(d.isoformat(), 0) == 0:
        d -= dt.timedelta(days=1)
    cur_end = d
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    cur_start = d + dt.timedelta(days=1)

    # longest streak
    longest, run, prev, run_start, best = 0, 0, None, None, (None, None)
    for k in sorted(days):
        if days[k] <= 0:
            continue
        cd = d_of(k)
        if prev is not None and (cd - prev).days == 1:
            run += 1
        else:
            run, run_start = 1, cd
        prev = cd
        if run > longest:
            longest, best = run, (run_start, cd)

    def rng(a, b):
        if not a or not b:
            return "-"
        f = lambda x: x.strftime("%b %d")
        return f(a) if a == b else f"{f(a)} - {f(b)}"

    return cur, rng(cur_start, cur_end) if cur else "-", longest, rng(*best)


# --------------------------------------------------------------------------
# cards
# --------------------------------------------------------------------------
def tile(x, y, w, h, label, value, color, delay):
    return (
        f'<g class="in" style="animation-delay:{delay}s">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#0D1117" stroke="{color}" stroke-opacity=".55"/>'
        f'<rect x="{x}" y="{y + 12}" width="3" height="{h - 24}" rx="1.5" fill="{color}"/>'
        f'<text x="{x + 20}" y="{y + 25}" class="lbl">{esc(label)}</text>'
        f'<text x="{x + 20}" y="{y + 54}" class="num" style="fill:{color}">{esc(value)}</text>'
        f"</g>"
    )


def card_stats(user, repos, total_contrib):
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in own)
    forks = sum(r.get("forks_count", 0) for r in own)
    items = [
        ("PUBLIC REPOS", fmt(user.get("public_repos", len(repos))), "#8B5CF6"),
        ("TOTAL STARS", fmt(stars), "#FFB800"),
        ("TOTAL FORKS", fmt(forks), "#00FF9C"),
        ("FOLLOWERS", fmt(user.get("followers", 0)), "#00E5FF"),
        ("FOLLOWING", fmt(user.get("following", 0)), "#C4B5FD"),
        ("CONTRIBUTIONS", fmt(total_contrib), "#FF003C"),
    ]
    body = ""
    for i, (label, val, color) in enumerate(items):
        x = 17 + (i % 3) * 280
        y = 62 + (i // 3) * 78
        body += tile(x, y, 266, 66, label, val, color, round(i * 0.1, 1))
    since = user.get("created_at", "")[:4]
    body += f'<text x="430" y="232" class="sm" text-anchor="middle">@{esc(USER)}  //  MEMBER SINCE {esc(since)}</text>'
    return frame(860, 250, "GITHUB STATS", "LIVE DATA", body), stars


def card_streak(days, label, today):
    total = sum(days.values())
    cur, cur_rng, longest, long_rng = compute_streaks(days, today)
    circ = 2 * math.pi * 40
    frac = min(1.0, cur / max(longest, 1)) if cur else 0.0
    off = circ * (1 - frac)
    body = f"""
<line x1="287" y1="62" x2="287" y2="182" stroke="#8B5CF6" stroke-opacity=".35"/>
<line x1="573" y1="62" x2="573" y2="182" stroke="#8B5CF6" stroke-opacity=".35"/>

<g class="in">
<text x="143" y="84" class="lbl" text-anchor="middle">TOTAL CONTRIBUTIONS</text>
<text x="143" y="132" class="big" text-anchor="middle" style="fill:#8B5CF6">{fmt(total)}</text>
<text x="143" y="160" class="sm" text-anchor="middle">{esc(label)}</text>
</g>

<g class="in" style="animation-delay:.15s">
<circle cx="430" cy="106" r="40" fill="none" stroke="#1F2937" stroke-width="8"/>
<circle cx="430" cy="106" r="40" fill="none" stroke="url(#neon)" stroke-width="8" stroke-linecap="round"
 stroke-dasharray="{circ:.2f}" stroke-dashoffset="{circ:.2f}" transform="rotate(-90 430 106)" filter="url(#glow)">
<animate attributeName="stroke-dashoffset" from="{circ:.2f}" to="{off:.2f}" dur="1.4s" fill="freeze"/>
</circle>
<text x="430" y="118" class="num" text-anchor="middle" style="font-size:32px">{cur}</text>
<text x="430" y="170" class="lbl" text-anchor="middle" style="fill:#00E5FF">CURRENT STREAK</text>
<text x="430" y="188" class="sm" text-anchor="middle">{esc(cur_rng)}</text>
</g>

<g class="in" style="animation-delay:.3s">
<text x="717" y="84" class="lbl" text-anchor="middle">LONGEST STREAK</text>
<text x="717" y="132" class="big" text-anchor="middle" style="fill:#FF003C">{longest}</text>
<text x="717" y="160" class="sm" text-anchor="middle">{esc(long_rng)}</text>
</g>
"""
    return frame(860, 200, "CONTRIBUTION STREAK", "DAYS IN A ROW", body)


def card_languages(totals):
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    total = sum(v for _, v in items)
    if not total:
        body = '<text x="430" y="110" class="sm" text-anchor="middle">NO LANGUAGE DATA YET</text>'
        return frame(860, 160, "TOP LANGUAGES", "BY CODE SIZE", body)

    bar_x, bar_w = 24, 812
    body = (
        '<defs><clipPath id="barclip"><rect x="24" y="62" height="14" rx="7" width="0">'
        f'<animate attributeName="width" from="0" to="{bar_w}" dur="1.2s" fill="freeze"/></rect></clipPath></defs>'
        '<g clip-path="url(#barclip)">'
    )
    x = bar_x
    pcts = []
    for name, val in items:
        pct = val / total * 100
        pcts.append((name, pct))
        w = bar_w * val / total
        color = LANG_COLORS.get(name, "#8B5CF6")
        body += f'<rect x="{x:.2f}" y="62" width="{w + 0.5:.2f}" height="14" fill="{color}"/>'
        x += w
    body += "</g>"

    for i, (name, pct) in enumerate(pcts):
        col, row = i % 2, i // 2
        cx = 34 + col * 410
        cy = 112 + row * 30
        color = LANG_COLORS.get(name, "#8B5CF6")
        body += (
            f'<g class="in" style="animation-delay:{round(i * 0.08, 2)}s">'
            f'<circle cx="{cx}" cy="{cy - 4}" r="6" fill="{color}"/>'
            f'<text x="{cx + 16}" y="{cy}" class="name" style="font-size:14px">{esc(name)}</text>'
            f'<text x="{cx + 380}" y="{cy}" class="sm" text-anchor="end">{pct:.1f}%</text></g>'
        )
    rows = math.ceil(len(pcts) / 2)
    h = 112 + rows * 30 + 6
    return frame(860, h, "TOP LANGUAGES", "BY CODE SIZE", body)


def card_activity(days, today):
    series = []
    for k in range(29, -1, -1):
        d = today - dt.timedelta(days=k)
        series.append((d, days.get(d.isoformat(), 0)))
    counts = [c for _, c in series]
    total30 = sum(counts)
    peak = max(max(counts), 1)

    x0, base, ch, step = 56, 205, 135, 26
    body = ""
    for frac in (0, 0.5, 1):
        gy = base - ch * frac
        body += f'<line x1="{x0}" y1="{gy:.1f}" x2="836" y2="{gy:.1f}" stroke="#8B5CF6" stroke-opacity=".18" stroke-dasharray="3 5"/>'
    body += f'<text x="46" y="{base + 4}" class="lbl" text-anchor="end">0</text>'
    body += f'<text x="46" y="{base - ch + 4}" class="lbl" text-anchor="end">{peak}</text>'

    for i, (d, c) in enumerate(series):
        x = x0 + i * step + 4
        if c > 0:
            h = max(4, ch * c / peak)
            body += (
                f'<rect x="{x}" y="{base}" width="18" height="0" rx="3" fill="url(#bar)" filter="url(#glow)">'
                f'<animate attributeName="height" from="0" to="{h:.1f}" dur=".8s" begin="{i * 0.03:.2f}s" fill="freeze"/>'
                f'<animate attributeName="y" from="{base}" to="{base - h:.1f}" dur=".8s" begin="{i * 0.03:.2f}s" fill="freeze"/>'
                f"</rect>"
            )
        else:
            body += f'<rect x="{x}" y="{base - 2}" width="18" height="2" rx="1" fill="#8B5CF6" fill-opacity=".45"/>'
    for idx in (0, 14, 29):
        d = series[idx][0]
        body += f'<text x="{x0 + idx * step + 13}" y="226" class="lbl" text-anchor="middle">{d.strftime("%b %d").upper()}</text>'
    return frame(860, 244, "ACTIVITY SIGNAL", f"{fmt(total30)} CONTRIBUTIONS // 30 DAYS", body)


def card_project(repo, fallback_desc, idx):
    name = repo["name"] if repo else fallback_desc[0]
    desc = (repo.get("description") if repo else None) or fallback_desc[1]
    lang = (repo.get("language") if repo else None) or "Code"
    stars = repo.get("stargazers_count", 0) if repo else 0
    forks = repo.get("forks_count", 0) if repo else 0
    updated = (repo.get("pushed_at") or repo.get("updated_at") or "")[:10] if repo else ""
    color = LANG_COLORS.get(lang, "#8B5CF6")
    lines = wrap_text(desc, 48, 2)
    star = "M0 -7 L2 -2.5 L7 -2.2 L3.2 1.2 L4.4 6 L0 3.4 L-4.4 6 L-3.2 1.2 L-7 -2.2 L-2 -2.5 Z"

    body = f'<path d="M26 58 h12 l4 5 h18 v22 h-34 z" fill="none" stroke="#00E5FF" stroke-width="1.8" stroke-linejoin="round"/>'
    body += f'<text x="76" y="80" class="name" style="font-size:16px;fill:#8B5CF6">{esc(name[:30])}</text>'
    for i, ln in enumerate(lines):
        body += f'<text x="26" y="{110 + i * 18}" class="desc">{esc(ln)}</text>'
    body += (
        f'<circle cx="32" cy="162" r="6" fill="{color}"/>'
        f'<text x="46" y="166" class="sm">{esc(lang)}</text>'
        f'<g transform="translate(160 161)"><path d="{star}" fill="#FFB800"/></g>'
        f'<text x="172" y="166" class="sm">{stars}</text>'
        f'<text x="212" y="166" class="sm" style="fill:#00FF9C">FORKS {forks}</text>'
    )
    if updated:
        body += f'<text x="{420 - 24}" y="166" class="lbl" text-anchor="end">UPD {updated}</text>'
    return frame(420, 190, f"PROJECT {idx:02d}", "REPOSITORY", body)


ACH = [
    ("FIRST COMMIT", "Make a contribution", lambda s: s["contrib"] >= 1),
    ("REPO BUILDER", "Own 5+ repositories", lambda s: s["repos"] >= 5),
    ("CENTURY", "100 contributions", lambda s: s["contrib"] >= 100),
    ("STARGAZER", "Earn your first star", lambda s: s["stars"] >= 1),
    ("SOCIAL NODE", "Get 3+ followers", lambda s: s["followers"] >= 3),
    ("STREAK x3", "3 days in a row", lambda s: s["longest"] >= 3),
    ("STREAK x7", "7 days in a row", lambda s: s["longest"] >= 7),
    ("POLYGLOT", "Code in 4+ languages", lambda s: s["langs"] >= 4),
]


def card_achievements(stats):
    shield = "M0 -15 L13 -10 V3 C13 11 6 15 0 19 C-6 15 -13 11 -13 3 V-10 Z"
    body, unlocked = "", 0
    for i, (title, desc, cond) in enumerate(ACH):
        ok = bool(cond(stats))
        unlocked += ok
        col, row = i % 4, i // 4
        x, y = 17 + col * 206, 60 + row * 100
        stroke = "#00E5FF" if ok else "#374151"
        op = "1" if ok else ".55"
        icon = (
            '<path d="M-5 1 L-1 5 L6 -4" fill="none" stroke="#00FF9C" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
            if ok
            else '<rect x="-5" y="-1" width="10" height="8" rx="1.5" fill="#6B7280"/><path d="M-3 -1 v-3 a3 3 0 0 1 6 0 v3" fill="none" stroke="#6B7280" stroke-width="1.8"/>'
        )
        body += (
            f'<g class="in" style="animation-delay:{round(i * 0.08, 2)}s;opacity:{op}">'
            f'<rect x="{x}" y="{y}" width="194" height="88" rx="10" fill="#0D1117" stroke="{stroke}" stroke-opacity=".8"/>'
            f'<g transform="translate({x + 34} {y + 44})"><path d="{shield}" fill="{"#160024" if ok else "#111827"}" stroke="{stroke}" stroke-width="2"/>{icon}</g>'
            f'<text x="{x + 64}" y="{y + 38}" class="name" style="font-size:12px;letter-spacing:1px">{esc(title)}</text>'
            f'<text x="{x + 64}" y="{y + 58}" class="desc" style="font-size:11px">{esc(desc)}</text>'
            f'<text x="{x + 64}" y="{y + 76}" class="lbl" style="fill:{"#00FF9C" if ok else "#6B7280"}">{"UNLOCKED" if ok else "LOCKED"}</text>'
            f"</g>"
        )
    return frame(860, 264, "ACHIEVEMENT ARCHIVE", f"{unlocked}/{len(ACH)} UNLOCKED", body)


# --------------------------------------------------------------------------
def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    user = get(f"{API}/users/{USER}")
    repos = fetch_repos()
    print(f"user={USER} repos={len(repos)}")

    cal = fetch_calendar() or fetch_events()
    days, label = cal

    totals = fetch_languages(repos)

    stats_svg, stars = card_stats(user, repos, sum(days.values()))
    write("stats.svg", stats_svg)
    write("streak.svg", card_streak(days, label, today))
    write("languages.svg", card_languages(totals))
    write("activity.svg", card_activity(days, today))

    own = [r for r in repos if not r.get("fork")]
    _, _, longest, _ = compute_streaks(days, today)
    write(
        "achievements.svg",
        card_achievements(
            {
                "contrib": sum(days.values()),
                "repos": len(own),
                "stars": stars,
                "followers": user.get("followers", 0),
                "longest": longest,
                "langs": len(totals),
            }
        ),
    )

    by_name = {r["name"].lower(): r for r in repos}
    for i, (name, desc) in enumerate(FEATURED, 1):
        repo = by_name.get(name.lower())
        write(f"project-{i}.svg", card_project(repo, (name, desc), i))


if __name__ == "__main__":
    main()
