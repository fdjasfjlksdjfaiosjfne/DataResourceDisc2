(WIP)
# How to synthesize your own collection of discs
### Delete all traces of my data
Delete the following:
- All files in the `assets/textures` folder
- `data/omnidisc.json`
- In `data/data.json5`, delete all entries in the `discs_index` field
### Add metadata in `data.json5`
The `discs_index` field contains almost all metadata for the music discs.
Using 'glass beach - neon glow' as an example, a fully defined entry looks like this:
```json5
{
    id: "glass_beach-neon_glow"
    rpo_id: "glassBeachNeonGlow",
    display_name: "glass beach - neon glow",
    comparator_output: 5,
    length: 233.3,
    range: 65,
    texture_variation_display_name: "neon",
    display_name_variation_display_name: "default",
    mcmeta: {
        animation: {
            frame_time: 2
        }
    },
    display_name_variation: [
        {
            variation_id: "",
            variation_display_name: "",
            display_name: ""
        }
    ],
    texture_alts: [
        {
            variation_id: "",
            variation_display_name: ""
        }
    ],
}
```