#!/usr/bin/env python
# coding: utf-8

# In[69]:


import numpy as np
import matplotlib.pyplot as plt
import math


# In[ ]:


class Value:

    def __init__(self ,data, _children=(), _op='', label='') -> None:
        self.data = data 
        self.grad = 0.0
        self._backward = lambda : None
        self._prev = set(_children)
        self._op = _op
        self.label = label


    def __repr__(self) -> str:
        return f"Value(data={self.data})"

    def __add__(self, other):
        out = Value(self.data + other.data, (self,other), '+')

        def _backward():
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        out = Value(self.data * other.data, (self,other), '*')

        def _backward():
            self.grad += out.grad * other.data
            other.grad += out.grad * self.data

        out._backward = _backward
        return out

    def tanh(self):
        x = self.data
        t = (math.exp(2*x) - 1) / (math.exp(2*x) + 1)
        out = Value(t, (self, ), 'tanh')

        def _backward():
            self.grad += (1 - t**2) * out.grad

        out._backward = _backward

        return out

    def backward(self):        
        topo = []
        visited = set()

        def build_topo(v):
            if v not in visited:
                visited.add(v)

                for child in v._prev:
                    build_topo(child)

                topo.append(v)

        build_topo(self)
        self.grad = 1.0

        for node in reversed(topo):
            node._backward()

    def zero_grad(self):
        visited = set()

        def reset(v):
            if v not in visited:
                visited.add(v)
                v.grad = 0.0

                for child in v._prev:
                    reset(child)

        reset(self)





# In[71]:


from graphviz import Digraph

def trace(root):
    nodes, edges = set(), set()

    def build(v):
        if v not in nodes:
            nodes.add(v)
            for child in v._prev:
                edges.add((child, v))
                build(child)

    build(root)
    return nodes, edges


def draw_dot(root):
    dot = Digraph(format='svg', graph_attr={'rankdir': 'LR'})

    nodes, edges = trace(root)

    for n in nodes:
        uid = str(id(n))

        dot.node(name = uid, label = "{ %s | data %.4f | grad %.4f}" % (n.label, n.data, n.grad), shape='record')
        if n._op:
            dot.node(name=uid + n._op , label=n._op)
            dot.edge(uid + n._op, uid)

    for n1, n2 in edges:
        dot.edge(str(id(n1)), str(id(n2)) + n2._op)

    return dot



# In[97]:


a = Value(2.0, label='a')
b = Value(-3.0, label='b')
c = Value(10.0,label='c')

e = a*b; e.label='e'
d = e+c
d.label= 'd'
f = Value(-2.0, label='f')
L = d*f
L.label = 'L'


# In[98]:


# f.grad = 4.0 # dL/df = d
# d.grad = -2.0 # dL/dd = f
# L.grad = 1.0
# c.grad = -2.0
# e.grad = -2.0
# a.grad = 6.0
# b.grad = -4.0


# In[100]:


L.zero_grad()
L.backward()
draw_dot(L)


# In[ ]:


# def lol():
#     h = 0.001

#     a = Value(2.0, label='a')
#     b = Value(-3.0, label='b')
#     c = Value(10.0,label='c')
#     e = a*b; e.label='e'
#     d = e+c; d.label= 'd'
#     f = Value(-2.0, label='f')
#     L = d*f; L.label = 'L'
#     L1 = L.data

#     a = Value(2.0, label='a')
#     b = Value(-3.0 + h, label='b')
#     c = Value(10.0,label='c')
#     e = a*b; e.label='e'
#     d = e+c; d.label= 'd'
#     f = Value(-2.0, label='f')
#     L = d*f; L.label = 'L'
#     L2 = L.data

#     print((L2 - L1) / h)

# lol()


# In[76]:


plt.plot(np.arange(-5,5,0.2), np.tanh(np.arange(-5,5,0.2))); plt.grid()


# In[ ]:


# # inputs x1,x2
# x1 = Value(2.0, label='x1')
# x2 = Value(0.0, label='x2')

# # weights w1,w2
# w1 = Value(-3.0, label='w1')
# w2 = Value(1.0, label='w2')

# # bias of the neuron
# b = Value(6.8813735870195432, label='b')

# x1w1 = x1*w1; x1w1.label = 'x1*w1'
# x2w2 = x2*w2; x2w2.label = 'x2*w2'
# x1w1x2w2 = x1w1 + x2w2
# x1w1x2w2.label = 'x1*w1 + x2*w2'
# # neuron
# n = b + x1w1x2w2 ; n.label = 'n'
# # output
# o = n.tanh(); o.label = 'o'
# L1 = o.data


# # ============================================== #

# # inputs x1,x2
# h = Value(0.001, 'h')

# x1 = Value(2.0, label='x1')
# x2 = Value(0.0, label='x2')

# # weights w1,w2
# w1 = Value(-3.0, label='w1')
# w1.data += h.data

# w2 = Value(1.0, label='w2')

# # bias of the neuron
# b = Value(6.8813735870195432, label='b')

# x1w1 = x1*w1; x1w1.label = 'x1*w1'
# x2w2 = x2*w2; x2w2.label = 'x2*w2'
# x1w1x2w2 = x1w1 + x2w2
# x1w1x2w2.label = 'x1*w1 + x2*w2'


# # neuron
# n = b + x1w1x2w2; n.label = 'n'
# # output
# o = n.tanh(); o.label = 'o'



# L2 = o.data

# print((L2 - L1) / h.data)


# In[81]:


o.zero_grad()


# In[90]:


o.backward()


# In[93]:


o.zero_grad()
o.backward()

for node in [o, n, x1w1x2w2, b, x1w1, x2w2, x1, x2, w1, w2]:
    print(f"{node.label:15} data={node.data:.4f} grad={node.grad:.4f}")


# In[89]:


draw_dot(o)


# $$
# o = \tanh(n)
# $$
# 
# $$
# \frac{do}{dn}
# = \frac{d}{dn}(\tanh(n))
# $$
# 
# $$
# = 1-\tanh^2(n)
# $$
# 
# Since, $o=\tanh(n)$
# 
# $$
# \boxed{\frac{do}{dn}=1-o^2}
# $$

# In[88]:


# o.grad = 1.0
# n.grad = 0.5
# x1w1x2w2.grad = 0.5
# b.grad = 0.5
# x2w2.grad = 0.5
# x1w1.grad = 0.5
# x1.grad = -1.5
# x2.grad = 0.5
# w1.grad = 1
# w2.grad = 0


# In[ ]:


# def hello():
#     print("Hello world")

# x = hello
# x


# WRITE STORY DOWN WHO WILL YOU BECOME 10 YEARS LATER

# In[ ]:




