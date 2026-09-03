# SURE Trust VLSI Admission Test — Full Preparation Guide
### Real exam questions + correct answers + concept explanations

---

## 1. Sequential Circuit Basics

**Q: Which of the following is a level sensitive circuit element?**
**A: Latch**
*Concept:* A latch is "transparent" — its output follows the input as long as the enable/clock signal is at a particular level (high or low). No edge needed.

**Q: Which of the following is an edge triggered circuit element?**
**A: Flip-flop**
*Concept:* A flip-flop only updates its output at the moment the clock transitions (rising or falling edge) — not continuously like a latch. This is why flip-flops are used for reliable synchronous design.

**Q: How many Flip-Flops are required for a mod-16 counter?**
**A: 4**
*Concept:* A counter with N flip-flops can count 2^N states. To count 16 states (0-15), you need 2^N = 16 → N = 4.

**Q: What is the output of a negative edge-triggered D-Flip Flop when the clock is LOW?**
**A: Old data is reflected at the output**
*Concept:* Since it's edge-triggered (not level-triggered), the output only changes at the falling edge. While clock stays low (between edges), the flip-flop holds its last captured value — it doesn't track D continuously like a latch would.

---

## 2. OPAMP & Analog Fundamentals

**Q: The gain of an ideal OPAMP is**
**A: Infinity**
*Concept:* An ideal OPAMP has infinite open-loop gain, infinite input impedance, and zero output impedance — these are the three foundational ideal assumptions used to simplify OPAMP circuit analysis.

**Q: An OPAMP can be used as an**
**A: All of the above** (amplifier, comparator, integrator, differentiator, filter, oscillator, etc.)
*Concept:* OPAMPs are extremely versatile building blocks — the specific function depends entirely on the external feedback network you connect around it.

**Q: The intrinsic gain of a transistor depends upon**
**A: Both Transconductance and Output Resistance**
*Concept:* Intrinsic gain = gm × ro (transconductance × output resistance). Higher gm (more current per volt of input) and higher ro (less current leakage through the output) both increase the transistor's raw voltage gain.

**Q: A differential amplifier does which of the following functions?**
**A: Amplifies the difference between the two inputs and rejects the common mode signal**
*Concept:* This is the defining property of a diff-amp — it responds only to the *difference* between its two inputs (differential mode) and ideally cancels out any signal common to both inputs (common mode), which is why CMRR (Common Mode Rejection Ratio) is such an important spec.

**Q: A Zener diode, when used in voltage stabilization circuits, is biased in?**
**A: Reverse breakdown region**
*Concept:* Unlike normal diodes (which you avoid reverse-breaking), Zener diodes are specifically designed to operate safely in reverse breakdown, where voltage stays nearly constant across a range of currents — this constant voltage is exactly what makes them useful for regulation.

**Q: The bandwidth in a _______ filter equals the critical (cutoff) frequency?**
**A: Low pass**
*Concept:* For a low-pass filter, bandwidth is measured from 0 Hz (DC) to the cutoff frequency — so bandwidth = cutoff frequency by definition. (This is different from band-pass filters, where bandwidth = difference between two cutoff frequencies.)

**Q: Rectification efficiency — input power 300W, power obtained 180W. Calculate efficiency.**
**A: 60%**
*Concept:* Efficiency = (Output Power / Input Power) × 100 = (180/300) × 100 = 60%. Simple ratio — don't overthink these, just plug into the formula.

---

## 3. Data Converters & Mixed-Signal

**Q: For Nyquist rate data converters (DACs/ADCs), sampling frequency should be**
**A: At least twice the highest frequency component in the input signal**
*Concept:* This is the Nyquist-Shannon sampling theorem — sample below this rate and you get "aliasing," where higher frequencies fold back and corrupt your signal, making it impossible to reconstruct correctly.

**Q: Flash and SAR (Successive Approximation Register) are types of**
**A: Analog to Digital Converters (ADCs)**
*Concept:* Flash ADC compares the input to many reference voltages simultaneously (fast but hardware-heavy). SAR ADC does a binary search — testing one bit at a time (slower but far more efficient in hardware).

**Q: PLL (Phase Locked Loop) consists of**
**A: All of the above** (Phase Detector, VCO, Loop Filter)
*Concept:* A PLL is a feedback system that locks an output signal's phase/frequency to a reference. The Phase Detector compares phases, the Loop Filter smooths the error signal, and the VCO (Voltage Controlled Oscillator) adjusts its frequency accordingly — closing the loop.

