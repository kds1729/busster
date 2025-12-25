# BUSSter Hardware Design

This directory contains all hardware design files for the BUSSter project.

---

## Directory Structure

### `schematics/`
Circuit diagrams and schematics in standard formats:
- KiCad (.kicad_sch)
- PDF exports
- Component reference designators
- Signal flow annotations

### `pcb/`
Printed circuit board layouts:
- KiCad PCB files (.kicad_pcb)
- Gerber files for manufacturing
- Pick-and-place files
- Assembly drawings
- PCB specifications (layers, thickness, copper weight)

### `bom/`
Bills of materials:
- Component lists with part numbers
- Supplier links (Mouser, Digikey, etc.)
- Budget vs. boutique component options
- Substitution guidelines
- Cost analysis per build level

---

## Planned Hardware Components

### Phase 1: Single Pedal Loop (Coming Soon)
- 74HC4051 analog multiplexer circuit
- Input/output buffer design
- Power supply considerations
- Initial testing methodology

### Phase 2: Multi-Loop System (Coming Soon)
- 3-pedal proof of concept
- 8-pedal standard system
- 20+ pedal professional system
- Daisy-chain expansion capability

### Phase 3: Control System (Coming Soon)
- Microcontroller selection (likely ESP32 or STM32)
- Footswitch interface
- Display options (OLED, LED)
- MIDI interface (optional)
- Power distribution

### Phase 4: Audio Quality Enhancements (TBD)
- Input/output buffers
- Noise gate circuits
- EQ/filtering stages
- Op-amp selection and testing
- Grounding and shielding

---

## Design Philosophy

### Start Minimal
- Prove the 74HC4051 switching works
- Test audio quality with minimal components
- Add buffers/gates/EQ only when needed

### Modular Architecture
- Each pedal loop is independent
- Add loops as needed
- Scalable from 3 to 20+ pedals

### Multiple Build Levels
1. **Budget**: Direct MUX switching, minimal components
2. **Mid-level**: Add input/output buffers
3. **High-end**: Full buffering, noise gates
4. **Pro**: Custom features (MIDI, Bluetooth, expression pedals)

---

## Audio Quality Targets

- **THD (Total Harmonic Distortion)**: < 0.01% @ 1kHz
- **Noise Floor**: < -100dBu
- **Frequency Response**: 20Hz - 20kHz ±0.5dB
- **Crosstalk**: < -80dB between loops
- **Switching Noise**: Silent (< -90dBu transient)

---

## Key Design Decisions

### Why 74HC4051 Multiplexers?
- Silent solid-state switching (no relay noise)
- Fast switching (microseconds)
- Low on-resistance (~ 80Ω)
- True bypass capability
- Low cost ($0.50 per chip)

### Power Considerations
- Low current draw (< 100mA for control logic)
- Standard 9V DC input (common for pedal boards)
- Isolated power for audio and digital sections
- No power to pedals (they use their own supplies)

---

## Current Status

**Phase**: Pre-prototype design (December 2025)

Hardware files will be added as designs are completed and tested.

---

## Testing Checklist (Future)

- [ ] Audio quality measurements (THD, noise, frequency response)
- [ ] Switching speed and transient behavior
- [ ] Crosstalk between loops
- [ ] Power consumption
- [ ] Long-term reliability testing
- [ ] Real-world guitarist testing

---

## Contributing

We welcome hardware contributions:
- Circuit improvements
- PCB layout optimization
- Component selection advice
- Audio quality testing
- Cost reduction ideas

Please see the main project README for contribution guidelines.

---

*Last updated: December 2025*
