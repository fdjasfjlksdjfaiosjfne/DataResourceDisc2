A little data-driven generator to set up one datapack and two resource packs for Minecraft.

The only reason this is here is so I can use Github Releases to shove in `resource-pack` in my dedicated server's `server.properties`.

If you, for whatever reason, wants to clone this thing or curious on how it works, continue to read. Otherwise, you can leave.

# About the packs

There are three packs that is generated.
- Sound pack: A resource pack that simply contains a bunch of sound files and `sounds.json`, which create sound events.
- Resource pack: A resource pack that...make discs not look like purple checkerboards or vanilla discs. Supports [Respackopts](https://modrinth.com/mod/respackopts). Somehow.
- Data pack: A data pack that adds a UI to apply the disc's music and jukebox song definitions.

# Parts

The actual genarator consists of four script files.
- `main.py`: Run this script to generate the texture pack.
- `respack.py`: Generates the resource pack and the sound pack.
- `datapack.py`: Generates the datapack.
- `config.py`: Contains a typed version of `config.py` so I don't have to deal with a dictionary.

`_test_path.json` contains three paths, that are used to extract directly to a folder, mostly for debugging purposes. I made Git ignored it for...privacy reasons.
`data.json` contains all the other data needed for `main.py`.

There are also three standalone one-off scripts.
- `add-length.json`: Write `length` into song entries in `data.json`. 
- `music/!convert.py`: Re-encodes all music files in its directory to Vorbis `.ogg` files.
- `music/!compress.py`: Compress all Vorbis `.ogg` files and place them in `music/dist`.

# Dependencies
The main generator can run on nothing but the standard library as of Python 3.14.
However, it does accept `json5` to generate `.json5` files, which is used by Respackopts. The `json` package is used instead, if `json5` doesn't exist.
All three one-off scripts require:
- `pydub`: A high-level wrapper for the legendary `ffmpeg` binary. Or `libav`.
- `ffmpeg` or `libav`: Require for `pydub` to work. What, you thought `pydub` just does it for you?
- `audioop-lts`: Require for `pydub` to work. Only nessecary since Python 3.13.

# Quick Start

If you want to run this project from square one (not sure why but ok), here's your first steps.
0. Have a computer that can run Minecraft and Python.
1. Install [Python](https://python.org).
2. Install `ffmpeg`/`libav` if you haven't already.
    - MacOS (Homebrew): `brew install libav` or `brew install ffmpeg`
    - Linux (apt-get): `apt-get install libav-tools libavcodec-extra` or `apt-get install ffmpeg libavcodec-extra`
    - Windows: Install the builds manually, then put the binaries in PATH
3. Skim through this codebase to make sure it doesn't try to install RedLineStealer into your computer.
4. Get this codebase in your computer. Either use `git clone` (requires `git` to be installed) or manually install them by hand if you're a true masochist.
5. Move to the directory where the script files are on and create a new file called `_test_path.json`.
6. Open that file and add the three paths for the three packs. These paths will be used in `debug` mode. You'd usually want to point these to Minecraft's directories for convenient testing. Here's an example for Windows.
    ```json
    {
        "datapack": "C:/Users/User/AppData/Roaming/.minecraft/saves/New World/datapacks/Disc Data Provider",
        "respack": "C:/Users/User/AppData/Roaming/.minecraft/resourcepacks/Disc Art Additions",
        "soundpack": "C:/Users/User/AppData/Roaming/.minecraft/resourcepacks/Disc Music Additions"
    }
    ```
7. Install the necessary dependencies at [Dependencies](#dependencies).
8. Open the terminal on that directory and run `python main.py`

# How to Synthesize Your Own Collection Of Discs
Chances are, if you want to clone this, you want to use this as a baseline to make your own texture pack, with your own collection of music.

You'd only really need to mess with `data.json`, the `music` folder, and the `textures` folder in that case.
### Modifying `data.json`
In `data.json`, you'd be modifying the `discs_index` key, which contains all data relating to sound files.

Deleting all data in that key, and start anew with an empty list...It's not like you'll need my entries, right?

A disc entry with all fields defined looks something like this.
```json
{
    "id": "mili-through_patches_of_violet",
    "config_id": "miliThroughPatchesOfViolet",
    "display": "§5Mili§r - §dThrough Patches of Violet§r",
    "length": 232.832,
    "comparator_output": 9,
    "range": 67,
    "variation_display": "Fancy",
    "mcmeta": {
        "animation": {
            "frame_time": 2
        }
    },
    "alts": [
        {
            "variation_id": "simple",
            "display": "Simple",
            "mcmeta": {
                "animation": {
                    "frame_time": 2
                }
            }
        }
    ]
}
```
The fields are listed below. Note that 
- `id`\*: The internal ID used to identify to the disc internally. It's used almost everywhere except for Respackopts. This ID is compatible with Minecraft's resource location (allow alphabetical characters, numbers, underscores, hyphens, dots). The ID convention used in this codebase is `[artist_name]-[song_name]` or `[artist_name]-[song_name]-[alt_name]` with hyphens as separators of `snake_case` identifiers.
- `config_id`: The internal ID used exclusively in Respackopts, due to its identifier allowing only alphabetical characters. Optional. The generator will generate one for you based on `id` instead if omitted.
- `display`\*: The string used as the display name for the disc. Supports [§-based formatting codes](https://minecraft.wiki/w/Formatting_codes). Does not accept text components.
- `length`\*: The length of the song. You can leave this blank, then run `add_length.py` to add in the lengths for you.
- `range`: The range the song will play relative to the jukebox (radius measured in blocks). Defaults to 64.
- `comparator_output`: Use for determine the comparator output when a jukebox is playing the disc. Defaults to 7.
- `variation_display`: The string used as the display name for the default disc variant in the Respackopts config. Supports [§-based formatting codes](https://minecraft.wiki/w/Formatting_codes). Does not accept text components. Defaults to `"default"`.
- `mcmeta`: The JSON to put in its corresponding `.mcmeta` file. This is how you get animated textures btw.
- `alts`: A list containing the alternative visual appearance of discs, configurable via Respackopts. An empty list by default.
    - `variation_id`\*: The internal ID used to identify the alt. This is appended to the disc's ID. With the above example, the full ID for the variation `simple` would be `mili-through_patches_of_violet-simple`.
    - `display`\*: Same as `variation_display` on the root.
    - `mcmeta`: Same as `mcmeta` on the root.

### Sound files
Well, you just need to dump all of your sound files over the `music` directory, right?

Almost.

First of all, after dumping all of your music files there, open and run the `!convert.py` file, which will re-encode the files to Vorbis `.ogg` files. You can try and modify some arguments if needed.

Then, you can open and run the `!compress.py` which will compress the file (unless `COMPRESS` is set to `False`) and move them to `music/dist`, which is where the generator will grab the file from.

Why compress? The `resource-pack` file only accepts a maximum of 250MB. And I have a fuck lot of audio files. That's why.

Note that, the generator will use the disc ID to find the music, so remember to rename them so that the generator can find them.

### Textures

> **Note:** ***Do not delete the `missing.png` file.*** This file is used for replace missing texture files. If you delete `missing.png`, the generator will not check for its absence and it *will* crash if it's needed. If you accidentally delete it though, just shove in a random image as a replacement. The content isn't important (just needs to be a valid PNG), its existence is.

Somewhat same deal here.

Except there's no script. You just dump the `.png`s directly into the `textures` file.

The generator uses the song ID and variation ID to find the right texture. So again, rename them accordingly (e.g. `mili-through_patches_of_violet.png` or `mili-through_patches_of_violet-simple.png`) and you're golden.

# FAQ

"Frequently Asked Questions"? More like, "questions that I have a feeling some guy, if there is one at all, may asked after take a look at this crappy codebase".
But the acronym "QTIHAFSGITIOAAMAATALATCC" isn't very memorable nor familiar, so anyway:

##### Why is the `music/` folder empty?

A few music here are not royalty-free and/or not allowed to distribute freely as a music file on some random repo. I just make Git ignore all of them in the source. I'm not taking any chances.
If you do want to do what music is used in my server though, look at `data.json`.

##### I just look at your list. What the hell is your music taste?

The list here is a collection of multiple people's tastes. I don't judge any of their tastes and yet you do. Get a grip.

##### Can I join your server?

No.

##### What does it look like?

Shove them in Minecraft and check it for yourself.
It's not gonna infect your computer or anything. They're just resource packs and data packs.
Unless Minecraft has a CVE I'm not aware of. But I'm not aware of it either way so it's fine.

##### Why split into two resource packs?

As of now, the sound files have exceed 40MB+, and will only increase in the future, so I decided to split it so I can send the resource pack with the visuals on Discord (which are updated more frequently).
Why wouldn't I move the textures over as well? Respackopts would be no use otherwise.

##### Does this generator have OptiFine support?

This pack generator currently does not generate any OptiFine/MCPatcher files since I found no use for it, for now.

##### Can you add \[insert music name here]?

If you play on my server, sure. Otherwise, clone the repo and do it yourself.
Look into [this section](#how-to-synthesize-your-own-collection-of-discs) for an explanation on how to do it.

##### Can you tell me how the code works?

Ask AI.

##### Can a custom disc fall back to a vanilla texture?

Not at the moment.

##### What version of Python is this thing running on?

Python 3.14.0, any questions?

##### Can this run on older Python 3.x versions?

Possibly. The older the version, the less likely it gets.

##### Can this run on Python 2.x?

No.

##### Why are there two separate scripts for converting and compressing?

They are made at two different time periods. I can't be bothered to merge them.

##### Can you port this pack to \[insert Minecraft version here]?

Only if *my* server moves to that version. Otherwise, no.

##### Why don't you use TOML for `data.json` and `_test_path.json`?

Actually...yea you might be right.
The structure is *somewhat similar* to what TOML would be written in as well.
But welp, JSON is already done, so it is here to stay.
(And also, i guess, less dependencies? Minecraft uses JSON anyway.)

##### Some names here are pretty goofy, why is that?

Fun isn't forbidden.

##### Would you switch to TOML in that case?

Mayhaps.

##### Can you port this pack to Bedrock?

No.

##### How do you get the soundpack's SHA-1?

Open `data.json` and set `mode` to `release`. The SHA-1 will be printed in the console.

##### How to build or clone this repo?

Do it yourself.

##### Who made the textures?

Me and my friend. Neither are proficient at pixel art, but one is definitely better than the other.

##### What software do you two use to make textures?

Me: Piskel, now Aseprite (build from source) bc why not?
Him: idrk some app on Steam that looks like an old Android app escaping containment.

##### What texture files in here are free to use?

The ones that you don't want to use.
(Ok for real, idk how my friend would want his assets be handled so...)

##### Are you or your friend willing to make new textures for me?

Me: Sorry, no. Even with money. I have things to do.
Him: Not any time soon.

##### Are there any license for this?

This is meant to be used for personal purposes, but if you insist...

Music files: Belong to the respective artists.
Texture files: Ehhhhhhhhhhhhhhhhhh...Not sure why you'd need it unless you have the same music interest as us anyway...
Code: Go on and use them. Credits would be nice (and don't you dare mispell my beautiful name 😈) but I really don't care at the end of the day.

##### Is AI used in the process of this project?

All lines of code are written by me.
I do ask ChatGPT sometimes when I can't figure out a bug in the generator. But I still write the code *by myself* to my understanding afterwards.
The textures are completely AI-free. Can AI even generate 16x16 pixel art in the first place? I can't tell.

##### How long did this took?

One or two weeks, mostly working on-and-off, and adding random features.
Plus one sleepless night to implement Respackopts.

##### Do you really need to write this README down?

No. I do anyway, and there's nothing you can do about it.
Best and worst 6 hours of my life.