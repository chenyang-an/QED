# Analysis Problems (Apr 24, 2026)

There are four problems in this folder. All four problems are open research problems contributed by **Xiaoqian Xu**, Assistant Professor of Mathematics at Duke Kunshan University.

## QED Configuration

- **Prover mode:** Simple (not decomposition)
- **Literature survey:** Codex
- **Prover:** Codex, gpt-5.4
- **Verifiers:** Gemini, gemini-3.1-pro
- **Brainstorm:** Disabled
- **Max iterations:** 9

## Results

| Problem | Result | Round |
|---------|--------|-------|
| P1 | Failed (verifier rejected all 9 rounds) | — |
| P2 | Failed (verifier rejected all 9 rounds) | — |
| P3 | Proved | Round 1 |
| P4 | Proved | Round 3 |

Final proofs of P3 and P4 are human-verified by Professor Xiaoqian Xu.

## Workflow

- Professor Xiaoqian Xu provided four open problems to **Chenyang An**, PhD candidate at the UCSD Mathematics Department.
- Chenyang An has no background knowledge in the problem domain (applied analysis / fluid PDE).
- Chenyang An ran QED on each problem with the configuration above.
- No human intervention occurred at any point — the entire flow was fully automated.
- QED self-rejected its own proofs for P1 and P2 (the verifier found issues in all 9 rounds), and independently solved P3 and P4.
- The proofs for P3 and P4 were sent back to Professor Xiaoqian Xu, who verified their correctness.

## Expert Comments from Professor Xiaoqian Xu

1. These two problems are directly from one very recent research project of mine. I'm doing applied analysis, fluid PDE, or incompressible flow, Navier-Stokes Equations/Euler Equations.

2. The research project is about fluid mixing, or about the energy cascade in the study of turbulence. It was actually raised by Prof. Charlie Doering around 2016. Intuitively speaking, in fluid we know advection could transport energy to high-frequency modes, while the diffusion process will diffuse the energy faster in high-frequency modes than low-frequency modes. Hence, Charlie Doering in his paper in 2018 with Christopher Miles predicts that there should be some mode, which is similar to the Batchelor length scale in turbulence, so that the advection-diffusion process will get stuck on these modes. This question had no concrete progress until last year, when Keefer Rowan provided a counterexample to show that this may not be the case. In my paper with Yupei last year, we showed that it is highly possible that in general Doering's conjecture may not be correct, but generically it should be the case. Doering's Batchelor scale question is interesting also because it is relevant to the $L^2$ estimate of the general parabolic equations. What Yupei and I proved is the result for a particular type of flow, so-called shear flow. For shear flow, we proved that highly possibly, the Batchelor scale should exist. But our result is only a sufficient condition for such things. However, it is still the first result that shows that the Batchelor scale exists for an advection-diffusion process.

3. For P4, to my surprise, it shows that the result by Yupei and me is actually an equivalent condition for shear flow — that the Batchelor Scale exists.

4. This is really impressive because both of us agree that there may need some new tools, not just by our argument, to prove that the Batchelor Scale really exists. So this is the next thing we are planning to do. But AI told us that we don't even need to go deeper into our argument; our result itself is equivalent to the existence of the Batchelor Scale. The proof is relatively straightforward, but it is still nontrivial, and if we don't know the definite answer, we will probably never try it.

5. For P3, it is a relatively easier result. It's still a result about mixing of fluids. But still, it's about a critical case of the transport equation; usually people would expect some harder tools to deal with it, but AI just gives a very straightforward proof, which is not something we expected. Actually, P3 asks if it is possible to find a particular flow that satisfies some properties. What I expected is that such a construction is possible — it seems like some playing around with the Fourier modes with some special functions. However, AI gives me a negative answer.

6. I think both proofs are not hard. However, they are also not trivial, about 3-5 pages long. This is a tricky length; in a field like applied analysis, this is a length for the proofs in most of the acceptable papers, especially in the papers involving physics.

7. I would say that, as most people may agree at this moment, AI is very good at dealing with (relatively) short proofs.

8. Another impressive thing about these proofs is that usually we may think AI can only work for algebraic, combinatorial, or other problems that could be formalized — usually it may need Lean. Few people, especially in the field of analysis or PDE, think that it can really work for analysis problems. These proofs show that AI can really help, even with LLM.

9. In my field, usually knowing the correct answer is very important. Now these proofs show that AI is very good at attempting.

10. It is also worth saying that, in the whole process, I only provided the problem description. Chenyang, who is not an analyst, did all the prompt work, which means that all the prompt words are for general fields. The proofs were not obtained through guidance from experts. To be honest, I myself don't know how to solve the problems at all.

11. On the other hand, these proofs also surprise me because I also gave AI another two problems, which are problems I thought would be easier. P1 is a problem where we have a very complicated function, including several Bessel functions, and from numerical simulation we can see the function has some properties, like decreasing to zero, etc. But manually I don't know how to prove it rigorously. AI has no idea for this problem. For P2, it is a very standard problem for graduate students — it asks AI to read a paper and use the similar method in that paper with a slightly different differential equation. However, AI seems very poor at this. Like in P4, when AI thinks about a problem, it seems that it will not try to really follow the existing papers, even if I mentioned the papers, but tries to find a solution all by itself. And also, the solution of P2, if it exists, should be longer, like 10-20 pages. This also shows that AI seems to be good at shorter proofs.

12. For the level of these two proofs, even though they are quite interesting, due to the length of the proofs, it's better to add a bit more further results to them (maybe find another two similar proofs?), after which it could be a good publishable paper.
