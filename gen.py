"""Builds dark_mode.svg and light_mode.svg: ASCII portrait + neofetch-style card.
Run: GH_TOKEN=... python3 gen.py   (token only needed for live stats)"""
import json, os, urllib.request
from xml.sax.saxutils import escape
from PIL import Image, ImageFilter, ImageOps

LOGIN = "anuroopanand7"
COLS, ROWS = 96, 48  # rows = cols * ART_CW / ART_LH, so a square photo is not stretched
RAMP = " .:-=+*#%@"  # light to dark

INFO = [
    ("title", f"anuroop@{LOGIN}"),
    ("rule", ""),
    ("kv", "Role", "Founder, AIRs Network"),
    ("kv", "Alma mater", "IIT Kharagpur"),
    ("kv", "Location", "Hyderabad, India"),
    ("kv", "Building", "Verified IIT + IIM community app"),
    ("kv", "Skills.Product", "Product, UI/UX prototyping"),
    ("kv", "Skills.AI", "AI automation, agentic coding"),
    ("blank", ""),
    ("head", "Contact"),
    ("kv", "Email", "anuroop@airscommunity.com"),
    ("kv", "GitHub", f"github.com/{LOGIN}"),
    ("blank", ""),
    ("head", "GitHub Stats"),
]


def ascii_art(path):
    img = ImageOps.autocontrast(ImageOps.fit(Image.open(path).convert("L"), (400, 400)).filter(ImageFilter.MinFilter(3)).resize((COLS, ROWS), Image.LANCZOS))
    img = img.point(lambda p: 255 if p > 200 else p * 255 // 200)  # flat background to blank
    rows = []
    for y in range(ROWS):
        rows.append("".join(RAMP[(255 - img.getpixel((x, y))) * (len(RAMP) - 1) // 255] for x in range(COLS)))
    return rows


def stats():
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok:
        return {"Repos": "-", "Stars": "-", "Followers": "-", "Contributions (1y)": "-"}
    q = """query($l:String!){user(login:$l){followers{totalCount}
      repositories(ownerAffiliations:OWNER,first:100){totalCount nodes{stargazerCount}}
      contributionsCollection{contributionCalendar{totalContributions}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {tok}"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    r = u["repositories"]
    return {"Repos": r["totalCount"], "Stars": sum(n["stargazerCount"] for n in r["nodes"]),
            "Followers": u["followers"]["totalCount"],
            "Contributions (1y)": u["contributionsCollection"]["contributionCalendar"]["totalContributions"]}


THEMES = {
    "dark_mode": dict(bg="#0d1117", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", art="#ff7b54", dot="#484f58"),
    "light_mode": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", art="#cf4a1c", dot="#afb8c1"),
}
W_CH, LH, INFO_W = 8.4, 18, 52  # info: char width px, line height px, columns
ART_FS, ART_CW, ART_LH = 8.4, 5.04, 10.08  # small art font gives the eyes more cells


def svg(theme, art, lines):
    t = THEMES[theme]
    x0, x1 = 24, 24 + COLS * ART_CW + 30
    h = int(max(len(art) * ART_LH, len(lines) * LH) + 48)
    w = int(x1 + INFO_W * W_CH + 24)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14px">',
           f'<rect width="100%" height="100%" rx="12" fill="{t["bg"]}"/>',
           f'<text x="{x0}" y="36" fill="{t["art"]}" font-size="{ART_FS}px" xml:space="preserve">']
    out += [f'<tspan x="{x0}" dy="{0 if i == 0 else ART_LH}">{escape(r)}</tspan>' for i, r in enumerate(art)]
    out.append(f'</text><text x="{x1}" y="36" fill="{t["fg"]}" xml:space="preserve">')
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else LH
        kind = ln[0]
        if kind == "title":
            body = f'<tspan fill="{t["key"]}" font-weight="bold">{escape(ln[1])}</tspan>'
        elif kind == "rule":
            body = escape("-" * INFO_W)
        elif kind == "head":
            body = f'<tspan font-weight="bold">{escape(ln[1])}</tspan> ' + escape("-" * (INFO_W - len(ln[1]) - 1))
        elif kind == "kv":
            k, v = ln[1], str(ln[2])
            dots = "." * max(2, INFO_W - len(k) - len(v) - 4)
            body = (f'<tspan fill="{t["key"]}">{escape(k)}</tspan>: <tspan fill="{t["dot"]}">{dots}</tspan> '
                    f'<tspan fill="{t["val"]}">{escape(v)}</tspan>')
        else:
            body = "&#160;"
        out.append(f'<tspan x="{x1}" dy="{dy}">{body}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    art = ascii_art(os.path.join(os.path.dirname(os.path.abspath(__file__)), "portrait.jpg"))
    lines = INFO + [("kv", k, v) for k, v in stats().items()]
    assert all(len(r) == COLS for r in art) and len(art) == ROWS
    for name in THEMES:
        open(f"{name}.svg", "w").write(svg(name, art, lines))
    print("wrote", ", ".join(f"{n}.svg" for n in THEMES))
