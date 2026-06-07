import numpy as np 

x = np.array([3,4,3])
y = np.array([6,9,8])
z = np.array([[3],[4]])

# L2 Norm
print(np.linalg.norm(x))

# L1 Norm
print(np.linalg.norm(x, ord=1))

# Infinity norm
print(np.linalg.norm(x, ord=np.inf))

# distance 
distance = 0

for i in range(x.size):
    distance += abs(x[i] - y[i])

print(distance)

dist = np.linalg.norm(y - x, ord=1)

print(dist)
print(dist == distance)

print(np.linalg.norm(z))