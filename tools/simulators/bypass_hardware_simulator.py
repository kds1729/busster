#!/usr/bin/env python3
"""
BUSSter Hardware Simulator
Scene-Based Bypass Switching

Simulates hardware for scene-based pedal switching with fixed pedal order.

Hardware Concept:
- Fixed pedal chain: INPUT → P1 → P2 → P3 → ... → PN → OUTPUT
- Each pedal has a bypass switch (ON/OFF)
- Scene defines which pedals are active vs bypassed
- Much simpler than full permutation routing!

Switch Implementation:
- 74HC4066 quad bilateral switches (or similar analog switch ICs)
- Silent switching, no mechanical noise
- ~80Ω on-resistance (transparent for guitar signals)
"""

from typing import List, Dict
import sys


class PedalLoop:
    """Represents a single pedal loop with bypass switching."""

    def __init__(self, pedal_num: int, name: str = None):
        self.pedal_num = pedal_num
        self.name = name or f"Pedal {pedal_num}"
        self.is_active = False

    def set_active(self, active: bool):
        """Set pedal active (True) or bypassed (False)."""
        self.is_active = active

    def get_status(self) -> str:
        return "ACTIVE" if self.is_active else "BYPASSED"

    def __repr__(self):
        return f"{self.name}: {self.get_status()}"


class OutputRouter:
    """Represents output routing to multiple amplifiers."""

    def __init__(self, num_outputs: int = 4):
        self.num_outputs = num_outputs
        self.selected_output = 1

    def set_output(self, output_num: int):
        """Select which amplifier output to use (1-based)."""
        if 1 <= output_num <= self.num_outputs:
            self.selected_output = output_num
        else:
            raise ValueError(f"Output must be 1-{self.num_outputs}, got {output_num}")

    def get_output_name(self) -> str:
        output_names = {
            1: "Main Amp",
            2: "Secondary Amp",
            3: "Recording DI",
            4: "Wet/Dry Output"
        }
        return output_names.get(self.selected_output, f"Output {self.selected_output}")


class BUSSTerHardware:
    """Simulates BUSSter hardware with scene-based bypass switching."""

    def __init__(self, num_pedals: int, pedal_names: List[str] = None):
        self.num_pedals = num_pedals

        # Create pedal loops
        if pedal_names and len(pedal_names) >= num_pedals:
            self.pedals = [PedalLoop(i + 1, pedal_names[i]) for i in range(num_pedals)]
        else:
            self.pedals = [PedalLoop(i + 1) for i in range(num_pedals)]

        # Output router (optional)
        self.output_router = OutputRouter(num_outputs=4)

    def configure_scene(self, scene_binary: int, output_num: int = 1) -> Dict:
        """
        Configure hardware for a scene.

        Args:
            scene_binary: Binary representation (LSB = Pedal 1, MSB = Pedal N)
            output_num: Which output to route to (1-4)

        Returns:
            Configuration report dictionary
        """
        # Configure each pedal based on binary scene
        for i, pedal in enumerate(self.pedals):
            is_active = (scene_binary >> i) & 1
            pedal.set_active(bool(is_active))

        # Configure output routing
        self.output_router.set_output(output_num)

        return self._generate_report(scene_binary, output_num)

    def _generate_report(self, scene_binary: int, output_num: int) -> Dict:
        """Generate detailed configuration report."""
        active_pedals = [p.pedal_num for p in self.pedals if p.is_active]
        bypassed_pedals = [p.pedal_num for p in self.pedals if not p.is_active]

        # Build signal flow
        signal_flow = ["INPUT"]
        for pedal in self.pedals:
            if pedal.is_active:
                signal_flow.append(pedal.name)
        signal_flow.append("OUTPUT")
        signal_flow.append(self.output_router.get_output_name())

        # Generate control signals (one bit per pedal)
        control_bits = format(scene_binary, f'0{self.num_pedals}b')

        report = {
            'scene_binary': scene_binary,
            'binary_string': control_bits,
            'active_pedals': active_pedals,
            'bypassed_pedals': bypassed_pedals,
            'signal_flow': signal_flow,
            'output': self.output_router.get_output_name(),
            'pedal_states': [(p.name, p.get_status()) for p in self.pedals],
            'control_signals': self._generate_control_signals(scene_binary)
        }

        return report

    def _generate_control_signals(self, scene_binary: int) -> Dict:
        """Generate hardware control signals."""
        signals = {}

        for i, pedal in enumerate(self.pedals):
            bit_value = (scene_binary >> i) & 1
            signals[f'SW_{i+1}'] = 'HIGH' if bit_value else 'LOW'

        return signals

    def print_configuration(self, report: Dict):
        """Pretty print the configuration."""
        print(f"\nScene Configuration: Binary {report['binary_string']} (Decimal {report['scene_binary']})")
        print("=" * 80)

        print("\nSignal Flow:")
        print("-" * 80)
        print("  " + " → ".join(report['signal_flow']))

        print("\nPedal States:")
        print("-" * 80)
        for name, status in report['pedal_states']:
            symbol = "●" if status == "ACTIVE" else "○"
            print(f"  {symbol} {name:<25} {status}")

        print("\nControl Signals (to microcontroller GPIO):")
        print("-" * 80)
        for signal_name, value in report['control_signals'].items():
            print(f"  {signal_name}: {value}")

        print(f"\nOutput Routing:")
        print("-" * 80)
        print(f"  {report['output']}")


