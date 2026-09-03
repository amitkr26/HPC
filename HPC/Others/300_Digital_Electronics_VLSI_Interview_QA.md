# 300 Most Expected Digital Electronics & VLSI Interview Questions
*Built around your SURE Trust test topics, expanded for interview depth*

---

## A. Number Systems (1–25)

1. Convert binary 1101 to decimal → **13**
2. Convert decimal 45 to binary → **101101**
3. Convert hex 2F to decimal → **47**
4. Convert octal 17 to decimal → **15**
5. 1's complement of 1010 → **0101**
6. 2's complement of 1010 → **0110**
7. 2's complement of 0000 → **0000** (stays same)
8. Range of n-bit unsigned number → **0 to 2ⁿ−1**
9. Range of n-bit 2's complement signed number → **−2ⁿ⁻¹ to 2ⁿ⁻¹−1**
10. Why is 2's complement preferred over 1's complement? → Single representation of zero, simpler add/subtract hardware
11. Add 0111 + 0001 in binary → **1000**
12. Subtract using 2's complement: 0110 − 0011 → take 2's complement of 0011 (1101) and add: 0110+1101 = 10011 → drop carry → **0011**
13. BCD code for decimal 9 → **1001**
14. Why is BCD used despite being less efficient than pure binary? → Easy conversion to/from human-readable decimal (e.g., calculators, digital displays)
15. Gray code for decimal 3 → **0010**
16. Key property of Gray code → Only one bit changes between consecutive values (reduces switching errors/glitches)
17. Convert binary 1011 to Gray code → **1110**
18. Excess-3 code for decimal 5 → **1000**
19. Number of bits needed to represent decimal 200 in binary → **8 bits** (2⁸=256 ≥200)
20. ASCII is an example of what type of code? → Alphanumeric code
21. Parity bit purpose → Detect single-bit transmission errors
22. Odd parity for 1011 → append **0** (already odd number of 1s → 3 ones, stays odd, so parity bit = 0)
23. Hamming code purpose → Detect **and correct** single-bit errors (beyond simple parity)
24. Which number system is most compact for representing binary data to humans? → Hexadecimal
25. Radix (base) of octal number system → **8**

---

## B. Boolean Algebra & Logic Gates (26–55)

