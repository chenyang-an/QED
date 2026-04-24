\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{mathtools}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx}

% Theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\theoremstyle{remark}
\newtheorem{remark}{Remark}

\title{Properties of \(F_{\lambda,l}(R)\) from Modified Bessel Equations}
\author{}
\date{}

\begin{document}


# Proof

## Problem Statement
Let $\mathbb{T}^2=[-\pi,\pi]^2$. We say $\theta(x,y),(x,y)\in\mathbb{T}^2$ means $\theta$ is a periodic function in $x$ and $y$ of period $2\pi$.
\begin{problem}
Can you find a nonzero function $\theta_0(x,y)\in C^{\infty}(\mathbb{T}^2)$ with $\int_{\mathbb{T}^2}\theta_0(x,y)dxdy=0$, so that and there exists $u(y,t)\in L_t^{\infty}(W_y^{1,1}(\mathbb{T}))$, or $\int_{\mathbb{T}}|\partial_y u(y,t)|dy\leq C$ for some constant $C$, satisfies the following:
For the initial value problem:
\begin{equation}
\theta_t+u(y,t)\partial_x\theta=0, \quad\theta(x,y,0)=\theta_0,
\end{equation}
the solution satisfies
\begin{align*}
\|\theta\|_{\dot{H}^{-1}_{x,y}}(t)\leq C_1 e^{-C_2 t},
\end{align*}
for some constant $C_1$ and $C_2$. Here $\|\theta\|_{\dot{H}^{-1}_{x,y}}(t)$ is defined as follows:
\[
\|\theta\|^2_{\dot{H}^{-1}_{x,y}}(t)=\sum_{|n|>0,n\in\mathbb{Z}^2} \frac{1}{|n|^2}|\hat{\theta}(n)|^2,
\]
where $\hat{\theta}(n)$ is the $n$-th Fourier coefficient of $\theta$, namely $\hat{\theta}(n)=\int_{\mathbb{T}^2}\theta(x,y)e^{in\cdot (x,y)}dxdy$. 

Or, on the contrary, prove this is not possible.
\end{problem}

## Proof
We will prove the second alternative: **this exponential decay is not possible**. In fact, for every nonzero smooth mean-zero initial datum $\theta_0$ and every shear $u$ satisfying the stated assumption, the $\dot H^{-1}_{x,y}$ norm of the corresponding solution has a polynomial lower bound, so exponential decay cannot occur.

We write the Fourier coefficients exactly as in the problem statement:
\[
\hat\theta(k,m,t)=\int_{\mathbb T^2}\theta(x,y,t)e^{i(kx+my)}\,dx\,dy.
\]

### Step 1: A harmless reduction on the shear

The $y$-independent part of $u$ only causes a rigid translation in $x$, so we may subtract it. Since the problem assumes $u\in L_t^\infty(W_y^{1,1}(\mathbb T))$, the average
\[
\bar u(t):=\frac1{2\pi}\int_{-\pi}^{\pi}u(y,t)\,dy,
\]
is well-defined, and so is
\[
X(t):=\int_0^t \bar u(s)\,ds,
\]
and we define
\[
\widetilde\theta(x,y,t):=\theta(x+X(t),y,t).
\]
Then $\widetilde\theta$ solves
\[
\widetilde\theta_t+\widetilde u(y,t)\partial_x\widetilde\theta=0,
\qquad
\widetilde u(y,t):=u(y,t)-\bar u(t),
\]
and $\partial_y\widetilde u=\partial_yu$. Moreover, translation in $x$ does not change any Fourier modulus, so
\[
\hat{\widetilde\theta}(k,m,t)=e^{-ikX(t)}\hat\theta(k,m,t)
\qquad\text{for every }(k,m)\in\mathbb Z^2,
\]
hence
\[
\|\widetilde\theta\|_{\dot H^{-1}_{x,y}}(t)=\|\theta\|_{\dot H^{-1}_{x,y}}(t).
\]
Therefore we may assume, without loss of generality, that
\[
\int_{-\pi}^{\pi}u(y,t)\,dy=0\qquad\text{for every }t.
\]
From this point on, the proof uses only the bound $\|\partial_yu(\cdot,t)\|_{L^1(\mathbb T)}\le C$.

