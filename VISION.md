# BUSSter - Vision & Goals

**Bus-based Effects Switching and Routing System**

An open source hardware project for programmable guitar effects routing.

---

## The Problem

Guitarists face a common challenge: **complexity vs. control**.

### The Reality:
- Modern pedalboards often have **a lot of effects pedals**
- Each song requires **5-10 different tone combinations**
- During live performance, switching between sounds requires:
  - Hitting **multiple pedals simultaneously**
  - **Tap-dancing** across the pedalboard
  - **Hoping** you got the right combination
  - **Breaking** concentration during performance

### Example: "Smells Like Teen Spirit"

A guitarist needs:
1. **Clean intro**: Just compression
2. **Heavy chorus**: Compression + distortion + chorus
3. **Verse**: Compression + octave pedal
4. **Solo**: Compression + overdrive + distortion + delay

That's **4 different configurations**, each requiring multiple pedal switches. One mistake = wrong sound at a critical moment.

---

## Existing Solutions

### Commercial Loop Switchers:
- **Boss ES-8**: 8 loops, $700
- **GigRig G2**: 14 loops, $1,000+
- **Disaster Area DMC**: 12 loops, $600+

**Limitations:**
- Expensive
- Limited to 8-14 pedals (pros need 20+)
- Usually only 1-2 outputs (can't route to multiple amps easily)
- Closed-source (can't customize or repair)

### Manual Switching:
- **Cheap** ($0)
- **Flexible** (any combination)
- **Impractical** (requires tap-dancing)
- **Error-prone** (easy to hit wrong pedal)

---

## The BUSSter Vision

**What if you could:**
- Pre-program **any combination** of active pedals as a "scene"
- Switch **entire scenes** with **one footswitch**
- Walk through scenes **sequentially** (next/previous) during a song
- Route output to **multiple amplifiers** or recording destinations
- Build it yourself at **reasonable cost**
- Customize and improve the design
---

## Core Concept: Scene-Based Switching

### A "Scene" defines:
```
Scene: "Heavy Chorus"
  Pedals:  [Comp: ON]  [Dist: ON]  [Chorus: ON]  [Rest: OFF]
  Output:  → Amp 2 (Marshall)
```

### In Performance:
```
Song: "Smells Like Teen Spirit"
  Scene 1: Clean Intro
  Scene 2: Heavy Chorus    ← Press footswitch
  Scene 3: Clean Verse     ← Press footswitch
  Scene 4: Lead Solo       ← Press footswitch
```

**One button per scene change. No tap-dancing. No mistakes.**

---

## Key Features

### 1. Scalable Design
- Start with **3-5 pedals** (proof of concept)
- Scale up to **20+ pedals** (professional use)
- Modular architecture (add loops as needed)
- Extensible modules for expansion as the number of pedals increases

### 2. Scene Management
- Store **unlimited scenes** (memory permitting)
- Group scenes by **song** or **set list**
- Walk through scenes: **Next/Previous** footswitches
- Direct scene selection

### 3. Multiple Output Routing
- Route to **4-8 different amplifiers**
- **Wet/Dry** setups (clean + effects to different amps)
- **Stereo** routing (left/right to different amps)
- **Recording outputs** (DI, interface)

### 4. Silent Switching
- **Solid-state analog multiplexers** (74HC4051)
- Instant switching (microseconds)
- True bypass when OFF

### 5. Fixed Pedal Order
- Pedals stay in **musical order** (e.g., compression → drive → modulation → delay)
- No need to swap order (not musically useful)
- Simplifies design and reduces cost
- Each pedal can be ON or OFF per scene

### 6. Control Module Workflow
The control module manages scene creation, storage, and recall:

**Initial Version (Phase 1):**
- Extremely basic interface on the device itself
- Simple scene programming to prove the concept
- Manual configuration via buttons/encoder

**Future Versions:**
- Connect to laptop/computer via USB
- Drag-and-drop scene organization
- Visual pedal routing editor
- Easy scene naming and reordering
- Backup/restore configurations

**Before Performance (Scene Programming):**
1. Connect pedals to the board
2. Name each scene (e.g., "Clean Intro", "Heavy Chorus", "Lead Solo")
3. For each scene, specify which pedals are ON/OFF
4. Assign scenes to songs or setlists
5. Configure footswitch behavior (scene walk vs. direct control)

**During Performance:**
1. Press footswitch to advance to next scene
2. Display shows current scene name and what's next
3. All pedal switching happens instantly and silently
4. Walk through scenes as the song progresses
5. Switch between banks for different songs

**Advanced Options (Future):**
- Trigger amp channel switching when changing scenes
- Control external gear (delays, reverbs, etc.)
- Integrate amp effects loops into the signal path
- MIDI control and synchronization

---

## Design Philosophy

### Start Simple, Improve Iteratively

**Phase 1: Minimal Viable Product**
- Prove the 74HC4051 switching works
- Test audio quality (frequency response, noise)
- Build with **minimal components** first
- Add buffers/gates/EQ **only when needed**

**Phase 2: Community Refinement**
- Open source the design
- Let builders discover real-world needs
- Community contributes improvements:
  - Better buffer designs
  - Noise gate options
  - EQ/filtering stages
  - Ground loop elimination techniques
  - UI enhancements
  - Case designs

**Phase 3: Mature Product**
- Proven audio quality
- Multiple build options (budget to boutique)
- Complete documentation
- Active builder community

### "Build What You Need"

Different builders have different needs:
- **Budget build**: Minimal components, direct MUX switching
- **Mid-level**: Add input/output buffers
- **High-end**: Full buffering, noise gates, EQ stages, ground loop isolation
- **Pro**: Custom features (MIDI, Bluetooth, expression pedal control)

The design accommodates all levels.

---

## What BUSSter Is NOT

To keep scope manageable:

❌ **Not a multi-effects processor** (doesn't create effects, just routes them)
❌ **Not trying to replace pedals** (works WITH your existing pedals)
❌ **Not changing pedal order** (fixed chain, just ON/OFF control)
❌ **Not a complete amp switcher** (focuses on pedal routing + output selection)

---

## Project Status

### ✅ Completed (December 2025):
- Core algorithm development
- Path generation mathematics
- Hardware simulation tools
- Architecture design
- Proof that full permutation routing is unnecessary

### 🔄 Current Phase:
- Documentation for open source release
- License selection
- Community feedback on approach

### 🔜 Next Steps:
1. Design single pedal loop (analog circuit)
2. Prototype and test audio quality
3. Develop control firmware
4. Build 3-pedal proof of concept
5. Scale to 10+ pedals
6. Release complete design files

---

## Who This Is For

### Primary Audience:
- **DIY guitarists** who want programmable scene switching
- **Professional musicians** needing 15+ pedal routing
- **Electronics hobbyists** interested in audio design
- **Builders** who want to customize and improve

### Skills Needed to Build:
- **Beginner**: Can solder, follow instructions → Build from kit
- **Intermediate**: PCB assembly, basic circuits → Build from scratch
- **Advanced**: Circuit design, firmware → Contribute improvements

---

## Success Criteria

BUSSter will be successful when:

1. ✅ **Builders can create it** from published designs
2. ✅ **Audio quality is transparent** (no tone degradation)
3. ✅ **Switching is silent** (no pops, clicks, or thuds)
4. ✅ **Cost is reasonable** ($200-500 for 10 loops)
5. ✅ **Community improves it** (active contributions)
6. ✅ **Solves the real problem** (makes live performance easier)

---

## The Ultimate Goal

**Make professional-grade pedal routing accessible to everyone.**

Commercial loop switchers cost $700-1500 and max out at 8-14 loops.
BUSSter aims to provide 20+ loop routing for under $500, fully customizable, and open source.

If even one guitarist builds this and has a better performance because of it, the project succeeds.

---

## Get Involved

This is an open source hardware project. We welcome:
- Circuit design contributions
- Firmware development
- Documentation improvements
- Testing and feedback
- Build logs and photos
- Feature suggestions

**Status**: Project documentation phase (December 2025)
**Next**: Hardware prototyping (TBD)
**License**: TBD (permissive open source hardware license)

---

*Originally conceived December 2019*
*Revived and refined December 2025*
*Created by Keith D. Sprochi, Pompano Beach, Florida USA*
