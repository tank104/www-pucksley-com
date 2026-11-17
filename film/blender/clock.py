"""When things happen in the Pucksley film, in film seconds. The one place to change the film's timing: the
picture (film.py), the voices (film_voice.py), the music (film_music.py), the effects (film_effects.py) and
the join (film_join.py) all read it.

The film is one shot and one day: the card house on the real kitchen bench, from first light to lights
out. Each beat is something said to the puck, and the house answering in light.
"""
# when each beat starts: the moment the puck is tapped and starts to listen
BEAT = {
    'weather': 2.6,      # "What's the weather doing this afternoon?"
    'music': 9.8,        # "Play some jazz in the kitchen."            the kitchen lights yellow, notes rise
    'turn': 16.4,        # (no words: the puck is turned)               louder
    'group': 19.8,       # "Group the kitchen with the ensuite."        the ensuite lights too
    'timer': 25.8,       # "Set a timer for pasta. Ten minutes."        the ring starts
    'done': 32.0,        # (the timer finishes)                         a chime, a banner
    'tv': 35.8,          # "Turn off the downstairs TV."                the lounge's blue goes out
    'lamp': 40.8,        # "Lamp on."                                   a warm light in the lounge
    'heating': 44.8,     # "Turn the heating up half a degree."         terracotta under every floor
    'pc': 50.8,          # "Shut down the PC."                          it asks first; a turn for yes; the study goes dark
    'night': 57.8,       # "Everything off. Good night."                the rooms go out; the heating stays
}
END = 64.0               # the last frame of the shot
CARD = 4.0               # the closing card, after it
FADE = 0.8               # the shot fades into the card over this long

# the day's light
SUNRISE = 1.5            # the first sun reaches the bench
MIDDAY = (21.5, 24.0)    # the sun leaves the morning window, and comes back through the afternoon one
SUNSET = (38.5, 42.0)    # the afternoon sun goes
