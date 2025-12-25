#!/usr/bin/env python3
"""
BUSSter Scene Generator

Generates all possible scene configurations for scene-based switching.

Scene-Based Switching Concept:
- Pedals stay in fixed musical order (no reordering)
- Each pedal can be ON (active) or OFF (bypassed) per scene
- For N pedals, there are 2^N possible scenes
- Much simpler than full permutation routing (N!)

Example with 3 pedals:
  Scene 1:  [P1: OFF] [P2: OFF] [P3: OFF]  = Bypass all
  Scene 2:  [P1: ON ] [P2: OFF] [P3: OFF]  = Only P1
  Scene 3:  [P1: OFF] [P2: ON ] [P3: OFF]  = Only P2
  ...
  Scene 8:  [P1: ON ] [P2: ON ] [P3: ON ]  = All active

Total: 2^3 = 8 scenes
"""

from typing import List, Dict
import math


def generate_all_scenes(num_pedals: int) -> List[Dict]:
    """
    Generate all possible scene configurations.

    Args:
        num_pedals: Number of pedals in the system

    Returns:
        List of scene dictionaries containing pedal states
    """
    total_scenes = 2 ** num_pedals
    scenes = []

    for scene_num in range(total_scenes):
        scene = {
            'scene_number': scene_num + 1,
            'binary': format(scene_num, f'0{num_pedals}b'),
            'pedal_states': {},
            'active_pedals': [],
            'description': ''
        }

        # Generate pedal states from binary representation
        for pedal_idx in range(num_pedals):
            pedal_num = pedal_idx + 1
            # LSB = Pedal 1, MSB = Pedal N
            is_active = (scene_num >> pedal_idx) & 1
            scene['pedal_states'][pedal_num] = 'ON' if is_active else 'OFF'

            if is_active:
                scene['active_pedals'].append(pedal_num)

        # Generate human-readable description
        if len(scene['active_pedals']) == 0:
            scene['description'] = 'Bypass (all pedals OFF)'
        elif len(scene['active_pedals']) == num_pedals:
            scene['description'] = 'Full chain (all pedals ON)'
        else:
            active_str = ', '.join([f'P{p}' for p in scene['active_pedals']])
            scene['description'] = f'Active: {active_str}'

        scenes.append(scene)

    return scenes


def print_scene_table(num_pedals: int) -> List[Dict]:
    """Print formatted scene table."""
    print(f"BUSSter Scene Generator")
    print(f"=" * 80)
    print(f"Pedals: {num_pedals}")
    print(f"Pedal Order: INPUT → Pedal 1 → Pedal 2 → ... → Pedal {num_pedals} → OUTPUT")
    print(f"Total Scenes: 2^{num_pedals} = {2**num_pedals}")
    print()

    scenes = generate_all_scenes(num_pedals)

    # Print table header
    header = f"{'Scene':<8} {'Binary':<12}"
    for p in range(1, num_pedals + 1):
        header += f" P{p:<3}"
    header += f"  Description"
    print(header)
    print("-" * 80)

    # Print each scene
    for scene in scenes:
        row = f"{scene['scene_number']:<8} {scene['binary']:<12}"
        for p in range(1, num_pedals + 1):
            state = scene['pedal_states'][p]
            row += f" {state:<4}"
        row += f"  {scene['description']}"
        print(row)

    return scenes


def print_signal_flow(scenes: List[Dict], num_pedals: int):
    """Print detailed signal flow for selected scenes."""
    print()
    print("=" * 80)
    print("SIGNAL FLOW EXAMPLES")
    print("=" * 80)

    # Show a few interesting scenes
    interesting_scenes = [
        0,                      # Bypass all
        1,                      # Only first pedal
        2 ** num_pedals - 1,    # All pedals
    ]

    # Add middle scene if we have enough pedals
    if num_pedals >= 3:
        interesting_scenes.append(2 ** (num_pedals - 1))  # Only last pedal

    for scene_idx in interesting_scenes:
        if scene_idx < len(scenes):
            scene = scenes[scene_idx]
            print(f"\nScene {scene['scene_number']}: {scene['description']}")
            print("-" * 70)
            print(f"Binary: {scene['binary']}")
            print()
            print("Signal Flow:")

            # Build the signal flow chain
            flow = ["INPUT"]
            for p in range(1, num_pedals + 1):
                if scene['pedal_states'][p] == 'ON':
                    flow.append(f"Pedal {p}")
            flow.append("OUTPUT")

            print("  " + " → ".join(flow))
            print()
            print("Pedal States:")
            for p in range(1, num_pedals + 1):
                state = scene['pedal_states'][p]
                status = "ACTIVE" if state == 'ON' else "BYPASSED"
                print(f"  Pedal {p}: {status}")


