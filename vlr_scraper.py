"""
vlr_scraper.py

Pulls per-map player stats from a vlr.gg match page for use in the
VFL Points Calculator, instead of typing them in by hand.

Requires Playwright, since vlr.gg loads its stats tables in with
JavaScript after the initial page load — a plain requests.get() never
sees them. Install with:

    pip3 install playwright beautifulsoup4 --break-system-packages
    python3 -m playwright install chromium

Verified against a real match page (FNATIC vs. Karmine Corp, VCT 2026
EMEA Stage 2 W2) on 2026-07-23. vlr.gg uses div-based "tables"
(div.ovw-row / div.ovw-cell), not real <table> elements, which is why
earlier requests+BeautifulSoup attempts came back empty.

Known limitation: vlr.gg's Performance tab (2k/3k/4k/5k multi-kills)
has NOT been verified yet — the column structure there is assumed to
follow the same data-col pattern as the Overview tab but hasn't been
confirmed against real markup. Test fetch_multikills() before trusting
its output; if it's wrong, run a discovery script against the
Performance tab the same way we did for Overview.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def _get_rendered_html(url, wait_ms=3000):
    """Load a page in a real (headless) browser and return the fully
    rendered HTML, so JS-injected content (like vlr.gg's stat tables)
    is actually present."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_timeout(wait_ms)
        html = page.content()
        browser.close()
    return html


def _cell_value(cell):
    """Pull the 'both sides' number out of an ovw-cell, e.g.
    <div class="ovw-cell" data-col="acs"><span class="stats-sq">
        <span class="side mod-both">215</span>...</span></div>
    """
    if cell is None:
        return 0
    both = cell.select_one("span.side.mod-both")
    text = (both.get_text(strip=True) if both else cell.get_text(strip=True))
    text = text.replace("%", "").replace("+", "").strip()
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return 0


def _split_real_and_aggregate_rows(game):
    """
    Each map block can contain player rows twice over: once for "this map
    alone", and once for the "aggregate through all maps so far" table
    embedded right after it. Distinguishing them by agent-icon count only
    works once multiple maps are done (aggregate rows show more icons) —
    it fails on an in-progress match where only one map exists, since both
    row sets show exactly one icon each. A name-list comparison works
    regardless: if the row list duplicates itself (the same names, in the
    same order, twice), that's the real+aggregate pair.
    Returns (real_rows, aggregate_rows) — aggregate_rows is [] if no
    duplication is detected.
    """
    rows = [r for r in game.select("div.ovw-row") if "mod-head" not in (r.get("class") or [])]
    half = len(rows) // 2
    if half == 0:
        return rows, []

    def _row_name(r):
        el = r.select_one("div.ovw-player-name")
        return el.get_text(strip=True).lower() if el else ""

    first_half_names = [_row_name(r) for r in rows[:half]]
    second_half_names = [_row_name(r) for r in rows[half:]]

    if first_half_names == second_half_names:
        return rows[:half], rows[half:]
    return rows, []


def fetch_overview_stats(match_url, player_name):
    """
    Returns a list of dicts, one per map, with:
      { "map_num": int, "kills": int, "rnd_diff": int }
    """
    html = _get_rendered_html(match_url)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    game_blocks = soup.select("div.vm-stats-game")

    map_counter = 0
    for game in game_blocks:
        header = game.select_one("div.vm-stats-game-header")
        if header is None:
            continue

        map_name_el = header.select_one("div.map")
        map_name = ""
        if map_name_el:
            # Strip out the "PICK"/"BAN" badge text, keep just the map name
            map_name = map_name_el.get_text(" ", strip=True)
            map_name = map_name.split("PICK")[0].split("BAN")[0].strip()

        # Skip the "All Maps" combined summary block if present — we only
        # want individual maps
        if not map_name or map_name.lower() == "all maps":
            continue

        map_counter += 1
        i = map_counter

        team_divs = header.select("div.team")
        team_scores = []
        for t in team_divs:
            score_el = t.select_one("div.score")
            if score_el:
                score_text = score_el.get_text(strip=True)
                team_scores.append(int(score_text) if score_text.isdigit() else None)

        real_rows, _ = _split_real_and_aggregate_rows(game)
        half = len(real_rows) // 2

        player_row = None
        player_team_idx = None
        for idx, row in enumerate(real_rows):
            name_el = row.select_one("div.ovw-player-name")
            if name_el and player_name.lower() in name_el.get_text(strip=True).lower():
                player_row = row
                # vlr.gg lists team 1's players first, then team 2's —
                # use position instead of matching short tag text against
                # full team names, which don't reliably share substrings
                player_team_idx = 0 if idx < half else 1
                break

        if player_row is None:
            continue  # player didn't play this map

        kills_el = player_row.select_one('span.ovw-kda-stat[data-col="kills"]')
        kills = _cell_value(kills_el)

        rnd_diff = 0
        if player_team_idx is not None and len(team_scores) == 2 and None not in team_scores:
            own = team_scores[player_team_idx]
            opp = team_scores[1 - player_team_idx]
            rnd_diff = own - opp

        results.append({
            "map_num": i,
            "kills": kills,
            "rnd_diff": rnd_diff,
        })

    return results


def fetch_multikills(match_url, player_name):
    """
    Returns a list of dicts, one per map, with:
      { "map_num": int, "fourk": int, "fivek": int }
    Pulled from the Performance tab's "table.wf-table-inset.mod-adv-stats"
    table, which has real <table>/<tr>/<td> markup (unlike the Overview
    tab's div-based layout). Verified column order:
      [name/team, agent icon, 2K, 3K, 4K, 5K, 1v1, 1v2, 1v3, 1v4, 1v5, ECON, PL, DE]
    So 4K is td[4] and 5K is td[5] (0-indexed).
    sixk/sevenk aren't tracked by vlr.gg at all — there's no column past 5K.
    """
    perf_url = match_url.rstrip("/") + "/?tab=performance"
    html = _get_rendered_html(perf_url)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    game_blocks = soup.select("div.vm-stats-game")

    # Unlike the Overview tab, the Performance tab's blocks have no
    # div.map header text to key off. Verified against real data instead:
    # block 0's 2K/4K totals exactly equal the sum of blocks 1+2+3's —
    # confirming block 0 is the aggregate "All Maps" block and blocks
    # 1..N are the real individual maps, in order.
    for i, game in enumerate(game_blocks[1:], start=1):

        table = game.select_one("table.wf-table-inset.mod-adv-stats")
        if table is None:
            results.append({"map_num": i, "fourk": 0, "fivek": 0})
            continue

        player_row = None
        for row in table.select("tbody tr"):
            name_cell = row.find("td")
            if name_cell and player_name.lower() in name_cell.get_text(strip=True).lower():
                player_row = row
                break

        if player_row is None:
            results.append({"map_num": i, "fourk": 0, "fivek": 0})
            continue

        cells = player_row.find_all("td")

        def _stat_sq_value(cell):
            if cell is None:
                return 0
            sq = cell.select_one("div.stats-sq")
            if sq is None:
                return 0
            # Cells with real values embed a hidden tooltip (round-by-round
            # breakdown) inside the same div — strip it out first, or the
            # combined text won't be a clean digit and silently reads as 0
            popable = sq.select_one(".wf-popable-contents")
            if popable:
                popable.extract()
            text = sq.get_text(strip=True)
            return int(text) if text.isdigit() else 0

        fourk = _stat_sq_value(cells[4]) if len(cells) > 4 else 0
        fivek = _stat_sq_value(cells[5]) if len(cells) > 5 else 0

        results.append({"map_num": i, "fourk": fourk, "fivek": fivek})

    return results


def fetch_overall_rating(match_url, player_name):
    """
    The VFL calculator asks for ONE VLR rating for the whole match, not
    per map. Where that lives turns out to depend on match state:
      - On a fully completed match, it's a standalone block with NO
        div.map header text at all (confirmed: its kills total exactly
        equals the sum of the real per-map blocks').
      - On a still-live match, it can instead be merged into another
        block as duplicated rows (same names twice in a row).
    This checks for the standalone blank-name block first, and falls
    back to the row-duplication check if that's not found. Returns None
    if neither pattern turns anything up.
    """
    html = _get_rendered_html(match_url)
    soup = BeautifulSoup(html, "html.parser")

    game_blocks = soup.select("div.vm-stats-game")

    # Pattern 1: a standalone block with no map name
    for game in game_blocks:
        header = game.select_one("div.vm-stats-game-header")
        map_name_el = header.select_one("div.map") if header else None
        map_name = map_name_el.get_text(" ", strip=True).strip() if map_name_el else ""

        if map_name:
            continue  # this is a real, named map — not the aggregate block

        rows = [r for r in game.select("div.ovw-row") if "mod-head" not in (r.get("class") or [])]
        for row in rows:
            name_el = row.select_one("div.ovw-player-name")
            if name_el and player_name.lower() in name_el.get_text(strip=True).lower():
                return _cell_value(row.select_one('div.ovw-cell[data-col="rating2"]'))

    # Pattern 2: merged/duplicated rows within a named map block
    best_rating = None
    for game in game_blocks:
        _, aggregate_rows = _split_real_and_aggregate_rows(game)
        for row in aggregate_rows:
            name_el = row.select_one("div.ovw-player-name")
            if name_el and player_name.lower() in name_el.get_text(strip=True).lower():
                best_rating = _cell_value(row.select_one('div.ovw-cell[data-col="rating2"]'))

    return best_rating


def get_player_match_data(match_url, player_name, include_multikills=False):
    """
    Combines per-map stats + the overall match rating into one payload:
      { "maps": [ {map_num, kills, rnd_diff, fourk, fivek, sixk, sevenk}, ... ],
        "overall_rating": float or None }
    include_multikills defaults to False since that part is unverified —
    turn it on once fetch_multikills() has been checked.
    """
    overview = fetch_overview_stats(match_url, player_name)
    overall_rating = fetch_overall_rating(match_url, player_name)

    mk_by_map = {}
    if include_multikills:
        multikills = fetch_multikills(match_url, player_name)
        mk_by_map = {m["map_num"]: m for m in multikills}

    maps = []
    for entry in overview:
        mk = mk_by_map.get(entry["map_num"], {"fourk": 0, "fivek": 0})
        maps.append({
            "map_num": entry["map_num"],
            "kills": entry["kills"],
            "rnd_diff": entry["rnd_diff"],
            "fourk": mk["fourk"],
            "fivek": mk["fivek"],
            "sixk": 0,    # not tracked by vlr.gg at all
            "sevenk": 0,  # not tracked by vlr.gg at all
        })

    return {"maps": maps, "overall_rating": overall_rating}


if __name__ == "__main__":
    TEST_URL = "https://www.vlr.gg/712814/fut-esports-vs-pcific-esports-vct-2026-emea-stage-2-w2"
    TEST_PLAYER = "sociablEE"

    data = get_player_match_data(TEST_URL, TEST_PLAYER, include_multikills=True)
    print("Overall match rating:", data["overall_rating"])
    for map_data in data["maps"]:
        print(map_data)
