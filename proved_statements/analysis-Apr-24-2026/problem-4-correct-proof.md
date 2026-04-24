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
Consider the advection diffusion equation in $\mathbb{T}^2$:
\begin{equation}\label{shear}
    \partial_t \rho + U(t,y)\,\partial_x \rho = \Delta \rho.
\end{equation}
Assume that $0\neq \rho(0,\cdot) \in L^2_{x,y}$ is mean-zero and that 
\[
\|U\|_{L^{\infty}_t L^2_y} < \infty.
\]
Then we have for the weak solution $\rho$,
\begin{equation}
\liminf\limits_{t\rightarrow\infty}\frac{\|\rho(t)\|_{\dot{H}^{-1}}}{\|\rho(t)\|_{L^2}}>0.
\end{equation}
\end{problem}

## Proof
We use one known input from the literature survey: for every nonzero mean-zero solution of
\[
\partial_t \theta + U(t,y)\,\partial_x\theta=\Delta\theta
\]
with the same shear $U$, there exist constants $c,\gamma>0$ such that
\[
\|\theta(t)\|_{L^2_{x,y}}\ge c\,e^{-\gamma t}\qquad\text{for all }t\ge0.
\]
This is the exponential $L^2$ lower bound proved by Huang and Xu. The rest of the argument is self-contained.

Write the Fourier series in the $x$ variable:
\[
\rho(t,x,y)=\sum_{k\in\mathbb Z}u_k(t,y)e^{ikx},
\qquad
u_k(t,y):=\frac1{2\pi}\int_{\mathbb T}\rho(t,x,y)e^{-ikx}\,dx.
\]
Since the equation is linear and $U$ depends only on $(t,y)$, each $u_k$ solves
\begin{equation}\label{eq:mode}
\partial_t u_k + ik\,U(t,y)u_k=\partial_{yy}u_k-k^2u_k
\end{equation}
in the weak sense.

Let $\widehat{u_k}(t,\ell)$ be the $y$-Fourier coefficients of $u_k(t,\cdot)$. Define
\[
E_k(t):=\|u_k(t)\|_{L^2_y}^2=\sum_{\ell\in\mathbb Z}|\widehat{u_k}(t,\ell)|^2
\]
and
\[
F_k(t):=
\begin{cases}
\displaystyle \sum_{\ell\in\mathbb Z}\frac{|\widehat{u_k}(t,\ell)|^2}{k^2+\ell^2},&k\neq0,\\[2ex]
\displaystyle \sum_{\ell\neq0}\frac{|\widehat{u_0}(t,\ell)|^2}{\ell^2},&k=0.
\end{cases}
\]
Then Parseval gives
\begin{equation}\label{eq:sumdecomp}
\|\rho(t)\|_{L^2}^2=\sum_{k\in\mathbb Z}E_k(t),
\qquad
\|\rho(t)\|_{\dot H^{-1}}^2=\sum_{k\in\mathbb Z}F_k(t).
\end{equation}

We first prove a modewise lower bound.

### Claim 1
For every $k\in\mathbb Z$ such that $u_k\not\equiv0$, there exist constants $c_k>0$ and $T_k\ge0$ such that
\begin{equation}\label{eq:modewise-lb}
F_k(t)\ge c_k\,E_k(t)\qquad\text{for all }t\ge T_k.
\end{equation}

#### Proof of Claim 1: the case $k=0$
The equation for $u_0$ is the one-dimensional heat equation
\[
\partial_t u_0=\partial_{yy}u_0.
\]
Because the total mean of $\rho$ is zero, the $y$-average of $u_0$ is zero:
\[
\widehat{u_0}(t,0)=0.
\]
Let $\ell_0\ge1$ be the smallest integer such that $\widehat{u_0}(0,\pm \ell_0)$ is not both zero. Then
\[
\widehat{u_0}(t,\ell)=e^{-\ell^2 t}\widehat{u_0}(0,\ell),
\]
so the terms with $|\ell|=\ell_0$ dominate both $E_0(t)$ and $F_0(t)$ as $t\to\infty$. Therefore
\[
\lim_{t\to\infty}\frac{F_0(t)}{E_0(t)}=\frac1{\ell_0^2}>0.
\]
Hence \eqref{eq:modewise-lb} holds for $k=0$.

