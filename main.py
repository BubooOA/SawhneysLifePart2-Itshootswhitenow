import math, random, time, tkinter as tk

W, H = 800, 540
SPRITES = {"p": [".p.", "ppp", "p.p"], "z": ["zzz", "z.z", ".z."], "v": ["vvv", "v.v", "d.d"]}
COLORS = {"p": "#f1d2a4", "z": "#55a36a", "v": "#bd4c5a", "d": "#493450"}
FAMILIES = [("fire", 25, 4, .06), ("speed", 25, 3, .08), ("life", 25, 5, 1), ("regen", 24, 5, .5)]
upgrades = [{"kind": kind, "name": f"{kind.title()} {tier + 1}", "cost": min(25, base + tier), "value": step * (tier + 1)}
            for kind, count, base, step in FAMILIES for tier in range(count)]
upgrades.append({"kind": "rail", "name": "Whiteout Railgun", "cost": 50, "value": 1})


def reset():
    game.update({"x": W / 2, "y": H / 2, "keys": set(), "enemies": [], "shots": [], "bad_shots": [], "options": [], "stats": dict.fromkeys([f[0] for f in FAMILIES], 0), "lives": 3, "max_lives": 3, "money": 0, "kills": 0, "level": 0, "rail": 0, "mouse": False, "space": False, "mx": W / 2, "my": H / 2, "shot_time": 0, "spawn_time": 0, "hit_time": 0, "regen_time": 0, "mode": "play"})


def spawn(now):
    x, y = random.randrange(W), random.randrange(H)
    side = random.randrange(4)
    x = -10 if side == 0 else W + 10 if side == 1 else x
    y = -10 if side == 2 else H + 10 if side == 3 else y
    vampire = game["level"] > 10 and random.random() < .35
    game["enemies"].append({"x": x, "y": y, "hp": 2, "v": vampire, "time": now})


def killed(enemy):
    if enemy not in game["enemies"]:
        return
    game["enemies"].remove(enemy)
    game["kills"] += 1
    game["money"] += 2
    if game["mode"] == "play" and game["kills"] >= (game["level"] + 1) * 10:
        game["level"] += 1
        offer_upgrades()


def offer_upgrades():
    choices = [item for item in upgrades if item["kind"] != "rail" and item["cost"] <= game["money"]]
    rail = next((item for item in upgrades if item["kind"] == "rail"), None)
    game["options"] = random.sample(choices, 3)
    if game["money"] >= 50 and random.random() < .35:
        game["options"][-1] = rail
    game["mode"] = "shop"


def choose(index):
    item = game["options"][index]
    if item["cost"] > game["money"]:
        return
    game["money"] -= item["cost"]
    if item["kind"] == "rail":
        game["rail"] += 1
    else:
        game["stats"][item["kind"]] += item["value"]
    if item["kind"] == "life":
        game["lives"] += item["value"]
        game["max_lives"] += item["value"]
    game["mode"] = "play"


def key_down(event):
    key = event.keysym.lower()
    game["keys"].add(key)
    if key == "space":
        game["space"] = True
    if game["mode"] == "shop" and key in "123":
        choose(int(key) - 1)
    if game["mode"] == "over" and key == "return":
        reset()


def key_up(event):
    key = event.keysym.lower()
    game["keys"].discard(key)
    if key == "space":
        game["space"] = False


def mouse_move(event):
    game["mx"], game["my"] = event.x, event.y


def hurt(now):
    if now - game["hit_time"] <= .8:
        return
    game["lives"] -= 1
    game["hit_time"] = now
    if game["lives"] <= 0:
        game["mode"] = "over"


def fire(now):
    if not (game["mouse"] or game["space"]) or now - game["shot_time"] < max(.07, .24 / (1 + game["stats"]["fire"])):
        return
    game["shot_time"] = now
    angle = math.atan2(game["my"] - game["y"], game["mx"] - game["x"])
    if game["rail"]:
        dx, dy = math.cos(angle), math.sin(angle)
        hits = [e for e in game["enemies"] if (e["x"] - game["x"]) * dx + (e["y"] - game["y"]) * dy > 0 and abs((e["x"] - game["x"]) * dy - (e["y"] - game["y"]) * dx) < 20]
        if hits:
            first = min(hits, key=lambda e: math.hypot(e["x"] - game["x"], e["y"] - game["y"]))
            chain = [first] + [e for e in game["enemies"] if e is not first and math.hypot(e["x"] - first["x"], e["y"] - first["y"]) < 200][:2 + 2 * (game["rail"] - 1)]
            for enemy in chain:
                killed(enemy)
        return
    game["shots"].append([game["x"], game["y"], math.cos(angle) * 6, math.sin(angle) * 6])


