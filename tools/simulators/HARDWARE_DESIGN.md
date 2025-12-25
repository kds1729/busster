# BUSSter Hardware Design
## Scene-Based Bypass Switching

## Hardware Architecture

### Core Concept

**Fixed pedal chain with individual bypass switching:**
- Pedals remain in fixed order, no order-based routing at first
- Each pedal can be ON (active) or OFF (bypassed)
- Scene = combination of pedal ON/OFF states
- Simple, silent, effective!

### System Design

For **N pedals**, you need:
- **N bypass switches** (one per pedal)
- **1 microcontroller** (ESP32, STM32, or Arduino)
- **1 display** (OLED for scene names)
- **Footswitches** (scene next/previous, bank selection)

## Bypass Switching - 74HC4066

### IC Specifications
- **74HC4066 Quad Bilateral Switch**
- **4 independent analog switches** per IC
- **Control:** HIGH = ON, LOW = OFF (per switch)
- **On-resistance:** ~80Ω typical
- **Bandwidth:** > 40 MHz (way more than needed for audio)
- **Silent switching:** No mechanical noise

### Signal Path

```
GUITAR INPUT
     │
     ▼
┌────────────────────┐
│  PEDAL 1 LOOP      │
│  ┌──────────────┐  │
│  │ 74HC4066 SW1 │  │
│  └──────┬───────┘  │
│         ▼          │
│    [PEDAL 1]       │  ◄── If SW1=ON, signal goes through pedal
│         │          │      If SW1=OFF, signal bypasses pedal
│         ▼          │
└────────┼───────────┘
         │
         ▼
┌────────────────────┐
│  PEDAL 2 LOOP      │
│  ┌──────────────┐  │
│  │ 74HC4066 SW2 │  │
│  └──────┬───────┘  │
│         ▼          │
│    [PEDAL 2]       │
│         │          │
│         ▼          │
└────────┼───────────┘
         │
         ▼
        ...
         │
         ▼
┌────────────────────┐
│  PEDAL N LOOP      │
│  ┌──────────────┐  │
│  │ 74HC4066 SWN │  │
│  └──────┬───────┘  │
│         ▼          │
│    [PEDAL N]       │
│         │          │
│         ▼          │
└────────┼───────────┘
         │
         ▼
   AMPLIFIER OUTPUT
```

## Scene Examples

### Example 1: All Bypass (Scene 0)
```
Control Word: 00000000 (8 pedals)

Signal Flow:
  INPUT → [bypass all] → OUTPUT

All switches: OFF
Result: Clean, direct signal
```

### Example 2: Only Distortion (Scene 4)
```
Control Word: 00000100 (8 pedals)

Pedals in order: Comp, Oct, OD, Dist, Chorus, Phaser, Delay, Reverb
Binary:          0    0    0   1     0       0       0      0

Signal Flow:
  INPUT → [bypass Comp] → [bypass Oct] → [bypass OD]
       → [THROUGH Dist] → [bypass Chorus] → [bypass Phaser]
       → [bypass Delay] → [bypass Reverb] → OUTPUT

Only Distortion is active!
```

### Example 3: Full Lead Tone (Scene 217)
```
Control Word: 11011001 (8 pedals)

Pedals:  Comp  Oct  OD  Dist  Chorus  Phaser  Delay  Reverb
Binary:   1    0    0   1      1       0       1      1

Signal Flow:
  INPUT → [THROUGH Comp] → [bypass Oct] → [bypass OD]
       → [THROUGH Dist] → [THROUGH Chorus] → [bypass Phaser]
       → [THROUGH Delay] → [THROUGH Reverb] → OUTPUT

Lead tone with compression, distortion, chorus, delay, and reverb!
```

## Control System Wiring

### Microcontroller to Switch ICs

```
Microcontroller (ESP32/STM32/Arduino)
┌─────────────────────────────────────┐
│  GPIO Pins:                         │
│                                     │
│  GPIO_0  ──► SW1 (Pedal 1 bypass)  │
│  GPIO_1  ──► SW2 (Pedal 2 bypass)  │
│  GPIO_2  ──► SW3 (Pedal 3 bypass)  │
│  GPIO_3  ──► SW4 (Pedal 4 bypass)  │
│  GPIO_4  ──► SW5 (Pedal 5 bypass)  │
│  GPIO_5  ──► SW6 (Pedal 6 bypass)  │
│  GPIO_6  ──► SW7 (Pedal 7 bypass)  │
│  GPIO_7  ──► SW8 (Pedal 8 bypass)  │
│                                     │
│  + Footswitch inputs (GPIO_8-12)   │
│  + Display interface (I2C/SPI)     │
│  + Power management                │
│                                     │
└─────────────────────────────────────┘
```

### IC Count

| Pedals | 74HC4066 ICs | Control Pins |
|--------|--------------|--------------|
| 4      | 1            | 4            |
| 8      | 2            | 8            |
| 12     | 3            | 12           |
| 16     | 4            | 16           |
| 20     | 5            | 20           |

