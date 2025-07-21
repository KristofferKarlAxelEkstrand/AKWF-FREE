# AKWF

```text
   _____   ____  __.__      _____________
  /  _  \ |    |/ _/  \    /  \_   _____/   F R E E
 /  /_\  \|      < \   \/\/   /|    __)
/    |    \    |  \ \        / |     \
\____|__  /____|__ \ \__/\  /  \___  /
        \/        \/      \/       \/
```

AKWF or Adventure Kid Waveforms is a collection of one cycle waveforms
to be used within synthesizers or other kinds of sound generators. It
is basically the smallest sound possible to sample and still get the
overall feel of the sampled instrument.

## Versions

### AKWF (Original)

The waveforms are 600 samples long, chosen during my early work on
an additive synth in high school. That length worked well for
layering octaves, while shorter cycles degraded the sound. I hadn’t
yet learned about standard buffer sizes like 256 or 1024—this was
just my starting point.

If use it as a sample and treat it as a C ad you pitch it pitch it
to D1+2 you get an actual C... yeah... I know...

- File format: Wave
- Length: 600 samples
- Bit depth: 16bit
- Sample rate: 44.1khz
- Channels: Mono

### AKWF--Akai-MPC

- File format: Wave
- Length:
- Bit depth: 16bit
- Sample rate: 44.1khz
- Channels: Mono

### AKWF--Alchemy--Camel-Audio

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Big-Tick-Rhino

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Corona-Discovery-Pro

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Elektron--Model Samples

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--MonoMachine-SFX-60+

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Music-Line--Amiga

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Pro-Tracker--ST-Clones

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Reaktor

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--SonicWare--Smpltrek

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Surge

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Synapse-Audio-DUNE-3

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Synthesis-Technology

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Teensy

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--TX16W-Typhoon-Cyclone

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--U-he-Zebra

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--WT--Harmor-Komplexer

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF-c

The waveforms are defined in C as arrays of 16 unsigned integers, so basically 16-bit data.

- File format: Array
- Length: XX
- Bit depth: 16bit
- Sample rate: N/A
- Channels: Mono

### AKWF-js

The waveforms are defined in JS as 256 values long arrays of floating point numbers.

- File format: Array
- Length: 256 values
- Bit depth: N/A
- Sample rate: N/A
- Channels: Mono

### AKWF-png

View AKWF waveforms as PNG plots for visual reference. Each image offers a straightforward depiction of the waveform shape to aid analysis and selection.

### Sound-generators

#### [QU-Bit Chord](https://www.qubitelectronix.com/)

Chord is a plug and play solution for bringing musical polyphony to your modular system. In the Qubit Chord module, AKWF (Adventure Kid Waveforms) provide textures, allowing for creative sound design in modular synthesis. Ideal for adding complex and evolving tones.

#### [Elektron Model:Samples](https://elektron.se/explore/modelsamples)

Elektron Model:Samples uses AKWF in it's sound library.

## Usage

These waveforms are compact, single-cycle samples used as oscillator shapes. They can be loaded into samplers as pitch-tuned sources or into synthesizers as static waveform options. While not wavetables, some synths allow morphing between them. Their low resource demands make them suitable for both old gear and more modern setups, offering a bit more timbral variety beyond the basic shapes for synthesizers and enabling some kind of hybrid synth-sampler behavior.