def simulate_hardware_for_pedals(num_pedals: int, pedal_names: List[str] = None):
    """Run hardware simulation for N pedals."""
    print("=" * 80)
    print(f" BUSSTER HARDWARE SIMULATION - {num_pedals} PEDALS (Scene-Based Switching) ")
    print("=" * 80)

    print(f"\nHardware Configuration:")
    print(f"  Pedals: {num_pedals}")
    print(f"  Total Scenes: 2^{num_pedals} = {2**num_pedals}")
    print(f"  Control Signals: {num_pedals} (one per pedal)")
    print(f"  Switch Type: Analog switches (74HC4066 or similar)")
    print(f"  Signal Chain: Fixed order (no reordering)")

    if pedal_names:
        print(f"\nPedal Setup:")
        for i, name in enumerate(pedal_names[:num_pedals], 1):
            print(f"  Pedal {i}: {name}")

    hardware = BUSSTerHardware(num_pedals, pedal_names)

    # Generate some interesting scene examples
    example_scenes = [
        (0, "Bypass all pedals"),
        (2**num_pedals - 1, "All pedals active"),
    ]

    # Add a few specific scenes
    if num_pedals >= 3:
        example_scenes.append((0b00000001, "Only first pedal"))
        example_scenes.append((0b00000101, "First and third pedals"))

    if num_pedals >= 5:
        example_scenes.append((0b00011011, "Custom scene"))

    print(f"\n{'=' * 80}")
    print(f" EXAMPLE SCENE CONFIGURATIONS ")
    print(f"{'=' * 80}")

    for scene_value, description in example_scenes:
        if scene_value < 2**num_pedals:
            print(f"\n{description}:")
            print("-" * 70)
            report = hardware.configure_scene(scene_value)
            hardware.print_configuration(report)