**One IC handles 4 pedals.**

## Scene Storage

### Memory Requirements

Each scene stores:
- **Pedal states:** 1 bit per pedal (packed into bytes)
- **Scene name:** ~16 characters
- **Output routing:** 1 byte
- **Total:** ~20 bytes per scene

**Examples:**
- 8 pedals, 50 scenes = 1 KB
- 12 pedals, 100 scenes = 2 KB
- 20 pedals, 200 scenes = 4 KB

**All easily fit in microcontroller flash memory!**

### Scene Data Structure (C)

```c
typedef struct {
    char name[16];           // "Clean Intro", "Heavy Chorus", etc.
    uint32_t pedal_states;   // Binary: each bit = one pedal ON/OFF
    uint8_t output_routing;  // Which amp output (1-4)
    uint8_t reserved[3];     // Future expansion
} Scene;

// Example: 8 pedals, Comp + Dist + Reverb active
Scene scene1 = {
    .name = "Lead Tone",
    .pedal_states = 0b10001001,  // Reverb + Dist + Comp
    .output_routing = 1,
    .reserved = {0, 0, 0}
};
```

## Bill of Materials (8 Pedals)

| Part | Quantity | Est. Cost | Purpose |
|------|----------|-----------|---------|
| 74HC4066 | 2 | $1.00 | Bypass switches (4 pedals each) |
| ESP32 Dev Board | 1 | $10.00 | Microcontroller |
| 0.96" OLED Display | 1 | $5.00 | Scene name display |
| Footswitches | 4 | $12.00 | Next/Prev scene, Bank up/down |
| 1/4" Jacks | 18 | $18.00 | 16 for pedal loops, 2 for I/O |
| Enclosure | 1 | $20.00 | Project box |
| Power Supply | 1 | $10.00 | 9V DC to 5V/3.3V regulators |
| Misc (PCB, wire, etc.) | 1 | $24.00 | Resistors, caps, connectors |
| **TOTAL** | | **~$100** | **For 8-pedal system** |

**Much cheaper than commercial units ($700-1500)!**

## Audio Quality Targets

- **THD (Total Harmonic Distortion):** < 0.01% @ 1kHz
- **Noise Floor:** < -100dBu
- **Frequency Response:** 20Hz - 20kHz ±0.5dB
- **Crosstalk:** < -80dB between loops
- **Switching Noise:** Silent (solid-state, no pops)

The 74HC4066 easily meets these specs for guitar signals!

## Power Considerations

- **Control logic:** ~100mA (ESP32 + display)
- **Switching ICs:** ~1mA per IC
- **Total:** < 150mA @ 5V
- **Power source:** Standard 9V DC pedal power supply

## Scaling Analysis

| Pedals | Scenes (2^N) | ICs | GPIO | Memory (100 scenes) | Feasibility |
|--------|--------------|-----|------|---------------------|-------------|
| 3      | 8            | 1   | 3    | 200 bytes           | ✅ Trivial   |
| 8      | 256          | 2   | 8    | 2 KB                | ✅ Easy      |
| 12     | 4,096        | 3   | 12   | 2.4 KB              | ✅ Good      |
| 16     | 65,536       | 4   | 16   | 3.2 KB              | ✅ Great     |
| 20     | 1,048,576    | 5   | 20   | 4 KB                | ✅ Excellent |

**All are practical! No artificial limits.**

## Why This Design Works

### 1. Musically Correct
- Pedals stay in proper signal chain order
- Matches how guitarists think about tone
- Compression → Drive → Modulation → Delay → Reverb

### 2. Simple Hardware
- Just bypass switches (ON/OFF)
- No complex routing multiplexers
- Fewer components = lower cost & easier to build

### 3. Silent Operation
- Solid-state switching (no relay clicks)
- Instant switching (microseconds)
- No audio pops or thumps

### 4. Scalable
- Add pedals without redesign
- Memory scales linearly with scenes
- GPIO pins scale linearly with pedals

### 5. Flexible
- Scene-based control (one button per scene change)
- Bank organization (group scenes by song)
- Future: MIDI control, wireless, expression pedals

## Next Steps for Prototyping

1. **Breadboard Test** (1-2 pedals)
   - Verify 74HC4066 audio quality
   - Test switching speed and silence
   - Measure THD and noise floor

2. **Simple Prototype** (3-4 pedals)
   - Arduino + OLED display
   - Basic scene switching
   - Footswitch control

3. **Full Design** (8+ pedals)
   - PCB design with proper grounding
   - ESP32 for advanced features
   - Professional enclosure

4. **Test & Refine**
   - Real-world guitarist testing
   - Audio quality validation
   - Firmware improvements

## Files

- `bypass_hardware_simulator.py` - Complete scene-based hardware simulator
- `scene_generator.py` - Scene generation and complexity analysis
- `HARDWARE_DESIGN.md` - This document

---

*Hardware design updated: December 23, 2025*
*Approach: Scene-based bypass switching