**Q: PLLs are used in mixed signal chips for**
**A: All of the above** (clock generation, frequency synthesis, clock/data recovery, etc.)

---

## 4. Memory

**Q: SRAM and DRAM memories are examples of**
**A: Read Write Volatile Memory**
*Concept:* Both lose their stored data when power is removed (volatile), and both support reading and writing at any time (unlike ROM).

**Q: NAND Flash memory is an example of:**
**A: EEPROM**
*Concept:* Flash memory is technically a type of EEPROM (Electrically Erasable Programmable ROM) — it's non-volatile (retains data without power) but can be electrically erased and rewritten, unlike older one-time-programmable ROMs.

---

## 5. Number Systems & Boolean Algebra

**Q: The 2's complement of the number 1101101 is**
**A: 0010011**
*Concept:* Step 1 — invert all bits: 1101101 → 0010010. Step 2 — add 1: 0010010 + 1 = 0010011. Always practice this two-step method by hand; it's a guaranteed question type.

**Q: (734) base 8 = (___) base 16**
**A: 1DC**
*Concept:* Convert via binary as an intermediate step: octal 734 → binary 111 011 100 → regroup into 4-bit nibbles from the right: 0001 1101 1100 → hex: 1 D C.

**Q: Karnaugh map is used for the purpose of**
**A: To minimize the terms in a Boolean expression**
*Concept:* A K-map is a visual grid method for simplifying Boolean expressions by grouping adjacent 1s (or 0s), avoiding the algebraic tedium of Boolean law application.

**Q: How many cells will an n-input variable K-Map have?**
**A: 2^n**
*Concept:* Each input variable doubles the number of possible combinations, so n variables give 2^n total combinations/cells.

**Q: Y = AB + CD, realized using 2-input NAND gates. Minimum gates required?**
**A: 3**
*Concept:* AND-OR logic can always be converted to all-NAND implementation (NAND is a universal gate). For a 2-term SOP expression like this, you typically need 2 NAND gates for the two AND terms (each acting as AND due to double inversion) plus 1 final NAND to combine them as OR — total 3.

**Q: Minimum number of 2:1 MUX required to realize a 4:1 MUX?**
**A: 3**
*Concept:* A 4:1 MUX can be built as a tree: 2 MUXes handle the first-level selection (2 pairs of 4 inputs) and 1 MUX combines their outputs using the second select line — 2 + 1 = 3 total.

**Q: Which logic gate acts as an even parity generator?**
**A: XOR**
*Concept:* XOR outputs 1 when there's an odd number of 1s among inputs — chaining XORs across bits produces a parity bit that, when appended, makes the total number of 1s even. This is a widely used error-detection building block.

---

## 6. Transistor & MOSFET Physics

**Q: The threshold voltage of a PMOS device is**
**A: Negative**
*Concept:* PMOS conducts when gate-source voltage is sufficiently negative (i.e., gate pulled low relative to source) — so by convention its threshold voltage is expressed as a negative number, unlike NMOS (positive Vt).

