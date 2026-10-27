# How this was built: a human-led agentic workflow

Most of the code, patches and first drafts in this repo were written by AI agents (Claude Code,
running Claude Opus). I led the work: I chose the goals, set the direction, ran every test on
the hardware, made the judgment calls and decided what shipped. This page describes how that
split worked in practice, because the process is as much the point of this repo as the result.

## Who did what

| Me | The agents |
|---|---|
| Picked the problems and what "done" meant | Researched upstream code, mailing lists and other X1E laptops |
| Pointed research at sources the agents hadn't tried | Read the Windows driver store, ACPI tables and kernel sources |
| Ran several agents in parallel and decided how to split the work | Wrote drivers, patches, device-tree overlays, scripts and docs |
| Required read-only review passes before anything touched the system | Built kernels and modules, ran builds and static checks |
| Did all the hardware testing: reboots, suspends, cold boots, lid tests | Read logs and counters after each test and proposed the next step |
| Reported what I saw (an LED that never lit, a freeze on shutdown, the wake source) | Turned those observations into hypotheses and fixes |
| Made the trade-offs (which route, what to leave alone) and approved risky steps | Wrote undo steps and backups for every boot-critical change |

## Timeline (2026)

Earlier groundwork, August to September: Linux (Parrot OS) booting on the laptop with a community
7.0 kernel, the touchscreen, factory MAC addresses and audio.

| When | Track | Outcome |
|---|---|---|
| Oct 24-25 | Face unlock | IR camera identified, driven and used by Howdy for the lock screen and polkit prompts |
| Oct 25-26 | Deep sleep (in parallel with the touchpad) | Root causes found on 7.0; full SoC deep sleep reached on 7.3 |
| Oct 25-26 | Touchpad cold boot (in parallel with deep sleep) | Root causes found; driver fixes written, reviewed and later built into 7.3 |
| Oct 25 | Integration | A fourth agent reviewed the three tracks together and wrote one combined status |
| Oct 26 | 7.3 kernel | Custom 7.3.0-sl7 kernel built and made the default |
| Oct 26-27 | Publishing | This repo, with curated and scrubbed copies of the work |

## Where human judgment changed the outcome

- **Getting the camera wiring from Windows.** Face unlock started as "can we add face ID to my
  login?". The agent's first answer was that Linux can't use the IR camera: no driver, and
  nobody had published which sensor it is. I suggested pulling the Windows camera driver. That
  gave the sensor model, its power rails, reset GPIO and clock, which made the Linux
  device-tree overlay possible ([IR camera](ir-camera.md),
  [Windows reverse engineering](windows-re.md)).
- **An LED that never lit.** The agent's first guess was that the IR LED hangs off the PMIC
  flash driver. While it was testing that, I stopped it: I had been watching the laptop and the
  LED never came on. It dropped that idea and found that the sensor's own strobe output drives
  the IR LED, in sync with each frame, as Windows does it.
- **Review before running.** Before any new code touched the system, I had a separate read-only
  pass check it. On the touchpad driver port, that review found 10 issues, four of them
  must-fix (see [touchpad](touchpad.md)).
- **Choosing the practical route.** When deep sleep looked like it needed booting Linux at EL2
  (the hypervisor level), I split that research off to a separate agent and kept the main
  agent on the practical route. The practical route won: on the 7.3 kernel, the `deep` sleep
  mode reaches full SoC deep sleep at EL1 ([deep sleep](deep-sleep.md)).
- **Lock screen, not login screen.** I asked how the lock screen and the login screen differ,
  then put face unlock on the lock screen and on polkit prompts, and left the login screen
  alone. A face login would leave the keyring locked.
- **Integration as its own step.** After the three parallel tracks, I had a fresh agent review
  all of them together. It found interactions that no single track could see: two older sleep
  hooks that rebound the touchpad driver on every resume, and one shared initramfs behind every
  boot entry.

## Guard rails

- One change per boot, so a failure has one suspect.
- One-shot GRUB entries for test boots; the next boot returns to the known-good entry.
- Backups and written undo steps before anything boot-critical (DTBs, initramfs, GRUB, PAM).
- Read-only status scripts ([`sl7-status`](../tools/status/), `check-sleep`, `first-boot-check`)
  so every claim can be checked on the machine.
- For publishing: the work was copied file by file, never whole folders, and a scrub check
  ([`tools/dev/scrub-check`](../tools/dev/scrub-check)) runs on every commit and push.

## Attribution in this repo

- Commits in this repo carry a `Co-Authored-By: Claude` trailer.
- Kernel patches follow the kernel's own rule
  ([`Documentation/process/coding-assistants.rst`](https://docs.kernel.org/process/coding-assistants.html)):
  AI help is credited with `Assisted-by:`, and only a human adds `Signed-off-by`.
- Upstream work this builds on is credited in [CREDITS.md](../CREDITS.md) and next to each piece.
