n = int(input())
arr = list(map(int, input().split()))

mp = [0]*n

for i in arr:
    mp[i] += 1

i = 1
while i < n:
    print(i , mp[i])
    i += 2

❯ /home/siyam/MyCodes/MachineLearning/venv/bin/python /home/siyam/MyCodes/MachineLearning/course/freq.py