#### Proof of Claim 1: the case $k\neq0$
Fix $k\neq0$ with $u_k\not\equiv0$. The function
\[
\rho^{(k)}(t,x,y):=u_k(t,y)e^{ikx}
\]
is itself a nonzero mean-zero solution of the same advection-diffusion equation. By the exponential $L^2$ lower bound quoted at the beginning, there exist constants $a_k,\Gamma_k>0$ such that
\begin{equation}\label{eq:mode-exp-lb}
E_k(t)=\|u_k(t)\|_{L^2_y}^2\ge a_k e^{-\Gamma_k t}\qquad\text{for all }t\ge0.
\end{equation}

Fix an integer $N\ge1$ so large that
\begin{equation}\label{eq:N-conditions}
2N+1\ge 4C_0^2 k^2 M^2
\qquad\text{and}\qquad
2\Bigl(k^2+\frac{(N+1)^2}{2}\Bigr)>\Gamma_k,
\end{equation}
where
\[
M:=\|U\|_{L_t^\infty L_y^2},
\]
and $C_0$ is an absolute constant for which
\begin{equation}\label{eq:Bernstein}
\|P_{\le N}f\|_{L^\infty_y}\le C_0\sqrt{2N+1}\,\|P_{\le N}f\|_{L^2_y}
\end{equation}
holds for every $f\in L^2(\mathbb T_y)$, with $P_{\le N}$ denoting the projection to the $y$-Fourier modes $|\ell|\le N$.

Let
\[
u^L:=P_{\le N}u_k,\qquad u^H:=(I-P_{\le N})u_k,
\]
and define
\[
L(t):=\|u^L(t)\|_{L^2_y}^2,\qquad H(t):=\|u^H(t)\|_{L^2_y}^2.
\]
Then
\[
E_k(t)=L(t)+H(t).
\]

Set
\[
A_k:=-\partial_{yy}+k^2.
\]
Equation \eqref{eq:mode} can be rewritten as
\[
\partial_t u_k + A_k u_k = -ik\,Uu_k.
\]
Because $P_{\le N}$ commutes with $A_k$, and because the multiplication operator $-ikU$ is skew-adjoint on $L^2_y$, taking the real part of the $L^2_y$ inner products with $u^L$ and $u^H$ yields
\begin{align}
\frac12 H'(t)+\langle A_k u^H(t),u^H(t)\rangle &= T(t),\label{eq:H-eq}\\
\frac12 L'(t)+\langle A_k u^L(t),u^L(t)\rangle &= -T(t),\label{eq:L-eq}
\end{align}
where
\[
T(t):=\Re\langle -ik\,U(t,\cdot)\,u^L(t),u^H(t)\rangle.
\]
Indeed,
\[
\Re\langle -ikUu^L,u^L\rangle=\Re\langle -ikUu^H,u^H\rangle=0,
\]
and
\[
\Re\langle -ikUu^H,u^L\rangle=-\Re\langle -ikUu^L,u^H\rangle,
\]
because $\langle Uu^H,u^L\rangle=\overline{\langle Uu^L,u^H\rangle}$ and $-ik$ is purely imaginary.

We next bound $T(t)$. By Cauchy-Schwarz, Hölder, and \eqref{eq:Bernstein},
\begin{align}
|T(t)|
&\le |k|\,\|U(t,\cdot)\|_{L^2_y}\,\|u^L(t)\|_{L^\infty_y}\,\|u^H(t)\|_{L^2_y}\notag\\
&\le C_0 |k| M \sqrt{2N+1}\,\sqrt{L(t)H(t)}.\label{eq:T-bound}
\end{align}

Now define
\[
Z(t):=H(t)-L(t).
\]
Subtracting \eqref{eq:L-eq} from \eqref{eq:H-eq} gives
\begin{equation}\label{eq:Zprime}
Z'(t)= -2\Bigl(\langle A_k u^H,u^H\rangle-\langle A_k u^L,u^L\rangle\Bigr)+4T(t).
\end{equation}

