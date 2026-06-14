"""Evolutionary prompt optimization (EGPA).

Uses genetic algorithms to evolve prompt components:
- Genes: Individual prompt sections (role, constraints, style, etc.)
- Fitness: Measured by prompt tracker scores
- Selection: Tournament selection favoring higher fitness
- Crossover: Uniform crossover between parent genomes
- Mutation: LLM-driven rewriting of individual genes
"""

import logging
import random
from typing import Any, Callable, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PromptGenome:
    """A prompt represented as evolvable genes."""

    genes: dict[str, str]
    fitness: float = 0.0

    def to_prompt(self) -> str:
        """Combine genes into a full prompt."""
        parts = []
        for key, value in self.genes.items():
            parts.append(value)
        return "\n\n".join(parts)

    def crossover(self, other: "PromptGenome") -> "PromptGenome":
        """Create child via uniform crossover."""
        child_genes = {}
        for key in self.genes:
            if random.random() < 0.5:
                child_genes[key] = self.genes[key]
            else:
                child_genes[key] = other.genes[key]
        return PromptGenome(genes=child_genes)

    async def mutate(self, llm: Any, mutation_rate: float = 0.1):
        """Mutate genes using LLM rewriting."""
        for key in self.genes:
            if random.random() < mutation_rate:
                try:
                    response = await llm.call(
                        system="Rewrite the following text to be clearer and more effective. Return ONLY the rewritten text.",
                        messages=[{"role": "user", "content": self.genes[key]}],
                    )
                    self.genes[key] = response.content.strip()
                except Exception as e:
                    logger.warning(f"Mutation failed for {key}: {e}")


class EvolutionaryEngine:
    """Genetic algorithm engine for prompt optimization."""

    def __init__(
        self,
        gene_keys: list[str],
        population_size: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        tournament_size: int = 3,
        elite_count: int = 2,
    ):
        self._gene_keys = gene_keys
        self._pop_size = population_size
        self._mutation_rate = mutation_rate
        self._crossover_rate = crossover_rate
        self._tournament_size = tournament_size
        self._elite_count = elite_count

    async def create_population(self, seed_genes: dict[str, str], llm: Any | None = None) -> list[PromptGenome]:
        """Create initial population from seed genes.

        First genome is the seed, rest are copies with slight variations.
        """
        population = [PromptGenome(genes=dict(seed_genes))]

        # Create variations by paraphrasing or shuffling
        for i in range(self._pop_size - 1):
            new_genes = {}
            for key, value in seed_genes.items():
                words = value.split()
                if llm and len(words) > 3:
                    try:
                        response = await llm.call(
                            system="Paraphrase the following text to maintain its meaning but use different wording. Return ONLY the paraphrased text.",
                            messages=[{"role": "user", "content": value}],
                        )
                        new_genes[key] = response.content.strip()
                    except Exception as e:
                        logger.warning(f"Initial population generation failed for {key}: {e}")
                        new_genes[key] = value
                elif len(words) > 3:
                    # Slight shuffle fallback
                    idx = list(range(len(words)))
                    swap_count = max(1, len(words) // 5)
                    for _ in range(swap_count):
                        a, b = random.sample(range(len(words)), 2)
                        idx[a], idx[b] = idx[b], idx[a]
                    new_genes[key] = " ".join(words[j] for j in idx)
                else:
                    new_genes[key] = value
            population.append(PromptGenome(genes=new_genes))

        return population

    async def evaluate_population(
        self,
        population: list[PromptGenome],
        fitness_fn: Callable[[PromptGenome], Awaitable[float]],
    ):
        """Evaluate fitness for all genomes in population."""
        for genome in population:
            try:
                genome.fitness = await fitness_fn(genome)
            except Exception as e:
                logger.warning(f"Fitness evaluation failed: {e}")
                genome.fitness = 0.0

    def select_parents(
        self,
        population: list[PromptGenome],
        n: int = 2,
    ) -> list[PromptGenome]:
        """Select parents using tournament selection."""
        parents = []
        for _ in range(n):
            tournament = random.sample(population, min(self._tournament_size, len(population)))
            winner = max(tournament, key=lambda g: g.fitness)
            parents.append(winner)
        return parents

    def evolve_generation(
        self,
        population: list[PromptGenome],
    ) -> list[PromptGenome]:
        """Create next generation via selection, crossover, mutation."""
        # Sort by fitness
        population.sort(key=lambda g: g.fitness, reverse=True)

        # Keep elites
        new_population = [PromptGenome(genes=dict(g.genes), fitness=g.fitness)
                          for g in population[:self._elite_count]]

        # Fill rest with crossover + mutation
        while len(new_population) < self._pop_size:
            parents = self.select_parents(population, n=2)

            if random.random() < self._crossover_rate:
                child = parents[0].crossover(parents[1])
            else:
                child = PromptGenome(genes=dict(parents[0].genes))

            # Note: async mutation happens in run_evolution
            new_population.append(child)

        return new_population[:self._pop_size]

    def get_best(self, population: list[PromptGenome]) -> PromptGenome:
        """Get the best genome from population."""
        return max(population, key=lambda g: g.fitness)

    async def run_evolution(
        self,
        seed_genes: dict[str, str],
        fitness_fn: Callable[[PromptGenome], Awaitable[float]],
        llm: Any | None = None,
        generations: int | None = None,
    ) -> dict:
        """Run full evolutionary optimization.

        Returns:
            dict with best_genome, history, final_fitness
        """
        gens = generations or 10
        population = await self.create_population(seed_genes, llm)
        history = []

        for gen in range(gens):
            # Evaluate
            await self.evaluate_population(population, fitness_fn)

            # Track best
            best = self.get_best(population)
            history.append({
                "generation": gen,
                "best_fitness": best.fitness,
                "avg_fitness": sum(g.fitness for g in population) / len(population),
                "best_genes": dict(best.genes),
            })

            logger.info(f"Gen {gen}: best={best.fitness:.3f}, avg={history[-1]['avg_fitness']:.3f}")

            # Check convergence
            if gen > 2 and history[-1]["best_fitness"] == history[-2]["best_fitness"] == history[-3]["best_fitness"]:
                logger.info(f"Converged at generation {gen}")
                break

            # Evolve (except last generation)
            if gen < gens - 1:
                population = self.evolve_generation(population)
                # Apply mutations
                if llm:
                    for genome in population:
                        await genome.mutate(llm, self._mutation_rate)

        best = self.get_best(population)
        return {
            "best_genome": best,
            "best_prompt": best.to_prompt(),
            "best_fitness": best.fitness,
            "generations_run": len(history),
            "history": history,
        }
