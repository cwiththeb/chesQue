import requests, time

BASE = "https://api.chess.com/pub/player/{}"

def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent": "chessPull-CB"}, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_state(user):
    profile = fetch(BASE.format(user))
    stats = fetch(BASE.format(user) + "/stats")

    if not profile:
        return None

    # Online (derived)()
    online = (time.time() - profile.get("last_online", 0)) < 300

    # Ratings
    def rating(mode):
        return stats.get(mode, {}).get("last", {}).get("rating") if stats else None

    blitz = rating("chess_blitz")
    rapid = rating("chess_rapid")
    bullet = rating("chess_bullet")

    # Latest game
    latest_game = None
    archives = fetch(BASE.format(user) + "/games/archives")

    if archives and archives.get("archives"):
        last_month = archives["archives"][-1]
        games = fetch(last_month)
        if games and games.get("games"):
            latest_game = games["games"][-1]["url"]

    return {
        "online": online,
        "blitz": blitz,
        "rapid": rapid,
        "bullet": bullet,
        "last_game": latest_game
    }


def main():
    user = input("Enter Chess Username: ").strip()
    interval = input("Polling interval (default 60): ").strip()

    interval = int(interval) if interval.isdigit() else 60

    if interval < 30:
        print("Warning: Low interval may trigger API blocking.\n")

    print(f"Fetching {user}...\n")

    state = get_state(user)

    if not state:
        print("Invalid user or API error.")
        return

    print(f"{user} State Poll Result: ", state, "\n")

    while True:
        new = get_state(user)

        if not new:
            print("Fetch failed.")
            time.sleep(interval)
            continue

        # --- Detect changes ---

        if new["online"] != state["online"]:
            print(f"[ONLINE] -> {new['online']}")

        for mode in ["blitz", "rapid", "bullet"]:
            if new[mode] != state[mode] and new[mode] is not None:
                print(f"[RATING] {mode}: {state[mode]} -> {new[mode]}")

        if new["last_game"] != state["last_game"]:
            print(f"[NEW GAME] {new['last_game']}")

        state = new
        time.sleep(interval)


if __name__ == "__main__":
    main()