def update():
    now = time.time()
    if game["mode"] == "play":
        keys = game["keys"]
        dx = ("d" in keys or "right" in keys) - ("a" in keys or "left" in keys)
        dy = ("s" in keys or "down" in keys) - ("w" in keys or "up" in keys)
        speed = 3 + game["stats"]["speed"]
        length = math.hypot(dx, dy) or 1
        game["x"] = min(W - 15, max(15, game["x"] + dx / length * speed))
        game["y"] = min(H - 15, max(45, game["y"] + dy / length * speed))
        if now - game["spawn_time"] > max(.35, 1.1 - game["kills"] * .004):
            spawn(now)
            game["spawn_time"] = now
        fire(now)
        for shot in game["shots"][:]:
            shot[0] += shot[2]
            shot[1] += shot[3]
            if not 0 <= shot[0] <= W or not 0 <= shot[1] <= H:
                game["shots"].remove(shot)
                continue
            for enemy in game["enemies"][:]:
                if math.hypot(enemy["x"] - shot[0], enemy["y"] - shot[1]) >= 18:
                    continue
                enemy["hp"] -= 1
                if enemy["hp"] == 0:
                    killed(enemy)
                game["shots"].remove(shot)
                break
        for enemy in game["enemies"]:
            angle = math.atan2(game["y"] - enemy["y"], game["x"] - enemy["x"])
            enemy["x"] += math.cos(angle) * .65
            enemy["y"] += math.sin(angle) * .65
            if math.hypot(enemy["x"] - game["x"], enemy["y"] - game["y"]) < 20 and now - game["hit_time"] > .8:
                hurt(now)
            if enemy["v"] and now - enemy["time"] > 2.4:
                game["bad_shots"].append([enemy["x"], enemy["y"], math.cos(angle) * 2, math.sin(angle) * 2])
                enemy["time"] = now
        for shot in game["bad_shots"][:]:
            shot[0] += shot[2]
            shot[1] += shot[3]
            if math.hypot(shot[0] - game["x"], shot[1] - game["y"]) < 14 and now - game["hit_time"] > .8:
                hurt(now)
                game["bad_shots"].remove(shot)
            elif not 0 <= shot[0] <= W or not 0 <= shot[1] <= H:
                game["bad_shots"].remove(shot)
        if game["stats"]["regen"] and game["lives"] < game["max_lives"] and now - game["regen_time"] > max(5, 35 / game["stats"]["regen"]):
            game["lives"] += 1
            game["regen_time"] = now
    draw()
    root.after(30, update)


def sprite(kind, x, y):
    for row, line in enumerate(SPRITES[kind]):
        for col, pixel in enumerate(line):
            if pixel != ".":
                color = COLORS["d"] if pixel == "d" else COLORS[kind]
                canvas.create_rectangle(x + col * 7 - 7, y + row * 7 - 7, x + col * 7, y + row * 7, fill=color, outline=color)


def draw():
    canvas.delete("all")
    canvas.create_text(10, 15, anchor="w", fill="white", text=f"SAWHNEY  LIVES {game['lives']}/{game['max_lives']}  KILLS {game['kills']}  ${game['money']}  LEVEL {game['level']}")
    for enemy in game["enemies"]:
        sprite("v" if enemy["v"] else "z", enemy["x"], enemy["y"])
        canvas.create_text(enemy["x"], enemy["y"] + 14, text="*" * enemy["hp"], fill="white")
    sprite("p", game["x"], game["y"])
    for shot in game["shots"] + game["bad_shots"]:
        color = "white" if shot in game["shots"] else "#e45c73"
        canvas.create_rectangle(shot[0] - 3, shot[1] - 3, shot[0] + 3, shot[1] + 3, fill=color)
    if game["mode"] == "shop":
        canvas.create_rectangle(80, 120, 720, 420, fill="#111c1f", outline="#96b69d", width=3)
        canvas.create_text(400, 150, text=f"LEVEL {game['level']}: PICK AN AFFORDABLE UPGRADE", fill="white")
        for i, item in enumerate(game["options"]):
            canvas.create_text(400, 220 + i * 55, text=f"{i + 1}. {item['name']}  ${item['cost']}", fill="#f2d579")
    if game["mode"] == "over":
        canvas.create_text(400, 270, text="GAME OVER - PRESS ENTER", fill="white")


def main():
    global root, canvas, game
    root = tk.Tk()
    root.title("Sawhney's Life Part 2")
    canvas = tk.Canvas(root, width=W, height=H, bg="#182629", highlightthickness=0)
    canvas.pack()
    game = {}
    reset()
    root.bind("<KeyPress>", key_down)
    root.bind("<KeyRelease>", key_up)
    canvas.bind("<Motion>", mouse_move)
    canvas.bind("<ButtonPress-1>", lambda event: game.update({"mouse": True}))
    canvas.bind("<ButtonRelease-1>", lambda event: game.update({"mouse": False}))
    root.after(30, update)
    root.mainloop()


if __name__ == "__main__":
    main()
