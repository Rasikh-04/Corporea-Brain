# demo/

The instructor demonstration: a briefing page and a scripted run of the current build.

| File | What it is |
|---|---|
| `briefing.html` | The briefing. Open it in a browser. Works offline; images are in `shots/`. |
| `run-demo.sh` | The step-by-step runner. Step numbers match the briefing. |
| `slicer/driver.py` | Runs inside Slicer and changes the scene when the runner asks. |
| `fetch-data.sh` | Downloads three public 3D Slicer sample scans into git-ignored `build/demo-data/`. |
| `shots/` | Screenshots of the rehearsal, used by the briefing. |

```bash
demo/fetch-data.sh         # once, online
demo/run-demo.sh --check   # preflight
demo/run-demo.sh --auto    # full rehearsal without prompts
demo/run-demo.sh           # interactive: y next, b back, r repeat, 1 to 11 jump, q quit
```

Every step is labelled PLATFORM (stock 3D Slicer, not our work), OURS (code in this
repository) or MOCK (synthetic data showing a result we have not built yet). Nothing here is
application code and nothing here is a result. The mock attribution step uses made-up region
names on purpose and must never be shown as anatomy.

Two defects of this Slicer build (5.12.3 against system Qt 6 on Fedora 44) that the runner
works around, found on 2026-10-12:

- Opening the Volume Rendering module panel closes the application. Volume rendering itself
  works when driven through the module logic.
- The Segment Editor Smoothing effect raises a `TypeError` when its panel updates.

To refresh the screenshots, run `CORPOREA_DEMO_SHOTS=build/demo-shots demo/run-demo.sh --auto`
and convert the PNGs into `demo/shots/`.