26. A + A'B simplifies to → **A + B**
27. A(A+B) simplifies to → **A**
28. De Morgan's first theorem → (A+B)' = A'B'
29. De Morgan's second theorem → (AB)' = A'+B'
30. AB + AB' simplifies to → **A**
31. XOR truth table output for (1,1) → **0**
32. XNOR truth table output for (1,1) → **1**
33. Which gate is called a "universal gate"? → NAND and NOR (either alone can build any logic function)
34. Why is NAND preferred over NOR in CMOS fabrication? → NMOS-based NAND has better electron mobility/lower resistance than PMOS-based NOR, making NAND faster and smaller
35. Number of NAND gates to build a NOT gate → **1** (tie both inputs together)
36. Number of NAND gates to build an AND gate → **2** (NAND + NOT)
37. Number of NAND gates to build an OR gate → **3** (De Morgan's realization)
38. XOR gate can be built from how many 2-input NAND gates minimum? → **4**
39. Truth table rows for a 3-input gate → **8** (2³)
40. Buffer gate function → Passes input unchanged, used for signal strengthening/isolation, not logic inversion
41. Output of AND gate is 1 only when → All inputs are 1
42. Output of OR gate is 0 only when → All inputs are 0
43. Output of NOR gate is 1 only when → All inputs are 0
44. Complement of Boolean expression (A+B)C → A'B' + C'
45. Idempotent law states → A+A=A and A·A=A
46. Absorption law example → A + AB = A
47. Associative law applies to which operations? → AND and OR (not NOT)
48. Distributive law example → A(B+C) = AB + AC
49. Consensus theorem → AB + A'C + BC = AB + A'C (BC term is redundant)
50. Canonical SOP form uses which terms? → Minterms
51. Canonical POS form uses which terms? → Maxterms
52. A minterm is → A product term where every variable appears once, in true or complemented form
53. A maxterm is → A sum term where every variable appears once, in true or complemented form
54. Number of minterms possible for n variables → **2ⁿ**
55. Boolean function realized by only NAND gates is called → NAND-NAND implementation

---

## C. Karnaugh Maps & Minimization (56–75)

56. K-map used for how many variables typically (practical limit)? → Up to 4–5 variables (6+ becomes unwieldy, use Quine-McCarthy instead)
57. Adjacent cells in a K-map differ by → Exactly 1 bit
58. Groups in K-map must be sized as → Powers of 2 (1, 2, 4, 8...)
59. A "don't care" condition in K-map is marked as → X
60. Purpose of don't-care terms → Used to form larger, simpler groupings when convenient
61. Prime implicant definition → A product term that cannot be combined with any other term to form a larger group
62. Essential prime implicant → A prime implicant that covers at least one minterm not covered by any other prime implicant
63. Quine-McCluskey method used for → Tabular Boolean minimization, especially for more variables than K-maps handle well
64. SOP stands for → Sum of Products
65. POS stands for → Product of Sums
66. K-map wrap-around adjacency exists because → The map represents a toroidal (wrap-around) structure, so edge cells are adjacent to opposite edge cells
67. 3-variable K-map has how many cells? → **8**
68. 4-variable K-map has how many cells? → **16**
69. Overlapping groups in K-map are → Allowed, and often necessary for full minimization
70. Race condition (hazard) in logic circuits refers to → Momentary incorrect output due to unequal gate delays along different paths
71. Static-1 hazard → Output should stay 1 but briefly glitches to 0 during a transition
72. Static-0 hazard → Output should stay 0 but briefly glitches to 1 during a transition
73. How to eliminate a static hazard? → Add a redundant consensus term (extra gate) covering the transition boundary
74. Dynamic hazard → Output changes multiple times when it should change only once
75. K-map is a special case of which broader technique? → Truth table minimization / logic simplification

---

## D. Combinational Circuits — MUX, DEMUX, Encoders, Decoders (76–110)

76. MUX stands for → Multiplexer
77. A MUX with n select lines can choose from how many inputs? → **2ⁿ**
78. DEMUX function → Routes one input to one of multiple outputs, based on select lines
79. Decoder function → Converts n-bit binary input into 2ⁿ unique output lines (one active at a time)
80. Encoder function → Converts one active input line into an n-bit binary code (opposite of decoder)
81. Priority encoder differs from a plain encoder how? → Resolves conflicts when multiple inputs are active, by giving priority to the highest-order input
82. Number of inputs on a 3-to-8 decoder → **3 inputs, 8 outputs**
83. Half adder outputs → Sum and Carry
84. Half adder Sum equation → A XOR B
85. Half adder Carry equation → A AND B
86. Full adder adds how many bits? → **3** (A, B, and Carry-in)
87. Full adder Sum equation → A XOR B XOR Cin
88. Full adder Carry-out equation → AB + BCin + ACin
89. Number of half adders needed to build one full adder → **2** (plus an OR gate)
90. Ripple carry adder drawback → Carry propagation delay increases with number of bits (slow for wide adders)
91. Carry look-ahead adder advantage → Computes carries in parallel, much faster than ripple carry, at the cost of more hardware
92. Comparator circuit function → Compares two binary numbers and outputs which is greater/equal/smaller
93. A MUX can be used as a → Universal logic function generator (implements any Boolean function by feeding proper inputs to the data lines)
94. Implementing a 2-variable function with a 4:1 MUX needs how many select lines? → **2**
95. Implementing an n-variable Boolean function typically needs a MUX of size → 2ⁿ⁻¹:1 (using one variable as the select-independent input)
96. A code converter circuit example → Binary-to-Gray or BCD-to-7-segment converter
97. 7-segment decoder purpose → Converts BCD input to the segment pattern needed to display a digit
98. Parity generator vs parity checker → Generator creates a parity bit; checker verifies received data's parity for errors
99. Magnitude comparator for equal numbers outputs → A=B line goes high (1)
100. Combinational circuit defining property → Output depends only on current inputs, no memory of past state
101. Propagation delay definition → Time taken for output to respond to a change in input
102. tpHL vs tpLH → tpHL is delay for output High→Low transition; tpLH is delay for Low→High transition
103. Critical path in a circuit → The longest delay path determining maximum operating speed
104. Adder-subtractor circuit built using → Full adders + XOR gates (XOR toggles B input for subtraction via 2's complement)
105. Overflow in signed addition occurs when → Two numbers of the same sign produce a result of the opposite sign
106. ALU (Arithmetic Logic Unit) function → Performs arithmetic and logic operations selected via control/opcode lines
107. Barrel shifter function → Shifts/rotates a data word by a variable number of bit positions in a single cycle
108. Priority encoder used in which real application? → Interrupt handling (selecting the highest-priority interrupt request)
109. Tri-state buffer purpose → Allows an output to be driven, or electrically disconnected (high-impedance) — used for shared buses
110. High-impedance (Z) state used for → Allowing multiple devices to share a common bus without conflict

---

## E. Latches, Flip-Flops & Sequential Basics (111–140)

111. SR latch — invalid/forbidden state occurs when → S=1 and R=1 simultaneously (in NOR-based SR latch)
112. SR latch built from → Cross-coupled NOR (or NAND) gates
113. D latch function → Output follows D input while enable is high; holds when enable is low
114. Difference between latch and flip-flop → Latch is level-sensitive (transparent); flip-flop is edge-triggered
115. D flip-flop function → Captures D input value at the clock edge, holds it until next edge
116. JK flip-flop toggle condition → J=1, K=1 → output toggles
117. JK flip-flop hold condition → J=0, K=0 → output holds previous state
118. Why is JK flip-flop preferred over SR? → No invalid/forbidden state (J=K=1 gives a defined toggle instead of an undefined output)
119. T flip-flop function → Toggles output on every clock edge when T=1; holds when T=0
120. How to convert JK flip-flop to D flip-flop → Tie J = D, K = D' (complement)
121. How to convert JK flip-flop to T flip-flop → Tie J and K together (both = T)
122. Master-slave flip-flop purpose → Prevents race-around condition by using two latches (master captures on one clock phase, slave outputs on the other)
123. Race-around condition occurs in which flip-flop? → JK flip-flop, when clock pulse width is longer than propagation delay and J=K=1
124. Setup time definition → Minimum time input data must be stable before the clock edge
125. Hold time definition → Minimum time input data must remain stable after the clock edge
126. Clock-to-Q delay definition → Time taken for flip-flop output to change after the clock edge
127. Asynchronous reset vs synchronous reset → Asynchronous acts immediately regardless of clock; synchronous only takes effect on the next active clock edge
128. Metastability in flip-flops → An unstable, unpredictable output state caused by violating setup/hold time, usually resolved after settling time
129. How to reduce metastability risk in clock domain crossing? → Use a synchronizer (chain of 2 or more flip-flops)
130. Why use double flip-flop synchronizers? → Reduces the probability of metastability propagating to downstream logic
131. Positive edge-triggered flip-flop responds to → Rising (0→1) clock transition
132. Negative edge-triggered flip-flop responds to → Falling (1→0) clock transition
133. Flip-flop with both preset and clear active simultaneously → Generally an invalid/undefined condition (avoided in design)
134. Latch is transparent means → Output directly follows input while enabled, with no memory isolation
135. Why avoid latches in fully synchronous ASIC design? → Timing analysis becomes far more complex due to transparency (time borrowing across latch boundaries)
136. Where are latches still commonly and intentionally used? → Clock gating cells (ICG), and some low-power/high-speed custom paths
137. Flip-flop is a fundamental building block of which larger structures? → Registers, counters, memory elements, FSMs
138. A register is → A group of flip-flops used to store a multi-bit binary word
139. Shift register function → Moves stored bits left or right on each clock pulse
140. Types of shift registers → SISO, SIPO, PISO, PIPO (based on serial/parallel input and output combinations)

---

## F. Counters & Registers (141–165)

141. Mod-N counter definition → A counter that cycles through N distinct states before repeating
142. Number of flip-flops for mod-16 counter → **4**
143. Number of flip-flops for mod-10 (decade) counter → **4** (with reset logic, since 2³=8 < 10 ≤ 2⁴=16)
144. Asynchronous (ripple) counter drawback → Cumulative propagation delay through each flip-flop stage, limiting speed
145. Synchronous counter advantage → All flip-flops triggered by the same clock simultaneously, avoiding ripple delay
146. Up-counter vs down-counter → Up counts in increasing binary sequence; down counts in decreasing sequence
147. Ring counter function → Shift register where the output is fed back to the input, creating a single circulating 1 (or 0)
148. Johnson counter (twisted ring counter) → Feeds back the complemented output, doubling the number of unique states compared to a ring counter
149. Number of states in an n-bit ring counter → **n**
150. Number of states in an n-bit Johnson counter → **2n**
151. Self-correcting counter → A counter designed to return to a valid state sequence even if it enters an unused/invalid state
152. Presettable counter → A counter that can be loaded with an initial value rather than always starting from zero
153. Modulus of a counter defined by → Number of unique states before the sequence repeats
154. BCD counter counts from → 0000 to 1001 (0 to 9) then resets
155. Up/down counter control signal function → Selects counting direction (increment or decrement) each clock cycle
156. Why use synchronous reset over asynchronous reset in high-speed design? → Avoids reset signal acting as an unplanned/extra clock edge, keeping timing fully synchronous and easier to verify
157. Parallel load register function → Loads all bits simultaneously in one clock cycle, rather than serially
158. Universal shift register can perform → Serial/parallel load, shift left, shift right, and hold — all under mode control
159. Counter used in frequency division — how? → Each flip-flop stage divides the clock frequency by 2, so an n-stage counter divides by 2ⁿ
160. Why might a designer choose Gray code counters? → Only one bit changes per count, reducing glitches in downstream logic reading the counter output
161. Wrap-around in a counter means → After reaching its maximum count, it rolls back to zero (or minimum) on the next clock
162. LFSR (Linear Feedback Shift Register) used for → Pseudo-random sequence generation, built-in self-test (BIST), and CRC computation
163. Maximal-length LFSR cycles through how many states (n-bit, excluding all-zero)? → **2ⁿ − 1**
164. Watchdog timer function → A counter that resets the system if not periodically cleared, used to detect software/hardware hangs
165. Difference between a counter and a register → A counter has a fixed count sequence built in; a register simply stores/holds a value without incrementing it automatically

---

## G. Finite State Machines (166–185)

166. Mealy machine output depends on → Present state AND current input
167. Moore machine output depends on → Present state only
168. Which typically needs fewer states, Mealy or Moore? → Mealy
169. Which is glitch-free with respect to input changes, Mealy or Moore? → Moore (output tied only to state, changes cleanly on clock edge)
170. States needed to detect '0101' — Mealy and Moore respectively → **4 and 5**
171. FSM state diagram — a state is represented by → A circle/node
172. FSM state diagram — a transition is represented by → An arrow labeled with input (and output, for Mealy)
173. State encoding methods include → Binary encoding, one-hot encoding, Gray encoding
174. One-hot encoding uses how many flip-flops for n states? → **n** (one flip-flop per state)
175. Advantage of one-hot encoding → Simpler, faster next-state/output logic (often better timing) at the cost of more flip-flops
176. Advantage of binary encoding → Uses fewer flip-flops (log₂n) at the cost of more complex decode logic
177. State minimization purpose in FSM design → Reduce number of states by merging equivalent states, simplifying hardware
178. Two states are "equivalent" if → They produce the same output for every input sequence and transition to equivalent states
179. FSM used for control logic often implemented as → A combination of a state register (flip-flops) + next-state combinational logic + output combinational logic
180. Overlapping vs non-overlapping sequence detection → Overlapping allows the last part of one match to be the start of the next (e.g., '0101' matching in '010101'); non-overlapping resets fully after each match
181. Reset state in an FSM → The known starting state the machine enters on system reset
182. Why prefer Moore machine for output signals driving external hardware? → Avoids glitches, since output only changes synchronously with the clock
183. FSM design flow order → State diagram → state table → state assignment → next-state/output equations → circuit implementation
184. Deadlock state in FSM → A state from which the machine cannot transition out under normal operation (usually a design flaw, unless intentional)
185. Sequence detector for overlapping '1101' — why is Mealy usually chosen here? → Faster response (output changes same cycle as detecting input) and fewer states needed

---

## H. Timing, Setup/Hold & STA (186–205)

186. Setup violation cause → Data arrives too late relative to the clock edge (not enough setup margin)
187. Hold violation cause → Data arrives too early relative to the clock edge (races ahead of it)
188. Fix for setup violation → Reduce combinational path delay, or increase clock period
189. Fix for hold violation → Insert delay (buffers) on the fast path
190. Does increasing clock period fix a hold violation? → **No** — hold violations are independent of clock period
191. Clock skew definition → Difference in arrival time of the clock signal at different flip-flops due to routing/distribution delays
192. Positive clock skew effect → Can help setup time (if launch clock arrives earlier) but worsens hold time risk
193. Clock jitter definition → Cycle-to-cycle variation in clock edge timing (short-term, often due to noise)
194. Slack in timing analysis → Difference between required time and actual arrival time of a signal
195. Positive slack means → Timing requirement is met (there's margin)
196. Negative slack means → Timing violation (path is too slow/fast for the requirement)
197. Static Timing Analysis (STA) purpose → Verifies all timing paths in a design meet setup/hold requirements without needing full simulation
198. Why is STA preferred over simulation for large designs? → Much faster; checks all paths exhaustively rather than only simulated input vectors
199. Critical path definition → The path with the least slack (often the longest delay path) limiting the maximum clock frequency
200. False path in STA → A timing path that physically exists in the netlist but can never actually be sensitized/exercised in real operation
201. Multi-cycle path → A path intentionally allowed more than one clock cycle to settle, exempted from single-cycle timing checks
202. Clock domain crossing (CDC) risk → Metastability, when signals cross between two asynchronous clock domains
203. Common CDC mitigation technique → Double (or triple) flip-flop synchronizer
204. Why does a longer combinational logic path increase setup violation risk? → It takes longer for data to settle before the next clock edge, eating into the setup margin
205. On-chip variation (OCV) accounted for in STA because → Manufacturing/process, voltage, and temperature (PVT) variations cause real delay differences from nominal values

---

## I. CMOS Logic & VLSI Design Fundamentals (206–235)

206. CMOS stands for → Complementary Metal-Oxide-Semiconductor
207. CMOS inverter structure → PMOS (pull-up, connects to VDD) + NMOS (pull-down, connects to GND)
208. Why does CMOS have very low static power? → In steady state, only one of the pull-up/pull-down networks conducts, so no direct path from VDD to GND
209. Dynamic power in CMOS depends on → Switching frequency, supply voltage squared, and load capacitance
210. Short-circuit power in CMOS occurs when → Both PMOS and NMOS conduct briefly during a logic transition
211. Leakage (static) power sources in modern CMOS → Subthreshold leakage, gate leakage, junction leakage
212. Dynamic power formula → P = α·C·V²·f (α = switching activity factor)
213. Why does reducing supply voltage save power quadratically? → Dynamic power is proportional to V², so any voltage reduction has a squared effect on power savings
214. Threshold voltage (Vt) definition → Minimum gate-source voltage needed to form a conducting channel
215. PMOS threshold voltage sign convention → Negative
216. NMOS threshold voltage sign convention → Positive
217. Body effect (substrate bias effect) → Increases threshold voltage when there's a voltage difference between source and body/substrate
218. Channel length modulation effect → In saturation, drain current slightly increases with Vds due to effective channel length shortening
219. DIBL stands for → Drain Induced Barrier Lowering (a short-channel effect reducing threshold voltage as Vds increases)
220. Short-channel effects become significant when → Channel length becomes comparable to depletion region widths (very scaled-down technology nodes)
221. FinFET's key structural advantage → 3D fin-shaped channel wrapped by gate on multiple sides, giving stronger electrostatic control and less leakage
222. Why did the industry move from planar MOSFETs to FinFETs? → Better control over short-channel effects at very small technology nodes (better subthreshold slope, reduced leakage)
223. Gate-all-around (GAA) transistor → Next evolution after FinFET, where gate material surrounds the channel on all sides for even tighter control
224. Latch-up in CMOS circuits → A parasitic condition where parasitic bipolar transistors form a low-resistance path from VDD to GND, potentially destroying the chip
225. How to prevent latch-up? → Guard rings, proper substrate/well contacts, layout spacing rules
226. Noise margin definition → The amount of noise a logic signal can tolerate before being misinterpreted by the receiving gate
227. NMH and NML stand for → Noise Margin High and Noise Margin Low
228. Why is CMOS logic considered to have good noise immunity? → Full-swing output voltages and relatively large noise margins compared to some other logic families
229. Standard cell library used for → Pre-characterized logic gate layouts (timing, power, area) used by synthesis and place-and-route tools
230. Static CMOS logic vs dynamic (clocked) CMOS logic → Static logic always drives a valid output; dynamic logic relies on a precharge/evaluate clock phase and charge storage on a node
231. Domino logic → A form of dynamic CMOS logic chaining multiple stages, using inverting buffers between stages to avoid charge-sharing issues
232. Pass transistor logic drawback → Signal degradation (threshold voltage drop) when passing a strong logic level through certain transistor types
233. Transmission gate advantage over a single pass transistor → Passes both logic levels (0 and 1) at full strength, since PMOS and NMOS complement each other's weaknesses
234. Why is CMOS the dominant technology for large-scale digital ICs over bipolar/GaAs? → Low static power consumption and much higher achievable transistor density/integration
235. Technology scaling trend historically described by → Moore's Law (transistor count roughly doubling every ~18–24 months)

---

## J. Memory (236–255)

236. SRAM stands for → Static Random Access Memory
237. DRAM stands for → Dynamic Random Access Memory
238. Why does DRAM need periodic refresh but SRAM doesn't? → DRAM stores bits as charge on a capacitor that leaks over time; SRAM stores bits in a stable cross-coupled latch structure
239. Typical SRAM cell transistor count → 6 transistors (6T cell)
240. Typical DRAM cell transistor count → 1 transistor + 1 capacitor (1T1C cell)
241. Why is DRAM denser than SRAM? → Fewer transistors per cell, allowing much higher storage density per unit area
242. Why is SRAM faster than DRAM? → No refresh cycles needed and no capacitor charge/discharge delay; direct latch-based access
243. SRAM and DRAM are classified as → Volatile, read-write memory
244. ROM stands for → Read Only Memory
245. PROM → Programmable ROM (one-time programmable by the user)
246. EPROM → Erasable Programmable ROM (erased using UV light)
247. EEPROM → Electrically Erasable Programmable ROM (erased/rewritten electrically)
248. NAND Flash memory classified as a type of → EEPROM
249. Why is Flash memory non-volatile? → It retains stored charge on a floating gate even without power
250. NAND vs NOR Flash — which is denser? → NAND (better for storage-heavy applications like SSDs)
251. NAND vs NOR Flash — which allows faster random-access reads? → NOR (better for code execution, e.g., embedded firmware)
252. Cache memory purpose → Small, fast memory that stores frequently accessed data close to the processor to reduce access latency
253. Memory hierarchy order (fastest to slowest) → Registers → Cache → Main memory (RAM) → Secondary storage (disk/SSD)
254. Content Addressable Memory (CAM) → Memory searched by content/data value rather than by address, used in applications like network routing tables
255. Register file in a processor is essentially → A small, very fast multi-port SRAM-like storage array for CPU operands

---

## K. Analog Fundamentals & OPAMPs (256–275)

256. Ideal OPAMP open-loop gain → Infinity
257. Ideal OPAMP input impedance → Infinity
258. Ideal OPAMP output impedance → Zero
259. Virtual short concept in OPAMP circuits → In negative feedback configurations, the two input terminals are assumed to be at the same voltage
260. Why can an OPAMP be used as a comparator, integrator, or amplifier? → Its function depends entirely on the external feedback network connected around it
261. Common Mode Rejection Ratio (CMRR) measures → How well a differential amplifier rejects signals common to both inputs versus amplifying the true difference
262. Ideal CMRR value → Infinity (in practice, always finite)
263. Slew rate of an OPAMP → Maximum rate of change of output voltage per unit time, limiting how fast output can track fast input changes
264. Offset voltage in OPAMP → A small unwanted DC voltage difference needed between inputs to make output zero (due to component mismatch)
265. Zener diode operating region for voltage regulation → Reverse breakdown region
266. Why does Zener voltage stay nearly constant in breakdown? → A wide range of currents can flow through the device for a very small change in voltage in that region
267. Low-pass filter bandwidth equals → The cutoff (critical) frequency itself
268. Band-pass filter bandwidth equals → Difference between the upper and lower cutoff frequencies
269. Rectification efficiency formula → (Output power ÷ Input power) × 100
270. Intrinsic gain of a transistor formula → gm × ro (transconductance × output resistance)
271. Transconductance (gm) definition → Change in output current per unit change in input voltage
272. Output resistance (ro) significance in analog design → Higher ro means less current leaks through the output path, boosting achievable gain
273. Differential amplifier function → Amplifies the difference between two input signals while rejecting the common component
274. Common emitter current gain formula from common base gain → β = α / (1 − α)
275. Common base current gain (α) typical value range → Slightly less than 1 (e.g., 0.95–0.999)

---

## L. Data Converters & PLLs (276–290)

276. Nyquist sampling theorem requirement → Sampling frequency must be at least twice the highest input frequency component
277. What happens if sampling below Nyquist rate? → Aliasing — higher frequencies fold back and corrupt the reconstructed signal
278. Flash ADC operating principle → Compares input simultaneously against many reference voltages using parallel comparators (fast, but hardware-heavy)
279. SAR ADC operating principle → Performs a binary search, testing one bit at a time (slower, but much more hardware-efficient)
280. Sigma-Delta ADC known for → High resolution via oversampling and noise shaping, commonly used in audio applications
281. DAC resolution defined by → Number of output levels it can produce, tied to its bit-width (2ⁿ levels for n bits)
282. PLL stands for → Phase Locked Loop
283. Basic building blocks of a PLL → Phase detector, loop filter, voltage-controlled oscillator (VCO)
284. PLL phase detector function → Compares phase difference between the reference signal and feedback signal
285. PLL loop filter function → Smooths/filters the phase detector's error signal before driving the VCO
286. VCO function in a PLL → Generates an output frequency proportional to its control voltage
287. Common PLL applications → Clock generation, frequency synthesis, clock/data recovery
288. Why are PLLs important in mixed-signal chips? → They generate stable, synchronized clocks needed across different chip domains and interfaces
289. ADC quantization error → The inherent error from representing a continuous analog value with a finite number of discrete digital levels
290. Effective number of bits (ENOB) in an ADC → A practical measure accounting for noise/distortion, usually somewhat lower than the ADC's nominal bit resolution

---

## M. Fabrication & Process Technology (291–300)

291. Czochralski technique used for → Growing single-crystal silicon ingots for wafer production
292. Lithography purpose in chip fabrication → Transferring circuit patterns onto a photoresist-coated wafer using light/radiation through a mask
293. Doping purpose in semiconductor fabrication → Introducing impurity atoms to alter the electrical conductivity type (n-type or p-type) of silicon
294. Oxidation process purpose → Growing a silicon dioxide (SiO₂) layer, used for insulation and as a mask during processing
295. Etching purpose → Selectively removing material to define circuit patterns after lithography
296. Chemical Vapor Deposition (CVD) used for → Depositing thin films of material (like polysilicon or dielectrics) onto the wafer surface
297. Ion implantation purpose → A precise doping method that fires ions into the silicon at controlled energy/depth
298. Chemical Mechanical Polishing (CMP) purpose → Planarizing (flattening) the wafer surface between processing steps, essential for multi-layer interconnects
299. Why is silicon the dominant semiconductor material in the industry? → Abundant, stable native oxide (SiO₂) for excellent insulation, well-established low-cost processing infrastructure
300. Tape-out in chip design refers to → The final step of sending the completed, verified design layout to the foundry for fabrication

---

## How to use this bank
- These are compressed answers for rapid recall — for the topics flagged in your earlier prep doc (setup/hold, fanout wording, Mealy/Moore ordering, Vt vs channel length), go back to the concept explanations, not just the one-line answer here.
- In the interview itself, expect them to pick ~15-20 of these and ask you to *explain* or *draw*, not just state the answer — practice saying the "why" out loud, not just recalling the fact.
- If you want, I can turn any section (e.g., CMOS/VLSI or FSM) into practice flashcards or a timed self-quiz.