Suppose that $Z(t)=0$. Then $H(t)=L(t)=E_k(t)/2$. Since $u^H$ contains only $y$-frequencies $|\ell|\ge N+1$ while $u^L$ contains only $|\ell|\le N$, we have
\[
\langle A_k u^H,u^H\rangle\ge \bigl(k^2+(N+1)^2\bigr)H(t),
\qquad
\langle A_k u^L,u^L\rangle\le \bigl(k^2+N^2\bigr)L(t).
\]
Using these inequalities, together with $H=L=E_k/2$ and \eqref{eq:T-bound}, in \eqref{eq:Zprime} we obtain
\begin{align*}
Z'(t)
&\le -2\Bigl(k^2+(N+1)^2\Bigr)\frac{E_k(t)}2
+2\Bigl(k^2+N^2\Bigr)\frac{E_k(t)}2
+4C_0 |k| M \sqrt{2N+1}\,\frac{E_k(t)}2\\
&= \Bigl(-(2N+1)+2C_0 |k| M \sqrt{2N+1}\Bigr)E_k(t).
\end{align*}
The first condition in \eqref{eq:N-conditions} implies
\[
2C_0 |k| M \sqrt{2N+1}\le 2N+1,
\]
hence
\[
Z'(t)\le0\qquad\text{whenever }Z(t)=0.
\]
Therefore the region
\[
\{\,t\ge0:\ H(t)\le L(t)\,\}
\]
is forward invariant: once $H\le L$ holds at some time, it continues to hold for all later times.

We now show that $H\le L$ must occur at some time. Assume, to the contrary, that
\[
H(t)>L(t)\qquad\text{for all sufficiently large }t.
\]
Then $H(t)\ge E_k(t)/2$ for all sufficiently large $t$. Since
\[
E_k'(t)=-2\langle A_k u_k(t),u_k(t)\rangle
\]
and
\[
\langle A_k u_k,u_k\rangle
=\langle A_k u^L,u^L\rangle+\langle A_k u^H,u^H\rangle
\ge k^2E_k(t)+(N+1)^2H(t),
\]
we get, for all sufficiently large $t$,
\[
E_k'(t)\le -2\Bigl(k^2+\frac{(N+1)^2}{2}\Bigr)E_k(t).
\]
Gronwall's inequality then implies that $E_k(t)$ decays at least like
\[
e^{-2\left(k^2+\frac{(N+1)^2}{2}\right)t},
\]
which contradicts \eqref{eq:mode-exp-lb} because of the second condition in \eqref{eq:N-conditions}. Hence there exists a time $T_k$ such that
\[
H(T_k)\le L(T_k).
\]
By forward invariance, this yields
\[
H(t)\le L(t)\qquad\text{for all }t\ge T_k.
\]
Consequently,
\[
L(t)\ge \frac12 E_k(t)\qquad\text{for all }t\ge T_k.
\]

Finally, since $u^L$ contains only modes $|\ell|\le N$,
\[
F_k(t)\ge \sum_{|\ell|\le N}\frac{|\widehat{u_k}(t,\ell)|^2}{k^2+\ell^2}
\ge \frac1{k^2+N^2}\sum_{|\ell|\le N}|\widehat{u_k}(t,\ell)|^2
=\frac{L(t)}{k^2+N^2}.
\]
Therefore, for all $t\ge T_k$,
\[
F_k(t)\ge \frac{1}{2(k^2+N^2)}\,E_k(t).
\]
This proves \eqref{eq:modewise-lb} for $k\neq0$ as well. Claim 1 is proved.

### Claim 2
There exists an integer $K\ge0$ such that
\begin{equation}\label{eq:xtail}
\frac{\sum_{|k|>K}E_k(t)}{\|\rho(t)\|_{L^2}^2}\longrightarrow 0
\qquad\text{as }t\to\infty.
\end{equation}

