import numpy as np
# Part 1: Basic 1D Slicing (start:stop:step)
arr_1d = np.arange(10)
ans_1 = arr_1d[2:7]
print(ans_1)
ans_2 = arr_1d[::2]
print(ans_2)
ans_3 = arr_1d[-3:]
print(ans_3)
ans_4 = arr_1d[::-1]
print(ans_4)

# Part 2: Multidimensional Slicing (2D)
ans_5 = arr_2d[2, 3]
print(ans_5)
ans_6 = arr_2d[2, :]
print(ans_6)
ans_7 = arr_2d[:, 3]
print(ans_7)
ans_8 = arr_2d[1:4, 1:4]
print(ans_8)
ans_9 = arr_2d[::2, ::-1]
print(ans_9)