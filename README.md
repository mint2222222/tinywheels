# Tiny Wheels 🌸

A tiny racing game that runs entirely in your terminal. You drive a little white-and-black
AE86-style hatchback down a snowy road lined with sakura trees, under falling petals and
snowflakes, with Mt. Fuji on the horizon.

- Pseudo-3D "OutRun style" road with curves and hills, drawn with `▀` half-blocks in 24-bit color
- A new random track every race
- Ramps to jump, and stone lanterns, rocks and pine trees to avoid
- **3 LAPS** mode: race 3 laps for the fastest time
- **INFINITE** mode: an endless road. Torii-gate checkpoints add time, and you score points for distance, drifting and jumps
- Your records are saved and shown during the countdown, best first
- Pure Python standard library, nothing to install, uses about 15 MB of RAM

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
| 1 / 2          | Pick 3 LAPS / INFINITE on the title screen  |
| Enter          | Play again (after you finish)               |
| M              | Back to the title screen                    |
| Q / Esc        | Quit                                        |

Run `tinywheels --help` to see the controls in the terminal.

## How to play

- **Yellow-black stripes** are ramps: drive over them fast to jump.
- **Lanterns, rocks and pine trees** on the road slow you down. So does the deep snow off the road.
- **3 LAPS:** fastest total time wins.
- **INFINITE:** you start with 30 seconds. Every red torii gate is a checkpoint that adds time.
  You score points for distance (double while drifting, which means steering hard at high speed) and
  for jumps. Keep going until time runs out.

Records are saved in `~/.local/share/tinywheels/` (`records.txt` for lap times,
`infinite.txt` for scores).

## License

MIT, see [LICENSE](LICENSE).
