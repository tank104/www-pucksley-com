# Pucksley film: script and shot list, draft 1 (2026-11-17)

**One shot, one day, about 68 seconds.** A white card model of a house stands on the real kitchen bench
among the real things (a pot, a cup, a plant), with the puck in front of it. Somebody talks to the puck
from first light to lights out, and the house answers in light. Nothing in the house has any colour until
it does something: yellow for music, blue-white for screens, a warm lamp, terracotta for the heating.

The times below are the plan; the film's real times are in `blender/clock.py`, which the picture, the
voices, the music and the effects all read.

## Decided (2026-11-17)

- **The idea:** option C of the three mixes of "One puck, the whole house" and "A day on the bench": both
  at once, no cut.
- **Where it is going:** the website, GitHub and social first, and Kickstarter too. So the puck is a render
  for now and has to stay swappable: Kickstarter does not allow photorealistic renders of the product, and
  that version needs the puck filmed.
- **Voices:** a person asks (ElevenLabs "Brian"), the puck answers (Azure "Annette", the voice the real puck
  speaks with by default). Both are AI voices.
- **Music:** there is none until somebody asks for it. The score is what the house is playing.
- **The puck's screen while it answers** is the talking face, the plugin's default face (the user,
  2026-11-17: "show the AI character when responding, not claude asterix logo"). It moves with the words:
  `blender/face_capture.py` has Openspline animate it to each of Annette's lines, as the hub does live.
  After the line the screen goes to what was asked for. The brief "thinking" screen is gone too ("get rid
  of brief flash of spark too"). The spark is still on the clock and the listening screens.
- **The film's own screens:** `firmware/tools/sim/build/sim.exe film` in the product repository (NimbleHive/Pucksley) draws the ones this script needs
  (06:42 on the morning clock, "Simply Joyful" playing, the timer at 9:57, the banner at 17:38).
- **The puck springs back upright** after it is turned. The real one stays where it is left, and its screen
  with it; in the film a face lying on its side read badly.

## Shot list

`Y` you, `P` the puck. Every beat starts with a tap on the puck.

| Time | Light | Said | The puck's screen | The house |
|---|---|---|---|---|
| 0:00 | Before dawn, then the first sun through the back window. Birds. | | The clock | White and still |
| 0:03 | Morning | Y: "What's the weather doing this afternoon?" P: "Clearing by two. Take a jacket till then." | Listening, then the answer | Nothing: it is an assistant first |
| 0:10 | | Y: "Play some jazz in the kitchen." P: "Jazz, in the kitchen." | What is playing | The kitchen lights yellow; notes rise out of its speaker. **The music starts here**, small |
| 0:16 | | (the puck is turned) | Volume, 42 | The kitchen brightens, the notes grow, the music is louder and fuller |
| 0:20 | Towards midday | Y: "Group the kitchen with the ensuite." P: "Done. Both rooms." | What is playing | The ensuite upstairs lights yellow too |
| 0:26 | Afternoon, the sun now through the side window | Y: "Set a timer for pasta. Ten minutes." P: "Ten minutes. Starting now." | The timer's ring | The camera is down by the puck and the real pot |
| 0:32 | | P: "Your pasta's ready." (a chime) | "Your pasta timer is done" | The television and the study's screen have come on in the meantime |
| 0:36 | Late afternoon, the light going warm | Y: "Turn off the downstairs TV." P: "It's off." | TV · Lounge TV off | The lounge's blue goes out |
| 0:41 | Sunset | Y: "Lamp on." | Lamp · On | A warm lamp in the lounge |
| 0:45 | Night. Crickets. | Y: "Turn the heating up half a degree." P: "Twenty-one and a half." | Heating, 21.5 | Terracotta under every floor, a room at a time |
| 0:51 | | Y: "Shut down the PC." P: "Shut down the PC? Turn for yes." (the puck is turned, and tapped) | Confirm: No / Yes | The study's screen goes dark |
| 0:58 | | Y: "Everything off. Good night." P: "Good night." | The clock | The music stops; the rooms go out; the heating stays |
| 1:04 | | | | Card: **Pucksley** · A voice assistant you can hold. |

## Sound

- **Music:** "Simply Joyful" by William Claeson (Epidemic Sound), chosen from its tags, not by ear. It
  starts as one small speaker, opens out when the puck is turned, and stops with "Everything off".
- **Effects:** a tap on glass for every time the puck starts listening, the dial's clicks, the timer's
  chime, the television, a light switch, the heating clicking on, the PC shutting down. Birds until the
  music is under way; crickets from sunset to the end.

## Still open

- **Hands.** Nobody is seen tapping or turning the puck: it turns by itself.
- **The real puck's colour.** The render's case is black anodised aluminium, which is a guess.
- **Check on the real puck** that every beat works as shown: grouping two Sonos rooms by voice, the TV, a
  lamp on a plug, the heating by half a degree, the PC shutdown asking first, and "everything off".
- **Kickstarter version:** the puck filmed, not rendered.
- **The spark** is still on the clock and listening screens.
