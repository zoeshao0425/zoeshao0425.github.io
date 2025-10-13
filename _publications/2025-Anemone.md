---
title: "Rethinking Probabilistic Circuit Parameter Learning"
collection: publications
category: manuscripts
permalink: /publication/2025-Anemone
date: 2025-10-03
paperurl: 'http://zoeshao0425.github.io/files/Anemone.pdf'
citation: 'Anji Liu, Zilei Shao, Guy Van den Broeck. Rethinking Probabilistic Circuit Parameter Learning, 2025.'
---
You may access the entire paper [here](https://arxiv.org/abs/2505.19982).

Probabilistic Circuits (PCs) offer a computationally scalable framework for generative modeling, supporting exact and efficient inference of a wide range of probabilistic queries. While recent advances have significantly improved the expressiveness and scalability of PCs, effectively training their parameters remains a challenge. In particular, a widely used optimization method, full-batch Expectation-Maximization (EM), requires processing the entire dataset before performing a single update, making it ineffective for large datasets. Although empirical extensions to the mini-batch setting, as well as gradient-based mini-batch algorithms, converge faster than full-batch EM, they generally underperform in terms of final likelihood. We investigate this gap by establishing a novel theoretical connection between these practical algorithms and the general EM objective. Our analysis reveals a fundamental issue that existing mini-batch EM and gradient-based methods fail to properly regularize distribution changes, causing each update to effectively ``overfit'' the current mini-batch. Motivated by this insight, we introduce anemone, a new mini-batch EM algorithm for PCs. Anemone applies an implicit adaptive learning rate to each parameter, scaled by how much it contributes to the likelihood of the current batch. Across extensive experiments on language, image, and DNA datasets, anemone consistently outperforms existing optimizers in both convergence speed and final performance.