**Q: Effect of increasing channel length in a MOSFET on threshold voltage?**
**A: Threshold voltage decreases**
*(Note: this trips up many people — the intuitive "no effect" answer is wrong per this exam's key.)*
*Concept:* In short-channel devices, threshold voltage roll-off effects are more pronounced; as channel length increases (moving away from short-channel effects), certain charge-sharing effects change, altering Vt. Memorize this direction for the exam even if the deeper device physics is advanced.

**Q: In an NMOS transistor, which region of operation is characterized by Vds > Vgs − Vth?**
**A: Saturation region**
*Concept:* This is the standard boundary condition — when drain-source voltage exceeds the "overdrive voltage" (Vgs − Vth), the channel pinches off near the drain, and the transistor enters saturation, where current becomes largely independent of Vds (acts like a current source).

**Q: Benefit of using FinFETs in modern CMOS technology?**
**A: All of the above** (better gate control, lower leakage, higher drive current)
*Concept:* FinFETs wrap the gate around a 3D "fin" channel on multiple sides (instead of just one side, like planar MOSFETs), giving much tighter electrostatic control over the channel — this reduces leakage current and short-channel effects while enabling further transistor scaling.

**Q: In MOSFETs, DIBL stands for**
**A: Drain Induced Barrier Lowering**
*Concept:* A short-channel effect where a high drain voltage lowers the source-side potential barrier, causing the transistor to leak current even when it should be OFF — a major challenge in scaled-down technology nodes.

---

## 7. Fabrication & Process Technology

**Q: Which technique is used to grow single crystal silicon ingots for wafers?**
**A: Czochralski Technique**
*Concept:* A seed crystal is dipped into molten silicon and slowly pulled upward while rotating, growing a large single-crystal ingot — this remains the dominant industrial method for silicon wafer production.

**Q: Which processes are used to fabricate silicon wafers?**
**A: All of the above** (includes doping, oxidation, lithography, etching, deposition, etc.)

**Q: Which process step is primarily used for transferring patterns onto silicon wafers?**
**A: Lithography**
*Concept:* Lithography uses light (or other radiation) through a mask to transfer circuit patterns onto a photoresist-coated wafer — it's the foundational patterning step that defines transistor and interconnect geometry.

---

## 8. CMOS Logic & VLSI Design

**Q: Complementary CMOS logic gates consist of:**
**A: n-MOS pull down network and p-MOS pull up network**
*Concept:* In CMOS, PMOS transistors (which conduct when input is low) form the pull-up network connecting output to VDD, while NMOS transistors (conduct when input is high) form the pull-down network connecting output to ground — together they ensure the output is always driven to a valid logic level, never floating.

**Q: Power consumption in a CMOS logic gate depends upon**
**A: All the above** (switching frequency, supply voltage, load capacitance, leakage current)

**Q: Out of these logic families, which provides the minimum dissipation of power?**
**A: CMOS**
*Concept:* Unlike older families (TTL, ECL), CMOS has near-zero static power draw because in steady state, either the pull-up or pull-down network is off — current only flows during switching transitions.

**Q: In digital design, which logic family has the highest speed?**
**A: ECL (Emitter Coupled Logic)**
*Concept:* ECL transistors operate in the non-saturating region, avoiding slow saturation/desaturation delays — this trades away CMOS's power efficiency for raw switching speed, historically used in high-performance/legacy computing systems.

**Q: What does the term 'fanout' refer to?**
**A: The number of output pins driven by a net** (i.e., how many gate inputs a single gate's output can drive)
*Concept:* Careful with wording — fanout is about the driving capability of an output, not about counting input connections. Exceeding a gate's max fanout can degrade signal integrity and timing.

**Q: Purpose of using a Schmitt trigger in digital circuit design?**
**A: To provide hysteresis and reduce noise sensitivity**
*Concept:* A Schmitt trigger uses two different threshold voltages (one for rising, one for falling signals) instead of one, preventing a noisy/slow-transitioning input signal from causing multiple false output transitions ("chattering").

**Q: Main advantage of using an FPGA over an ASIC?**
**A: Flexibility in design**
*Concept:* FPGAs are reprogrammable after manufacturing, letting you change the logic design anytime — ideal for prototyping or low-volume production. ASICs are faster/more power-efficient but fixed once fabricated, and only economical at high volumes.

**Q: Purpose of clock gating in digital circuits?**
**A: Reduce power consumption**
*Concept:* Clock gating disables the clock signal to unused/idle parts of a circuit, preventing unnecessary switching activity (and the dynamic power that comes with it) in blocks that aren't currently doing useful work.

**Q: According to Moore's Law, the number of transistors on a chip doubles every**
**A: Eighteen months**
*Concept:* Gordon Moore's 1965 observation (often cited as ~18-24 months) — not a physical law, but an industry trend describing the pace of semiconductor scaling that held remarkably true for decades.

**Q: In VLSI Design, CMOS technology is most popular compared to Bipolar and GaAs due to**
**A: Both (a) & (b)** — typically low power consumption + high integration density
*Concept:* CMOS's near-zero static power and ability to pack far more transistors per chip (compared to bipolar/GaAs) made it the dominant technology for large-scale digital ICs.

---

## 9. Timing (Setup/Hold) — High-Yield VLSI Topic

**Q: In VLSI design, a 'hold violation' occurs when:**
**A: Data arrives too early at the receiving flip-flop**
*Concept:* Hold time is the minimum time data must remain *stable after* the clock edge. If new data arrives too soon (races ahead of the clock edge), the flip-flop might incorrectly capture the new value instead of the old one — this is a hold violation. (Contrast with setup violation: data arrives too *late*, before the clock edge, without enough settle time.)

---

## 10. RTL / Verilog / EDA Flow

**Q: Primary role of the EDA tool during the synthesis process?**
**A: Translate RTL code into a gate-level netlist**
*Concept:* Synthesis is the automated step where a synthesis tool (e.g., Design Compiler, Genus) converts your behavioral/RTL Verilog description into an actual gate-level circuit implementation using a specific standard cell library.

**Q: Correct syntax to define a 2-to-1 multiplexer in Verilog?**
**A: `assign y = sel ? a : b;`**
*Concept:* This uses Verilog's ternary conditional operator inside a continuous assignment — when `sel` is true (1), `y` gets `a`; otherwise `y` gets `b`. This is the standard idiomatic way to write a simple combinational MUX.

**Q: Using FSM concepts, to detect binary sequence '0101', how many states in Mealy & Moore machines respectively?**
**A: 4 & 5**
*Concept:* Mealy machines generally need fewer states because output depends on both state AND input (more information per state), while Moore machines need an extra state since output depends only on state — detecting the same pattern typically needs one more state in Moore than in Mealy.

---

## 11. BJT / Bipolar Devices

**Q: A BJT has a common base forward short circuit current gain (α) of 0.999. Find common emitter current gain (β).**
**A: 999**
*Concept:* The relationship is β = α / (1 − α). Plugging in: β = 0.999 / (1 − 0.999) = 0.999 / 0.001 = 999. This α-to-β conversion is a classic BJT exam question — memorize the formula.

---

## 12. Number System Comparison

**Q: Given four numbers in different number systems, which has the greatest value?**
**A: (1F4A)₁₆**
*Concept:* When comparing across number systems, always convert everything to decimal first before comparing magnitudes — don't try to eyeball it. (1F4A)₁₆ = 1×16³ + 15×16² + 4×16¹ + 10×16⁰ = a large decimal value; verify by conversion rather than assumption.

---

## Quick-Fire Review List (Concept → Answer, no explanation, for last-minute scan)

| Concept | Answer |
|---|---|
| Level sensitive element | Latch |
| Edge triggered element | Flip-flop |
| Ideal OPAMP gain | Infinity |
| SRAM/DRAM type | Read Write Volatile |
| NAND Flash type | EEPROM |
| Nyquist sampling rate | ≥ 2× max frequency |
| PMOS Vt | Negative |
| Moore's Law period | 18 months |
| Silicon ingot growth | Czochralski Technique |
| CMOS pull-up/down | PMOS up, NMOS down |
| Mod-16 counter flip-flops | 4 |
| 2's complement of 1101101 | 0010011 |
| K-map purpose | Minimize Boolean expression |
| Y=AB+CD via NAND (min gates) | 3 |
| 4:1 MUX via 2:1 MUX (min) | 3 |
| Zener bias for regulation | Reverse breakdown |
| Fastest logic family | ECL |
| Lowest power logic family | CMOS |
| Fanout definition | Output pins driven by a net |
| Schmitt trigger purpose | Hysteresis / noise immunity |
| Hold violation cause | Data arrives too early |
| Channel length ↑ → Vt | Decreases |
| NMOS saturation condition | Vds > Vgs − Vth |
| FinFET benefit | All of the above |
| DIBL | Drain Induced Barrier Lowering |
| Lithography purpose | Pattern transfer |
| Synthesis tool role | RTL → gate-level netlist |
| 2:1 MUX Verilog syntax | `assign y = sel ? a : b;` |
| Mealy/Moore states for '0101' | 4 & 5 |
| FPGA vs ASIC advantage | Flexibility |
| Clock gating purpose | Reduce power |
| α to β formula | β = α/(1−α) |
| Even parity gate | XOR |
| K-map cells for n inputs | 2^n |

---

## How to use this document
1. Read through once fully, concept by concept — don't just memorize the answer, understand *why*.
2. Use the Quick-Fire table for rapid pre-test review.
3. Pay extra attention to the ones flagged as commonly missed (channel length/Vt, fanout wording, Mealy/Moore order).
4. For anything unfamiliar, cross-reference with the broader 150-question practice set for additional angle coverage on the same topics.
