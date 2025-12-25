# BUSSter Firmware

This directory contains firmware for the BUSSter microcontroller.

---

## Overview

The firmware manages:
- Scene storage and recall
- Footswitch input processing
- MUX control signal generation
- Display interface (OLED/LED)
- MIDI communication (optional)
- Configuration persistence

---

## Planned Architecture

### Core Modules

#### 1. Scene Manager
- Store/recall scene configurations
- Binary pedal state per scene (ON/OFF)
- Output routing per scene
- Scene naming and organization
- Song mode (sequential scene walking)

#### 2. Control Engine
- Generate MUX control words from scene data
- Translate scene → binary signals for 74HC4051 chips
- Fast switching (< 1ms scene transition)
- Atomic updates (all pedals switch simultaneously)

#### 3. Input Handler
- Footswitch debouncing
- Long press vs. short press detection
- Multi-switch combinations
- Expression pedal input (optional)

#### 4. Display Driver
- Scene name/number display
- Pedal status indicators
- Battery/power status
- Configuration menus

#### 5. MIDI Interface (Optional)
- Scene change via MIDI program change
- MIDI controller integration
- DAW synchronization
- Preset management via MIDI SysEx

#### 6. Storage Manager
- Non-volatile scene storage (EEPROM/Flash)
- Configuration backup/restore
- Factory reset capability
- Scene import/export

---

## Microcontroller Selection (TBD)

### Option 1: ESP32
**Pros:**
- WiFi/Bluetooth (wireless scene management)
- Powerful dual-core processor
- Large community support
- Arduino IDE compatible
- USB programming

**Cons:**
- Higher power consumption
- More complex than needed for basic operation

### Option 2: STM32
**Pros:**
- Lower power consumption
- Excellent real-time performance
- Good peripheral support
- Cost-effective

**Cons:**
- Steeper learning curve
- Less community support than ESP32

### Option 3: Arduino (ATmega328P/ATmega2560)
**Pros:**
- Simple, well-documented
- Low cost
- Large community
- Easy for beginners

**Cons:**
- Limited memory for complex features
- Fewer GPIO pins (limits scaling)

**Current Recommendation:** ESP32 for prototype, may simplify to STM32 or Arduino for production.

---

## Scene Data Structure (Draft)

```c
typedef struct {
    char name[16];              // Scene name ("Clean", "Lead", etc.)
    uint8_t pedal_states;       // Binary: each bit = one pedal ON/OFF
    uint8_t output_routing;     // Which amp output to use
    uint8_t reserved[4];        // Future expansion
} Scene;

// Example for 8 pedals:
// pedal_states = 0b00101101
//   Bit 0: Pedal 1 = ON
//   Bit 1: Pedal 2 = OFF
//   Bit 2: Pedal 3 = ON
//   Bit 3: Pedal 4 = ON
//   Bit 4: Pedal 5 = OFF
//   Bit 5: Pedal 6 = ON
//   Bit 6: Pedal 7 = OFF
//   Bit 7: Pedal 8 = OFF
```

---

## Footswitch Operations (Draft)

### Basic Mode
- **Next**: Short press → Next scene
- **Previous**: Short press → Previous scene
- **Menu**: Long press → Enter configuration

### Advanced Mode (Optional)
- **Direct Scene**: Number pad for direct scene selection
- **Bank Up/Down**: Organize scenes into banks
- **Tap Tempo**: Sync delays to tempo (requires delay pedal MIDI control)

---

## Development Roadmap

### Phase 1: Basic Functionality
- [ ] Scene storage (hardcoded, then EEPROM)
- [ ] MUX control signal generation
- [ ] Simple footswitch input (next/previous)
- [ ] LED status indicators

### Phase 2: Display Integration
- [ ] OLED display support
- [ ] Scene name display
- [ ] Pedal status visualization
- [ ] Simple menu system

### Phase 3: Advanced Features
- [ ] MIDI interface
- [ ] Wireless scene management (ESP32)
- [ ] Expression pedal support
- [ ] Tap tempo

### Phase 4: Polish
- [ ] Configuration backup/restore
- [ ] Firmware update capability
- [ ] Performance optimization
- [ ] Error handling and recovery

---

## Code Style Guidelines (Draft)

- Use clear, descriptive variable names
- Comment complex logic
- Keep functions small and focused
- Test each module independently
- Document all public APIs

---

## Testing Strategy

### Unit Tests
- Scene data encoding/decoding
- MUX control word generation
- Footswitch debouncing logic

### Integration Tests
- Scene switching speed
- Display responsiveness
- MIDI message handling

### Real-World Tests
- Guitarist feedback
- Live performance testing
- Edge case discovery

---

## Current Status

**Phase**: Planning and architecture design (December 2025)

Firmware development will begin after hardware prototype is validated.

---

## Contributing

We welcome firmware contributions:
- Microcontroller selection advice
- Code optimization
- Feature implementations
- Testing and debugging
- Documentation

Please ensure code is well-commented and follows project style guidelines.

---

## Dependencies (TBD)

- Arduino IDE / PlatformIO
- Display libraries (Adafruit SSD1306 for OLED)
- MIDI libraries (if implementing MIDI)
- Unit testing framework (Unity, Google Test)

---

*Last updated: December 2025*
