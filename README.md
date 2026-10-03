# Tiny Wheels 🌸

A tiny racing game that runs entirely in your terminal. You drive a little white-and-black
AE86-style hatchback down a snowy road lined with sakura trees, under falling petals and
snowflakes, with Mt. Fuji on the horizon.

- Pseudo-3D "OutRun style" road with curves and hills, drawn with `▀` half-blocks in 24-bit color
- A new random track every race
- Ramps to jump, and stone lanterns, rocks and pine trees to avoid
- A day and night cycle: sunrise, a red sun, sunset, then a moon and stars. At night your
  headlights light up the road ahead, the taillights glow (brighter when you brake), and
  lanterns, house windows and shops shine warmly
- Cozy roadside details: sakura trees, stone lanterns, little wooden houses, vending machines,
  festival lantern strings across the road, and a pagoda by Mt. Fuji
- **3 LAPS** mode: race 3 laps for the fastest time
- **GARAGE**: start with the AE86 and unlock more iconic Japanese cars with easy challenges:
  Mazda RX-7 FD, Honda NSX, Toyota Supra MK4, Nissan Skyline GT-R R34 and Subaru Impreza WRX
- **INFINITE** mode: an endless road. Torii-gate checkpoints add time, and you score points for distance, drifting and jumps.
  Pass 20,000 points and convenience stores (konbini) start to appear along the road
- **DRIFT** mode: an Initial D-style downhill mountain pass through a forest of pines and sakuras
  (no snow here). A lower drift-cam shows the car turned sideways in a cloud of tire smoke.
  Points build up while you slide, linked drifts raise a combo up to x5, and hitting the guardrail loses the drift
- Your records are saved and shown during the countdown, best first
- Pure Python standard library, nothing to install, uses about 200 MB of RAM

Inspired by the Roblox game *Tiny Wheels* (not affiliated).

## Requirements

- Linux (or macOS) with **Python 3.8+**. On Arch Linux: `sudo pacman -S python`
- A terminal with 24-bit color: Ghostty, kitty, Alacritty, foot, WezTerm, GNOME Terminal, Konsole…
- Best in terminals that support the kitty keyboard protocol (Ghostty, kitty, Alacritty, foot, WezTerm),
  because they report key releases. Other terminals work too, but the controls feel a bit less precise.

## Install

```sh
git clone https://github.com/mint2222222/tinywheels.git ~/tinywheels
cd ~/tinywheels
./install.sh
```

Then type `tinywheels` from anywhere to play.

The installer adds a link at `~/.local/bin/tinywheels` that points to the game in the folder you
cloned, so **keep that folder**. If `~/.local/bin` isn't in your `PATH`, the installer tells you
which line to add.

## Update

```sh
cd ~/tinywheels
git pull
```

That's all you need: the command points to the cloned folder, so updates take effect right away.

## Uninstall

```sh
cd ~/tinywheels
./install.sh --uninstall
```

Then delete the folder if you want (`rm -rf ~/tinywheels`). Your records are kept in
`~/.local/share/tinywheels/`. Delete that folder too to remove them.

## Controls

| Key            | Action                                      |
|----------------|---------------------------------------------|
| ↑ / W          | Speed up                                    |
| ↓ / S          | Brake                                       |
| ← → / A D      | Steer                                       |
| Space          | Handbrake: throw the car into a drift (DRIFT mode) |
| 1 / 2 / 3      | Pick 3 LAPS / INFINITE / DRIFT on the title screen |
| 4              | Open the GARAGE (← → to look, Enter to choose, Esc / M to go back) |
| Enter          | Play again (after you finish)               |
| M              | Back to the title screen                    |
| Q / Esc        | Quit                                        |

Run `tinywheels --help` to see the controls in the terminal.

## How to play

- **Yellow-black stripes** are ramps: drive over them fast to jump.
- **Lanterns, rocks and pine trees** on the road slow you down. So does the deep snow off the road.
- **3 LAPS:** fastest total time wins.
- **INFINITE:** you start with 40 seconds. Every red torii gate is a checkpoint that adds time.
  You score points for distance (double while drifting, which means steering hard at high speed) and
  for jumps. Keep going until time runs out.

- **DRIFT:** hold **Space** and steer into a corner to throw the tail out. Keep steering into it with
  the gas held to hold the drift, and steer the other way to straighten up. Your drift points are added to
  your score when you straighten out without hitting anything. Chain drifts quickly for a bigger combo.

### Cars to unlock

| Car | How to unlock it |
|---|---|
| Toyota AE86 Trueno | You start with it |
| Mazda RX-7 FD | Finish a 3 LAPS race |
| Honda NSX | Finish 5 races (any mode) |
| Toyota Supra MK4 | Score 3000 in INFINITE |
| Nissan Skyline GT-R R34 | Score 2000 in DRIFT |
| Subaru Impreza WRX | Get a x3 combo in DRIFT |

Records are saved in `~/.local/share/tinywheels/` (`records.txt` for lap times,
`infinite.txt` and `drift.txt` for scores, `progress.json` for your cars).

## License

MIT, see [LICENSE](LICENSE).
