# Genesis

The creation of the world, Genesis 1:1 to 2:3, as a Minecraft experience for VR.

It begins in darkness over the deep. A narrator reads the text verse by verse, and after each verse the
world does what was said: light, the firmament, land rising from the sea, plants, the sun, moon and stars,
the creatures of the sea and the air, the beasts of the earth. At "male and female created he them" you wake
as Adam or Eve. When the seventh day is blessed the world is yours: walk it, and name every animal. The one
you did not choose stands beside you, played by Claude, and speaks.

## Play

1. `.\start.ps1` (add `-NewWorld` to begin again from the darkness). This opens the local server and the companion.
2. Minecraft launcher, profile **Genesis VR**, Play. For the headset, start SteamVR first and switch Vivecraft to VR.
3. Multiplayer, **Genesis**. Stand on the gold stone to be Adam, the diamond stone to be Eve.

A second player can join the same server and take the other part; then there is no companion.

To name a creature, look at it and say what it shall be called. Every creature of that kind carries the name
from then on.

## What is here

| Path | What it is |
|---|---|
| `tools/build_datapack.py` | Generates the whole datapack: the island, the scripted sky, the timed intro |
| `datapack/genesis` | The generated datapack |
| `pack/genesis-resources` | Resource pack with the narration |
| `companion/bridge.py` | The companion: microphone, Claude, voice, and the link to the game |
| `companion/companion.py` | The character and voice on their own, for testing |
| `characters.md` | Who Adam and Eve are; this is the companion's brief |
| `cue-sheet.md`, `narration-script.md` | What happens at each verse, and the text as read |
| `tools/server.ps1`, `tools/rcon.py` | Run the server and talk to it |
| `tools/visual_test.py` | Plays the intro in a desktop client and saves screenshots |
| `work/*.py` | How the narration was cut, cleaned and given its voice |

## How it works

- **Minecraft 26.3**, Fabric, [Vivecraft](https://modrinth.com/mod/vivecraft) for VR. None of those are in this repository.
- The world is a flat sea in its own biome with no natural spawning. The island is generated in Python and
  raised layer by layer with `fill` commands.
- The sky is scripted with a custom timeline on a custom world clock: three days of light with no sun, the
  first sunrise on the fourth day, then an ordinary day that repeats. A second timeline lays the opening
  darkness, the mist and the clouds over it.
- The companion is a mannequin entity. A Python process listens on the microphone (Silero VAD, Whisper),
  asks Claude for the reply in character, speaks it with Chatterbox, and names creatures through the
  server's remote console.
- Only animals that live peaceably together were made: no wolves, foxes or cats.

## Rebuilding

`tools/build_datapack.py` needs the verse clips in `verses/dry` (for their lengths) and the vanilla data
reports in `work/mcdata`, made with the server jar's data generator. Python comes from the
`D:\voice-assistant` environment (faster-whisper, chatterbox-tts, silero-vad, sounddevice).
