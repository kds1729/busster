# BUSSter Simulators

Simulation tools for the BUSSter guitar effects routing system.

## Overview

BUSSter uses **scene-based switching** with fixed pedal order. These simulators demonstrate how scenes are generated and how hardware control signals work.

## Files

### 1. `scene_generator.py`

Generates all possible scene configurations for N pedals.

**Concept:**
- Fixed pedal chain: INPUT → P1 → P2 → ... → PN → OUTPUT
- Each pedal: ON (active) or OFF (bypassed)
- Total scenes = 2^N

**Usage:**
```bash
python3 scene_generator.py
```

**Output:**
- Scene tables for 3, 5, and 8 pedals
- Signal flow examples
- Complexity analysis (2^N vs N!)
- Song example presets

### 2. `bypass_hardware_simulator.py`

Simulates hardware control for scene-based bypass switching.

**Hardware:**
- 74HC4066 Quad Bilateral Switch
- One control bit per pedal (HIGH = ON, LOW = OFF)

**Usage:**
```bash
python3 bypass_hardware_simulator.py
```

**Output:**
- Hardware configuration details
- Scene control signals
- Signal flow visualization
- Bill of materials

### 3. `HARDWARE_DESIGN.md`

Complete hardware implementation guide with schematics, wiring diagrams, and BOM.

## Quick Start

```bash
# Generate scenes
python3 scene_generator.py

# Simulate hardware
python3 bypass_hardware_simulator.py
```

## Hardware Requirements (8 Pedals)

- 2x 74HC4066 ICs (~$1)
- 1x ESP32 or Arduino (~$10)
- 1x OLED display (~$5)
- Footswitches, jacks, enclosure (~$50)
- **Total: ~$100** (vs $700-1500 commercial)

## History

- **December 2019**: Original concept
- **December 23, 2025**: Pivot to an open source project

---

*Created by Keith D. Sprochi, Pompano Beach, Florida USA*
