\subsection{Problem 3: Exponential mixing shear flows}
This is a problem coming from \cite{huang2025exponential}. 

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