#### Proof of Claim 2
Apply the exponential lower bound to the full solution $\rho$. There exist constants $a,\Gamma>0$ such that
\[
\|\rho(t)\|_{L^2}^2\ge a e^{-\Gamma t}\qquad\text{for all }t\ge0.
\]
Choose $K$ so large that
\[
2(K+1)^2>\Gamma.
\]
For every $|k|>K$, the modewise energy identity gives
\[
E_k'(t)=-2\langle A_k u_k(t),u_k(t)\rangle\le -2k^2 E_k(t)\le -2(K+1)^2 E_k(t).
\]
Hence
\[
E_k(t)\le e^{-2(K+1)^2 t}E_k(0),
\]
and summing over $|k|>K$ yields
\[
\sum_{|k|>K}E_k(t)\le e^{-2(K+1)^2 t}\sum_{|k|>K}E_k(0).
\]
Dividing by $\|\rho(t)\|_{L^2}^2\ge a e^{-\Gamma t}$ gives \eqref{eq:xtail}, because $2(K+1)^2-\Gamma>0$. Claim 2 is proved.

We now finish the proof of the theorem.

Let $K$ be given by Claim 2. For each integer $k$ with $|k|\le K$ and $u_k\not\equiv0$, Claim 1 provides constants $c_k>0$ and $T_k$ such that
\[
F_k(t)\ge c_k E_k(t)\qquad\text{for all }t\ge T_k.
\]
If $u_k\equiv0$, then $E_k(t)=F_k(t)=0$ for all $t$. Since there are only finitely many integers with $|k|\le K$, we may define
\[
c_*:=\min\{\,c_k:\ |k|\le K,\ u_k\not\equiv0\,\}>0,
\qquad
T_*:=\max\{\,T_k:\ |k|\le K,\ u_k\not\equiv0\,\}.
\]
This finite set is nonempty: otherwise $E_k\equiv0$ for all $|k|\le K$, so
\[
\sum_{|k|>K}E_k(t)=\|\rho(t)\|_{L^2}^2
\]
for every $t$, contradicting Claim 2.
Then for all $t\ge T_*$,
\[
\sum_{|k|\le K}F_k(t)\ge c_*\sum_{|k|\le K}E_k(t).
\]
Using \eqref{eq:sumdecomp}, we obtain
\[
\|\rho(t)\|_{\dot H^{-1}}^2
\ge c_*\sum_{|k|\le K}E_k(t)
= c_*\Bigl(\|\rho(t)\|_{L^2}^2-\sum_{|k|>K}E_k(t)\Bigr).
\]
Divide by $\|\rho(t)\|_{L^2}^2$:
\[
\frac{\|\rho(t)\|_{\dot H^{-1}}^2}{\|\rho(t)\|_{L^2}^2}
\ge c_*\Biggl(1-\frac{\sum_{|k|>K}E_k(t)}{\|\rho(t)\|_{L^2}^2}\Biggr).
\]
Now let $t\to\infty$. Claim 2 shows that the parenthetical factor tends to $1$. Therefore
\[
\liminf_{t\to\infty}\frac{\|\rho(t)\|_{\dot H^{-1}}^2}{\|\rho(t)\|_{L^2}^2}\ge c_*>0.
\]
Taking square roots yields
\[
\liminf_{t\to\infty}\frac{\|\rho(t)\|_{\dot H^{-1}}}{\|\rho(t)\|_{L^2}}>0.
\]
This proves the theorem.

## Key Ideas
The proof is modewise in the conserved $x$-Fourier variable. For each fixed $k$, one splits the $y$-frequencies into a low block $|\ell|\le N$ and a high block $|\ell|\ge N+1$. The high block dissipates faster by an amount $2N+1$, while the shear can transfer energy from low to high only through a term bounded by $|k|\,\|U\|_{L^\infty_tL^2_y}\sqrt{2N+1}\sqrt{LH}$. For $N$ large, the hypersurface “high energy = low energy” is pointing inward, so once the low block has at least half of the mode energy, that property is preserved forever. If the high block had more than half of the energy for all large times, then that mode would decay faster than the known exponential lower bound for nonzero solutions, which is impossible. Hence every nonzero $x$-mode eventually keeps at least half of its energy in finitely many $y$-frequencies, and that immediately gives a positive modewise $\dot H^{-1}/L^2$ lower bound. Finally, only finitely many $x$-modes can matter asymptotically, because the $k^2$ term forces large $|k|$ modes to decay faster than the full solution’s exponential lower bound.






\end{document}