"""General MIDI program mapping used by the core MIDI writer.

Program values are zero-based MIDI program numbers. For example, GM Acoustic
Bass is program 33 in one-based GM lists and value 32 in raw MIDI bytes.
"""

INSTRUMENT_PROGRAMS = {
    "piano": 0,          # Acoustic Grand Piano
    "bass": 32,         # Acoustic Bass / upright bass foundation
    "upright_bass": 32,
    "electric_bass_finger": 33,
}