def simulate_song_scenes():
    """Simulate realistic song scene configurations."""
    print("\n\n")
    print("=" * 80)
    print(' REALISTIC EXAMPLE: "Smells Like Teen Spirit" Scene Presets ')
    print("=" * 80)

    pedal_names = [
        "Compressor",
        "Octave",
        "Overdrive",
        "Distortion",
        "Chorus",
        "Phaser",
        "Delay",
        "Reverb"
    ]

    num_pedals = len(pedal_names)
    hardware = BUSSTerHardware(num_pedals, pedal_names)

    # Define song-specific scenes
    song_scenes = [
        {
            'name': 'Scene 1: Clean Intro',
            'binary': 0b10000001,  # Comp + Reverb
            'output': 1,
            'description': 'Clean tone with compression and reverb'
        },
        {
            'name': 'Scene 2: Heavy Chorus',
            'binary': 0b10011001,  # Comp + Dist + Chorus + Reverb
            'output': 1,
            'description': 'Heavy distorted sound with chorus effect'
        },
        {
            'name': 'Scene 3: Verse',
            'binary': 0b10000011,  # Comp + Octave + Reverb
            'output': 1,
            'description': 'Octave pedal for the verse riff'
        },
        {
            'name': 'Scene 4: Lead Solo',
            'binary': 0b11011001,  # Comp + OD + Dist + Delay + Reverb
            'output': 2,  # Route to different amp for lead tone
            'description': 'Full lead tone with delay, routed to high-gain amp'
        }
    ]

    for scene in song_scenes:
        print(f"\n{scene['name']}")
        print("=" * 80)
        print(f"{scene['description']}")
        report = hardware.configure_scene(scene['binary'], scene['output'])
        hardware.print_configuration(report)

    print("\n\nPerformance Workflow:")
    print("-" * 80)
    print("  1. Press 'Next Scene' footswitch → Scene 1 (Clean Intro)")
    print("  2. Press 'Next Scene' footswitch → Scene 2 (Heavy Chorus)")
    print("  3. Press 'Next Scene' footswitch → Scene 3 (Verse)")
    print("  4. Press 'Next Scene' footswitch → Scene 4 (Lead Solo)")
    print("\n  ONE button press per scene change. No tap-dancing!")


def print_hardware_specifications():
    """Print detailed hardware specifications."""
    print("\n\n")
    print("=" * 80)
    print(" HARDWARE IMPLEMENTATION NOTES ")
    print("=" * 80)

    print("\n1. Bypass Switching:")
    print("-" * 80)
    print("  74HC4066 Quad Bilateral Switch (or equivalent)")
    print("    • Silent solid-state switching (no mechanical noise)")
    print("    • ~80Ω on-resistance (transparent for guitar signals)")
    print("    • Microsecond switching speed")
    print("    • Low power consumption")
    print("    • Each IC controls 4 pedal loops")
    print("    • Example: 8 pedals = 2x 74HC4066 chips")

    print("\n2. Control System:")
    print("-" * 80)
    print("  • Microcontroller: ESP32, STM32, or Arduino")
    print("  • GPIO Requirements: 1 pin per pedal + footswitches + display")
    print("  • Memory: Minimal - each scene is just a binary number")
    print("  • Example: 20 pedals with 100 scenes = ~2.5KB storage")

    print("\n3. Audio Quality Considerations:")
    print("-" * 80)
    print("  • Ground loop isolation (critical for large boards)")
    print("  • Buffered input/output stages (optional, add only if needed)")
    print("  • Separate analog and digital power supplies")
    print("  • Shielded audio cables between pedals and loops")
    print("  • Star grounding for audio signals")

    print("\n4. Scaling:")
    print("-" * 80)
    print("  • 8 pedals:  256 scenes, 8 control signals, 2 ICs")
    print("  • 12 pedals: 4,096 scenes, 12 control signals, 3 ICs")
    print("  • 20 pedals: 1,048,576 scenes, 20 control signals, 5 ICs")
    print("  • All are practical with modern microcontrollers!")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "BUSSter Hardware Simulator" + " " * 32 + "║")
    print("║" + " " * 17 + "Scene-Based Bypass Switching System" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Simple example with 3 pedals
    print("EXAMPLE 1: Simple 3-Pedal System")
    simulate_hardware_for_pedals(3, ["Overdrive", "Delay", "Reverb"])

    # Complex example with 8 pedals (realistic)
    print("\n\n")
    print("EXAMPLE 2: Professional 8-Pedal System")
    pedal_names = [
        "Compressor", "Octave", "Overdrive", "Distortion",
        "Chorus", "Phaser", "Delay", "Reverb"
    ]
    simulate_hardware_for_pedals(8, pedal_names)

    # Realistic song example
    simulate_song_scenes()

    # Hardware specs
    print_hardware_specifications()

    print("\n")
    print("=" * 80)
    print(" SIMULATION COMPLETE ")
    print("=" * 80)
    print()
