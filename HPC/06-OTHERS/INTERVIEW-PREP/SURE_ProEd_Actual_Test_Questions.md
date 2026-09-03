# SURE Trust VLSI Admission Test — ACTUAL Questions & Correct Answers
(Extracted directly from real quiz results data — 50 questions, high confidence)

1. **Which of the following is a level sensitive circuit element?** → Latch
2. **Which of the following is an edge triggered circuit element?** → Flip-flop
3. **The gain of an ideal OPAMP is** → Infinity
4. **SRAM and DRAM memories are examples of** → Read Write Volatile Memory
5. **NAND Flash memory is an example of:** → EEPROM
6. **An OPAMP can be used as an** → All of the above
7. **PLL (Phase Locked Loops) are used in mixed signal chips for:** → All of the above
8. **The intrinsic gain of a transistor depends upon** → Both Transconductance and Output Resistance
9. **A differential amplifier does which of the following functions** → Amplifies the difference between the two inputs and rejects the common mode signal
10. **For Nyquist rate data converters (DACs and ADCs) the sampling frequency should be** → At least twice the highest frequency component in the input signal
11. **In VLSI Design CMOS technology is most popular compared to Bipolar and GaAs due to** → Both (a) & (b)
12. **The threshold voltage of a PMOS device is** → Negative
13. **According to Moore's Law the number of transistors on a chip doubles every** → Eighteen months
14. **A PLL (Phased Locked Loop) consists of** → All of the above
15. **Flash and SAR (Successive Approximation Register) are types of** → Analog to Digital Converters (ADCs)
16. **Which technique is used to grow single crystal silicon ingots for wafers?** → Czochralski Technique
17. **Which processes are used to fabricate silicon wafers?** → All of the above
18. **Complementary CMOS logic gates consist of:** → n-MOS pull down network and p-MOS pull up network
19. **Power consumption in a CMOS logic gate depends upon** → All the above
20. **The Pentium series microprocessors belong to** → Intel
21. **The bandwidth in a _______ filter equals the critical frequency** → Low pass
22. **Rectification efficiency: input power 300w, power obtained 180w. Calculate efficiency** → 60%
23. **(Matching question)** → P-4, q-1, r-3, s-2
24. **BJT common base current gain = 0.999, find common emitter current gain (β)** → 999
25. **How many Flip-Flops are required for mod-16 counter?** → 4
26. **The 2's complement of the number 1101101 is** → 0010011
27. **Karnaugh map is used for the purpose of** → To minimize the terms in a Boolean expression
28. **Y = AB + CD realized using 2-input NAND gates. Minimum gates required?** → 3
29. **Minimum no. of 2:1 MUX required to realize a 4:1 MUX?** → 3
30. **A Zener diode, in voltage stabilization circuits, is biased in** → Reverse breakdown region
31. **(734) base 8 = (___) base 16** → 1DC
32. **Which logic family provides minimum power dissipation?** → CMOS
33. **What does the term 'fanout' refer to?** → The number of output pins driven by a net (i.e., how many gate inputs a single output can drive)
34. **Purpose of using a Schmitt trigger in digital circuit design?** → To provide hysteresis and reduce noise sensitivity
35. **In VLSI design, a 'hold violation' occurs when:** → Data arrives too early at the receiving flip-flop
36. **Effect of increasing channel length in a MOSFET on threshold voltage?** → Threshold voltage decreases
37. **Output of a negative edge-triggered D-Flip Flop when clock is low?** → Old data is reflected at the output
38. **In an NMOS transistor, which region has Vds > Vgs − Vth?** → Saturation region
39. **Benefit of using FinFETs in modern CMOS technology?** → All of the above
40. **In MOSFETs, DIBL stands for** → Drain Induced Barrier Lowering
41. **Which process step is primarily used for transferring patterns onto silicon wafers?** → Lithography
42. **Primary role of the EDA tool during synthesis?** → Translate RTL code into a gate-level netlist
43. **FSM to detect sequence '0101' — number of states in Mealy & Moore respectively?** → 4 & 5
44. **Correct syntax to define a 2-to-1 MUX in Verilog?** → `assign y = sel ? a : b;`
45. **Which logic gate acts as an even parity generator?** → XOR
46. **Which number has the greatest value: compare across number systems?** → (1F4A)₁₆ (hexadecimal option — was the correct answer across all instances)
47. **How many cells will an n-input variable K-Map have?** → 2^n
48. **Which logic family has the highest speed?** → ECL
49. **Main advantage of using an FPGA over an ASIC?** → Flexibility in design
50. **Purpose of clock gating in digital circuits?** → Reduce power consumption

---

## Priority focus — questions many top scorers still got wrong (tricky ones):
- **Q36** (MOSFET channel length → threshold voltage): correct answer is "**decreases**" — many people intuitively guessed "no effect," which was wrong.
- **Q33** (Fanout definition): it's about **output pins driving inputs**, not "input pins connected" — a commonly confused wording.
- **Q43** (Mealy/Moore states for '0101' detection): remember order is **Mealy first, Moore second** → 4 & 5.
- **Q26** (2's complement): make sure you compute correctly — 0010011.
- **Q21** (Filter bandwidth = critical frequency): specifically **Low pass**, not band pass — a couple of toppers slipped on this one.

## Format reminder
This was a 50-question MCQ test, camera-on Google Meet. Full marks were achievable (top scorer got 100%). Most people scored 90-98% — the errors were concentrated in a handful of tricky wording questions above, not obscure content. Review those five carefully.
