\subsection{Problem 1: Analysis of an explicit function}
This problem is a function I had in one paper (\cite{feng2023tumor}) about tumor growth. We did the numerical simulation and the result is pretty clear, but how to prove it is not very obvious and we didn't really spend time on it since it is not so important. I assume this problem is the easiest one since this function is almost explicit.

For $n\geq 0,n\in\mathbb{Z}$, consider the following ODE:
\[
r^2\frac{d^2f}{d r^2}+r\frac{d f}{d r}-(r^2+n^2)f=0.
\]
These ODEs are so-called modified Bessel equations. As a linear second order ODE, the solution of it can be written as 
\[
f=c_1I_n+c_2K_n,
\]
where $c_1$ and $c_2$ are constant, as $r\rightarrow 0$, $I_n$ has no singularity at zero, and $K_n$ has singularity at zero. $I_n$ and $K_n$ are called modified functions.

For $\lambda>0,l\geq 2,l\in\mathbb{Z}$, function $F_{\lambda,l}(R)$ is defined as follows(which is the rescale of $F_4$ in \cite{feng2023tumor}):
\begin{align*}
\begin{split}
F_{\lambda,l}(R)=&\frac{ l}{\sqrt{\lambda}R C_{\lambda}(R)}\left(\frac{C_{1,\lambda}(R)}{C_{l,\lambda}(R)}K_l(R)I_l(\sqrt{\lambda}R)-K_1(R)I_1(\sqrt{\lambda}R)\right)\\
&-\frac{1}{C_{\lambda}(R)}\left(\frac{C_{1,\lambda}(R)}{C_{l,\lambda}(R)}K_l(R)I_l'(\sqrt{\lambda}R)-K_1(R)I_1'(\sqrt{\lambda}R)\right),
\end{split}
\end{align*}
here
\[
C_{j,\lambda}(R)=K_j'(R)I_j(\sqrt{\lambda}R)-\sqrt{\lambda}I_j'(\sqrt{\lambda}R)K_j(R),
\]
and
\[
C_{\lambda}(R)=\sqrt{\lambda}K_0(R)I_1(\sqrt{\lambda}R)+K_1(R)I_0(\sqrt{\lambda}R),
\] 
and
\[
I_j'(x)=\frac{d}{dx}I_j(x),
\qquad
K_j'(x)=\frac{d}{dx}K_j(x).
\]
Here is the Problem $1$.
\begin{problem}

\begin{enumerate}
\item Verify that $F_{\lambda,l}(R)$ is well-defined for $\lambda>0$ and $l\geq 2$ and $R>0$. Which means $C_{\lambda}(R)$ and $C_{l,\lambda}(R)$ not equal to zero for $R>0$. 
    \item If $0<\lambda\leq 1$, $l\geq 2,l\in\mathbb{Z}$, then $F_{\lambda,l}(R)$ is negative and monotonic increasing for $R> 0$. 
    \item If $\lambda>1$, $l\geq 2,l\in\mathbb{Z}$, there exists $R_1>0$, so that $F_{\lambda,l}(R)$ is increasing for $R\in (0,R_1)$, decreasing for $R>R_1$, and $F_{\lambda,l}(R_1)>0$. 
\end{enumerate}

\end{problem}