Because $u(\cdot,t)\in W^{1,1}(\mathbb T)\subset C(\mathbb T)$ and has mean zero, it takes both nonnegative and nonpositive values, so there exists $y_t\in\mathbb T$ such that $u(y_t,t)=0$. For any $y\in\mathbb T$, the one-dimensional fundamental theorem of calculus gives
\[
|u(y,t)|=\left|\int_{y_t}^{y}\partial_yu(z,t)\,dz\right|
\le \int_{-\pi}^{\pi}|\partial_yu(z,t)|\,dz
\le C,
\]
so $u$ is bounded and
\[
\Phi(y,t):=\int_0^t u(y,s)\,ds
\]
is well-defined. Also,
\[
\partial_y\Phi(y,t)=\int_0^t \partial_yu(y,s)\,ds
\]
in the distributional sense, hence
\[
\|\partial_y\Phi(\cdot,t)\|_{L^1(\mathbb T)}
\le \int_0^t \|\partial_yu(\cdot,s)\|_{L^1(\mathbb T)}\,ds
\le Ct.
\]

### Step 2: If there is no nonzero $x$-mode, the solution is stationary

Assume first that
\[
\hat\theta_0(k,m)=0\qquad\text{for every }k\neq0 \text{ and every }m\in\mathbb Z.
\]
Then $\theta_0$ is independent of $x$. The time-independent function
\[
\theta(x,y,t)=\theta_0(y)
\]
is a solution of the initial value problem. By uniqueness for this linear transport equation, the solution is stationary:
\[
\theta(x,y,t)=\theta_0(x,y)\qquad\text{for every }t\ge0.
\]
Because $\theta_0$ is mean zero and not identically zero, it has at least one nonzero Fourier coefficient with index $(0,m)$ and $m\neq0$. Therefore its $\dot H^{-1}_{x,y}$ norm is a fixed positive constant, so it cannot satisfy
\[
\|\theta\|_{\dot H^{-1}_{x,y}}(t)\le C_1e^{-C_2t}
\qquad (C_2>0)
\]
for all $t\ge0$.

Thus the only remaining possibility is that there exists at least one integer $k\neq0$ for which the $k$-th $x$-Fourier mode of $\theta_0$ is nonzero.

### Step 3: Exact evolution of one nonzero $x$-Fourier mode

Fix $k\in\mathbb Z\setminus\{0\}$ such that the function
\[
F_k^0(y):=\int_{-\pi}^{\pi}\theta_0(x,y)e^{ikx}\,dx
\]
is not identically zero. Since $\theta_0\in C^\infty(\mathbb T^2)$, we have
\[
F_k^0\in C^\infty(\mathbb T),\qquad F_k^0\not\equiv0.
\]

For the solution, define
\[
F_k(y,t):=\int_{-\pi}^{\pi}\theta(x,y,t)e^{ikx}\,dx.
\]
Integrating the equation $\theta_t+u(y,t)\theta_x=0$ against $e^{ikx}$ in $x$, we obtain
\[
\partial_tF_k(y,t)+u(y,t)\int_{-\pi}^{\pi}\theta_x(x,y,t)e^{ikx}\,dx=0.
\]
Because $\theta(\cdot,y,t)$ is $2\pi$-periodic in $x$,
\[
\int_{-\pi}^{\pi}\theta_x(x,y,t)e^{ikx}\,dx
=\Big[\theta(x,y,t)e^{ikx}\Big]_{x=-\pi}^{x=\pi}
-ik\int_{-\pi}^{\pi}\theta(x,y,t)e^{ikx}\,dx
=-ik\,F_k(y,t).
\]
Therefore
\[
\partial_tF_k(y,t)-ik\,u(y,t)F_k(y,t)=0.
\]
For each fixed $y$, this is an ordinary differential equation in $t$, so
\[
F_k(y,t)=e^{ik\Phi(y,t)}F_k^0(y).
\]
In particular,
\[
|F_k(y,t)|=|F_k^0(y)|\qquad\text{for every }y,t.
\]

### Step 4: The $L^2_y$ mass of this mode is conserved, and its $W^{1,1}_y$ norm grows at most linearly

