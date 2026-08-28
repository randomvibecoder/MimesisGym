# 3D track

**Status: planned; not implemented yet.**

The 3D track will test whether an agent can infer a coherent object from several 2D views. A task will provide rendered images from known viewpoints, and the agent will construct a portable 3D asset that can be inspected from directions it never saw.

## Intended challenge

The agent will need to reconcile silhouettes, depth, proportions, materials, and occluded structure across multiple observations. The evaluator will render the submitted asset under controlled cameras and lighting, including hidden viewpoints.

Evaluation is expected to combine:

- silhouette and geometry agreement;
- hidden-view consistency;
- material and color appearance;
- topology and artifact validity;
- scale, orientation, and coordinate-system compliance.

3D will reuse MimesisGym's fresh-context episode runner and isolated sandbox contract. Its precise asset format, rendering engine, camera protocol, and reward are still to be designed; there are currently no runnable 3D commands.

Return to the [project overview](../../../README.md) or explore the implemented [Image track](../image/README.md).
