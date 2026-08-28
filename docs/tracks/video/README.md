# Video track

**Status: planned; not implemented yet.**

The Video track will test whether an agent can infer motion—not just reproduce isolated images. A task will provide a small set of frames sampled from a short reference clip. The agent will construct a smooth, approximately 30 fps animation that remains faithful between the observed frames.

## Intended challenge

The agent will need to recover object shapes, timing, trajectories, layering, and transformations from sparse evidence. A strong result should preserve both the appearance of individual frames and the continuity of motion across the entire clip.

Evaluation is expected to combine:

- appearance and geometry at observed and hidden timestamps;
- motion and trajectory accuracy;
- temporal consistency and flicker;
- duration, frame rate, dimensions, and encoding validity.

Video will reuse MimesisGym's fresh-context episode runner and isolated sandbox contract. Its precise task format, tools, codec policy, and reward are still to be designed; there are currently no runnable Video commands.

Return to the [project overview](../../../README.md) or explore the implemented [Image track](../image/README.md).
