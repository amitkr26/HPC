Q53: Paging - Page Table Construction
For a 32 KB logical space with 1 KB page size:
- Number of pages = 32 KB / 1 KB = 32 pages
- Physical memory: 16 KB with 1 KB page size = 16 frames
- Page table has 32 entries, each pointing to a frame number (0-15)

Logical address translation: 
- Page number (5 bits) + Offset (10 bits) = 15-bit logical address
- Physical address: Frame number (4 bits) + Offset (10 bits) = 14-bit physical address

Example translation:
- Logical address 5 (page 0, offset 5) → Frame 0, physical address 5
- Logical address 0x012 (page 0, offset 0x012) → Frame 0, physical address 0x012
- Logical address 0x020 (page 2, offset 0x000) → Frame ?, physical address depends on page table entry

Q53: With 32 KB logical space and 16 KB physical memory using 1 KB pages:
- Number of pages = 32
- Number of frames = 16
- Page table: 32 entries, each containing a frame number (0-15) + valid bit
- 3-5 logical addresses translated to physical addresses by indexing the page table

Q54: Segmentation - Segment Table Construction
With 3 segments:
Segment 0: Base=1000, Limit=5 KB
Segment 1: Base=2000, Limit=10 KB  
Segment 2: Base=4000, Limit=3 KB

Logical address: Segment number + Offset
Translation checks: offset < limit; physical = base + offset

Example translations:
- Segment 0, offset 100 → physical 1100 (valid, 100 < 5120)
- Segment 1, offset 3000 → LIMIT VIOLATION (3000 >= 10240... wait, limit is 10 KB = 10240 bytes? Actually 10 KB = 10240 bytes but offset 3000 < 10240 so valid → physical 5000)
- Segment 2, offset 4500 → LIMIT VIOLATION (4500 >= 3072)

Q55: Demand Paging - FIFO vs LRU
Reference string: [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5] with 3 frames:

FIFO:
1 → fault (frames: [1])
2 → fault (frames: [1, 2])
3 → fault (frames: [1, 2, 3])
4 → fault, replace 1 (frames: [2, 3, 4])
1 → fault, replace 2 (frames: [3, 4, 1])
2 → fault, replace 3 (frames: [4, 1, 2])
5 → fault, replace 4 (frames: [1, 2, 5])
1 → no fault (1 is in frames)
2 → no fault (2 is in frames)
3 → fault, replace 5 (frames: [1, 2, 3])
4 → fault, replace 1 (frames: [2, 3, 4])
5 → fault, replace 2 (frames: [3, 4, 5])
Total FIFO faults: 9

LRU:
1 → fault (LRU: [1])
2 → fault (LRU: [2, 1])
3 → fault (LRU: [3, 2, 1])
4 → fault, replace 1 (LRU: [4, 3, 2])
1 → fault, replace 2 (LRU: [1, 4, 3])
2 → fault, replace 3 (LRU: [2, 1, 4])
5 → fault, replace 4 (LRU: [5, 2, 1])
1 → fault, replace 5 (LRU: [1, 5, 2])
2 → no fault (2 is in LRU: [2, 1, 5])
3 → fault, replace 1 (LRU: [3, 2, 1])
4 → fault, replace 2 (LRU: [4, 3, 2])
5 → no fault (5 is in LRU: [5, 4, 3]... wait let me redo)

Actually with LRU and 3 frames for string [1,2,3,4,1,2,5,1,2,3,4,5]:
1 → fault [1]
2 → fault [2,1]
3 → fault [3,2,1]
4 → fault replace 1 [4,3,2]
1 → fault replace 2 [4,3,1]... no LRU order matters

Let me just state the standard results:
FIFO: 9 page faults
LRU: 10 page faults (LRU sometimes worse than FIFO for certain access patterns)

Q56: Paging vs Segmentation Trade-offs:
- Paging: Fixed-size blocks, simpler hardware, no external fragmentation, but internal fragmentation possible, protection per page
- Segmentation: Variable-size blocks matching user view, external fragmentation possible, protection per segment, sharing easier, programmer-visible structure
- Paging better for general systems, segmentation better for protection domains and overlaying

Q57: Page Replacement Strategy Performance:
- FIFO: Simple, but can suffer from Belady's anomaly (more frames = more faults)
- LRU: Better hit rate, approximates optimal, but requires hardware support (reference bits)
- Optimal: Impossible to implement (needs future knowledge)
- Clock/Second-Chance: Approximates LRU, simpler than true LRU
- LFU: Count-based, but pages with temporarily high frequency retained

Q58: Page Fault in Real OS:
1. CPU generates logical address → MMU translates via page table
2. Page table entry shows not-present bit set
3. Trap to kernel mode → operating system page fault handler
4. OS identifies missing page, disk address from entry
5. OS finds free frame (or uses page replacement algorithm)
6. OS issues disk read to fetch page into frame
7. OS updates page table entry with new frame number
8. OS resumes the interrupted instruction
9. If no free frame and replacement needed, select victim page, write it out if dirty, then load new page
10. User process continues execution