Since multiplication by $e^{ik\Phi(y,t)}$ has modulus $1$,
\[
\int_{-\pi}^{\pi}|F_k(y,t)|^2\,dy
=\int_{-\pi}^{\pi}|F_k^0(y)|^2\,dy.
\]
Define
\[
S:=2\pi\int_{-\pi}^{\pi}|F_k^0(y)|^2\,dy.
\]
Because $F_k^0\not\equiv0$, we have $S>0$.

Next, differentiate $F_k(y,t)=e^{ik\Phi(y,t)}F_k^0(y)$ with respect to $y$ in the distributional sense:
\[
\partial_yF_k(y,t)=e^{ik\Phi(y,t)}\Big((F_k^0)'(y)+ik\,\partial_y\Phi(y,t)\,F_k^0(y)\Big).
\]
Hence
\[
\|\partial_yF_k(\cdot,t)\|_{L^1(\mathbb T)}
\le \|(F_k^0)'\|_{L^1(\mathbb T)}
+|k|\,\|F_k^0\|_{L^\infty(\mathbb T)}\,\|\partial_y\Phi(\cdot,t)\|_{L^1(\mathbb T)}.
\]
Using $\|\partial_y\Phi(\cdot,t)\|_{L^1}\le Ct$, we obtain
\[
\|\partial_yF_k(\cdot,t)\|_{L^1(\mathbb T)}
\le A+Bt,
\]
where
\[
A:=\|(F_k^0)'\|_{L^1(\mathbb T)},
\qquad
B:=|k|\,C\,\|F_k^0\|_{L^\infty(\mathbb T)}.
\]

### Step 5: Quantitative control of the $y$-Fourier tail

For each $m\in\mathbb Z$,
\[
\hat\theta(k,m,t)=\int_{-\pi}^{\pi}F_k(y,t)e^{imy}\,dy.
\]
By one-dimensional Parseval on $\mathbb T$,
\[
\sum_{m\in\mathbb Z}|\hat\theta(k,m,t)|^2
=2\pi\int_{-\pi}^{\pi}|F_k(y,t)|^2\,dy
=S.
\]

Now let $m\neq0$. Integrating by parts in $y$ and using periodicity,
\[
\hat\theta(k,m,t)
=\int_{-\pi}^{\pi}F_k(y,t)e^{imy}\,dy
=-\frac1{im}\int_{-\pi}^{\pi}\partial_yF_k(y,t)e^{imy}\,dy,
\]
because the boundary term
\[
\Big[\frac{F_k(y,t)e^{imy}}{im}\Big]_{y=-\pi}^{y=\pi}
\]
vanishes. Therefore
\[
|\hat\theta(k,m,t)|
\le \frac{\|\partial_yF_k(\cdot,t)\|_{L^1(\mathbb T)}}{|m|}
\le \frac{A+Bt}{|m|}.
\]

Let
\[
V(t):=A+Bt.
\]
Then, for every integer $N\ge1$,
\[
\sum_{|m|>N}|\hat\theta(k,m,t)|^2
\le V(t)^2\sum_{|m|>N}\frac1{m^2}.
\]
Since
\[
\sum_{|m|>N}\frac1{m^2}
=2\sum_{m=N+1}^{\infty}\frac1{m^2}
\le 2\int_N^\infty \frac{dx}{x^2}
=\frac2N,
\]
we get
\[
\sum_{|m|>N}|\hat\theta(k,m,t)|^2
\le \frac{2V(t)^2}{N}.
\]

Choose
\[
N(t):=\max\left\{1,\left\lceil \frac{4V(t)^2}{S}\right\rceil\right\}.
\]
Then $N(t)\ge 1$ and
\[
\sum_{|m|>N(t)}|\hat\theta(k,m,t)|^2
\le \frac{2V(t)^2}{N(t)}
\le \frac{S}{2}.
\]
Combining this with $\sum_m |\hat\theta(k,m,t)|^2=S$, we obtain
\[
\sum_{|m|\le N(t)}|\hat\theta(k,m,t)|^2
\ge \frac{S}{2}.
\]

### Step 6: A polynomial lower bound for $\|\theta\|_{\dot H^{-1}_{x,y}}(t)$

Since the $\dot H^{-1}_{x,y}$ norm is the sum of nonnegative terms, the contribution of the single fixed $x$-frequency $k$ gives
\[
\|\theta\|_{\dot H^{-1}_{x,y}}^2(t)
\ge \sum_{m\in\mathbb Z}\frac{|\hat\theta(k,m,t)|^2}{k^2+m^2}.
\]
For the terms with $|m|\le N(t)$ we have $k^2+m^2\le k^2+N(t)^2$, hence
\[
\sum_{m\in\mathbb Z}\frac{|\hat\theta(k,m,t)|^2}{k^2+m^2}
\ge \frac1{k^2+N(t)^2}\sum_{|m|\le N(t)}|\hat\theta(k,m,t)|^2
\ge \frac{S}{2\bigl(k^2+N(t)^2\bigr)}.
\]
Therefore
\[
\|\theta\|_{\dot H^{-1}_{x,y}}^2(t)
\ge \frac{S}{2\bigl(k^2+N(t)^2\bigr)}.
\]

It remains to bound $N(t)$ from above. Since
\[
V(t)^2=(A+Bt)^2\le 2A^2+2B^2t^2\le 2(A^2+B^2)(1+t^2),
\]
the definition of $N(t)$ gives
\[
N(t)\le 1+\frac{4V(t)^2}{S}
\le 1+\frac{8(A^2+B^2)}{S}(1+t^2).
\]
Set
\[
D:=1+\frac{8(A^2+B^2)}{S}.
\]
Then
\[
N(t)\le D(1+t^2).
\]
Hence
\[
N(t)^2\le D^2(1+t^2)^2\le 2D^2(1+t^4),
\]
because $(1+t^2)^2=1+2t^2+t^4\le 2(1+t^4)$. Consequently,
\[
k^2+N(t)^2\le (k^2+2D^2)(1+t^4).
\]
Substituting this into the previous lower bound, we obtain
\[
\|\theta\|_{\dot H^{-1}_{x,y}}^2(t)
\ge \frac{S}{2(k^2+2D^2)}\cdot \frac1{1+t^4}.
\]
Since $S>0$, the constant
\[
c_*:=\frac{S}{2(k^2+2D^2)}
\]
is strictly positive. Therefore
\[
\|\theta\|_{\dot H^{-1}_{x,y}}^2(t)\ge \frac{c_*}{1+t^4},
\]
and hence
\[
\|\theta\|_{\dot H^{-1}_{x,y}}(t)\ge \frac{\sqrt{c_*}}{1+t^2}
\qquad\text{for every }t\ge0,
\]
because $\sqrt{1+t^4}\le 1+t^2$.

### Step 7: Contradiction with exponential decay

Suppose, for contradiction, that there exist constants $C_1>0$ and $C_2>0$ such that
\[
\|\theta\|_{\dot H^{-1}_{x,y}}(t)\le C_1e^{-C_2t}
\qquad\text{for all }t\ge0.
\]
Combining this with the polynomial lower bound just proved gives
\[
\frac{\sqrt{c_*}}{1+t^2}\le C_1e^{-C_2t}
\qquad\text{for all }t\ge0.
\]
Equivalently,
\[
\sqrt{c_*}\,e^{C_2t}\le C_1(1+t^2)
\qquad\text{for all }t\ge0.
\]
But the left-hand side grows exponentially in $t$, while the right-hand side grows only polynomially, so this is impossible for all sufficiently large $t$.

This contradiction shows that no such pair $(\theta_0,u)$ can exist.

Therefore the correct answer to the problem is: **it is not possible**.

## Key Ideas
- A horizontal shear preserves each $x$-Fourier mode separately; a nonzero $x$-mode evolves only by multiplication with a phase $e^{ik\Phi(y,t)}$.
- For such a mode, the $L^2_y$ mass is exactly conserved, while the $W^{1,1}_y$ norm can grow at most linearly because $\|\partial_yu(\cdot,t)\|_{L^1}$ is uniformly bounded.
- The $W^{1,1}$ bound implies $|\hat\theta(k,m,t)|\lesssim (1+t)/|m|$ for $m\neq0$, so only a controlled amount of the mode’s mass can move into very high $y$-frequencies.
- A fixed positive portion of that mass must remain at $|m|\lesssim 1+t^2$, yielding $\|\theta\|_{\dot H^{-1}_{x,y}}(t)\gtrsim (1+t^2)^{-1}$ and ruling out exponential decay.





\end{document}