def print_complexity_analysis(max_pedals: int = 20):
    """Show complexity comparison: Scene-based (2^N) vs Permutation (N!)."""
    print()
    print("=" * 80)
    print("COMPLEXITY ANALYSIS: Scene-Based Switching vs Full Permutation Routing")
    print("=" * 80)
    print()
    print(f"{'Pedals':<8} {'Scene-Based (2^N)':<25} {'Permutation (N!×e)':<25} {'Ratio'}")
    print("-" * 80)

    for n in range(1, max_pedals + 1):
        scene_based = 2 ** n

        # Calculate permutation routing complexity: floor(n! × e)
        factorial = math.factorial(n)
        permutation = int(factorial * math.e)

        # Calculate ratio
        if scene_based > 0:
            ratio = permutation / scene_based
        else:
            ratio = 0

        # Format large numbers
        if scene_based < 10000:
            scene_str = f"{scene_based:,}"
        else:
            scene_str = f"{scene_based:,.0f}"

        if permutation < 10000:
            perm_str = f"{permutation:,}"
        else:
            perm_str = f"{permutation:,.0f}"

        if ratio < 1000:
            ratio_str = f"{ratio:.1f}x"
        elif ratio < 1000000:
            ratio_str = f"{ratio/1000:.1f}K x"
        else:
            ratio_str = f"{ratio/1000000:.1f}M x"

        print(f"{n:<8} {scene_str:<25} {perm_str:<25} {ratio_str}")

    print()
    print("Key Insights:")
    print("  • Scene-based switching scales MUCH better than permutation routing")
    print("  • 20 pedals: ~1 million scenes (manageable) vs ~66 billion permutations")
    print("  • Scene-based is musically practical - guitarists don't reorder pedals")


def generate_example_song_scenes(num_pedals: int = 8):
    """Generate example scene presets for a song."""
    print()
    print("=" * 80)
    print('EXAMPLE: Scene Presets for "Smells Like Teen Spirit"')
    print("=" * 80)
    print()
    print(f"Pedalboard Setup ({num_pedals} pedals):")
    pedal_names = [
        "Compressor", "Octave", "Overdrive", "Distortion",
        "Chorus", "Phaser", "Delay", "Reverb"
    ]
    for i in range(min(num_pedals, len(pedal_names))):
        print(f"  Pedal {i+1}: {pedal_names[i]}")
    print()

    # Define song scenes
    song_scenes = [
        {
            'name': 'Clean Intro',
            'active': [1, 8],  # Compressor + Reverb
            'description': 'Just compression and reverb for clean intro'
        },
        {
            'name': 'Heavy Chorus',
            'active': [1, 4, 5, 8],  # Comp + Dist + Chorus + Reverb
            'description': 'Heavy distortion with chorus effect'
        },
        {
            'name': 'Verse',
            'active': [1, 2, 8],  # Comp + Octave + Reverb
            'description': 'Octave pedal for the verse riff'
        },
        {
            'name': 'Lead Solo',
            'active': [1, 3, 4, 7, 8],  # Comp + OD + Dist + Delay + Reverb
            'description': 'Full lead tone with delay'
        }
    ]

    print("Song Scenes:")
    print("-" * 70)

    for idx, scene in enumerate(song_scenes, 1):
        print(f"\nScene {idx}: {scene['name']}")
        print(f"  {scene['description']}")
        print(f"  Active Pedals: {', '.join([pedal_names[p-1] for p in scene['active']])}")

        # Generate binary representation
        binary_value = 0
        for pedal_num in scene['active']:
            binary_value |= (1 << (pedal_num - 1))
        binary_str = format(binary_value, f'0{num_pedals}b')

        print(f"  Binary: {binary_str}")
        print(f"  Scene Number: {binary_value + 1}")

    print()
    print("During Performance:")
    print("  Press footswitch to walk through scenes:")
    print("  Clean Intro → Heavy Chorus → Verse → Lead Solo")
    print("  One button press per section. No tap-dancing!")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "BUSSter Scene Generator" + " " * 30 + "║")
    print("║" + " " * 20 + "Scene-Based Switching Simulator" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Generate and display scenes for different pedal counts
    test_cases = [3, 5, 8]

    for num_pedals in test_cases:
        print("\n" + "=" * 80)
        print(f" {num_pedals} PEDALS ")
        print("=" * 80 + "\n")

        scenes = print_scene_table(num_pedals)
        print_signal_flow(scenes, num_pedals)
        print("\n")

    # Show complexity analysis
    print_complexity_analysis(20)

    # Show practical example
    generate_example_song_scenes(8)

    print("\n")
    print("=" * 80)
    print(" SCENE GENERATION COMPLETE ")
    print("=" * 80)
    print()
