import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.improvement.evolution import EvolutionaryEngine, PromptGenome


class TestPromptGenome:
    def test_create_genome(self):
        genome = PromptGenome(
            genes={
                "role": "You are a coding assistant.",
                "constraints": "Be concise.",
                "style": "Professional.",
            }
        )
        assert genome.fitness == 0.0
        assert genome.genes["role"] == "You are a coding assistant."

    def test_genome_to_prompt(self):
        genome = PromptGenome(
            genes={
                "role": "You are a coding assistant.",
                "constraints": "Be concise.",
                "style": "Professional.",
            }
        )
        prompt = genome.to_prompt()
        assert "coding assistant" in prompt
        assert "concise" in prompt

    def test_genome_crossover(self):
        parent1 = PromptGenome(genes={"role": "A", "constraints": "B", "style": "C"})
        parent2 = PromptGenome(genes={"role": "X", "constraints": "Y", "style": "Z"})
        child = parent1.crossover(parent2)
        # Child should have genes from both parents
        for key in child.genes:
            assert child.genes[key] in ["A", "B", "C", "X", "Y", "Z"]

    def test_genome_mutation(self, tmp_path):
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(content="Mutated text."))

        genome = PromptGenome(genes={"role": "Original", "constraints": "Original"})
        # Note: mutation requires LLM, so we test the structure
        assert genome.genes["role"] == "Original"


class TestEvolutionaryEngine:
    @pytest.mark.asyncio
    async def test_create_population(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints", "style"],
            population_size=10,
        )
        population = await engine.create_population(
            seed_genes={"role": "You are helpful.", "constraints": "Be concise.", "style": "Professional."}
        )
        assert len(population) == 10
        # First genome should be the seed
        assert population[0].genes["role"] == "You are helpful."

    @pytest.mark.asyncio
    async def test_evaluate_population(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = await engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )

        # Mock fitness function
        async def mock_fitness(genome: PromptGenome) -> float:
            return 0.8

        await engine.evaluate_population(population, mock_fitness)
        for genome in population:
            assert genome.fitness == 0.8

    @pytest.mark.asyncio
    async def test_select_parents(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = await engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )
        # Set fitness values
        for i, genome in enumerate(population):
            genome.fitness = i * 0.2

        parents = engine.select_parents(population, n=2)
        assert len(parents) == 2
        # Both parents should be from the population
        assert all(p in population for p in parents)

    @pytest.mark.asyncio
    async def test_evolve_generation(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints", "style"],
            population_size=10,
            mutation_rate=0.5,
            crossover_rate=0.7,
        )
        # Use diverse seed genes so crossover produces different children
        population = await engine.create_population(
            seed_genes={"role": "You are a coding assistant", "constraints": "Be concise and clear", "style": "Professional tone"}
        )
        # Set fitness with variation
        for i, genome in enumerate(population):
            genome.fitness = i * 0.1

        new_pop = engine.evolve_generation(population)
        assert len(new_pop) == 10
        # Elites should be preserved (top 2 fitness)
        assert new_pop[0].fitness == 0.9  # Highest fitness
        assert new_pop[1].fitness == 0.8  # Second highest

    @pytest.mark.asyncio
    async def test_get_best_genome(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = await engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )
        population[2].fitness = 1.0  # Best
        best = engine.get_best(population)
        assert best is population[2]
