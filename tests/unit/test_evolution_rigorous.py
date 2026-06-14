"""Rigorous tests for EvolutionaryEngine."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.improvement.evolution import EvolutionaryEngine, PromptGenome


class TestPromptGenomeRigorous:
    """Rigorous tests for PromptGenome."""

    def test_genome_with_many_genes(self):
        """Test genome with many genes."""
        genes = {f"gene_{i}": f"value_{i}" for i in range(20)}
        genome = PromptGenome(genes=genes)
        prompt = genome.to_prompt()
        for i in range(20):
            assert f"value_{i}" in prompt

    def test_genome_with_empty_genes(self):
        """Test genome with empty gene values."""
        genome = PromptGenome(genes={"role": "", "constraints": ""})
        prompt = genome.to_prompt()
        assert prompt == "\n\n"

    def test_genome_with_multiline_genes(self):
        """Test genome with multiline gene values."""
        genome = PromptGenome(genes={
            "role": "You are a\ncoding assistant.",
            "constraints": "Be concise.\nBe accurate.\nBe helpful.",
        })
        prompt = genome.to_prompt()
        assert "\n" in prompt
        assert "coding assistant" in prompt

    def test_crossover_preserves_all_genes(self):
        """Test that crossover preserves all gene keys."""
        parent1 = PromptGenome(genes={"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"})
        parent2 = PromptGenome(genes={"a": "X", "b": "Y", "c": "Z", "d": "W", "e": "V"})

        # Do multiple crossovers to test randomness
        children = [parent1.crossover(parent2) for _ in range(100)]

        for child in children:
            assert set(child.genes.keys()) == {"a", "b", "c", "d", "e"}

    def test_crossover_randomness(self):
        """Test that crossover produces different children."""
        parent1 = PromptGenome(genes={"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"})
        parent2 = PromptGenome(genes={"a": "X", "b": "Y", "c": "Z", "d": "W", "e": "V"})

        children = [parent1.crossover(parent2) for _ in range(50)]

        # At least some children should differ from parent1
        differs_from_parent1 = False
        for child in children:
            for key in child.genes:
                if child.genes[key] != parent1.genes[key]:
                    differs_from_parent1 = True
                    break
        assert differs_from_parent1

    def test_crossover_uniform_distribution(self):
        """Test that crossover is roughly uniform."""
        parent1 = PromptGenome(genes={"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"})
        parent2 = PromptGenome(genes={"a": "X", "b": "Y", "c": "Z", "d": "W", "e": "V"})

        # Count how often each gene comes from parent1
        from_parent1 = {k: 0 for k in parent1.genes}
        trials = 1000

        for _ in range(trials):
            child = parent1.crossover(parent2)
            for key in child.genes:
                if child.genes[key] == parent1.genes[key]:
                    from_parent1[key] += 1

        # Each gene should come from parent1 roughly 50% of the time
        for key, count in from_parent1.items():
            ratio = count / trials
            assert 0.4 < ratio < 0.6, f"Gene {key} came from parent1 {ratio:.2%} of the time"

    @pytest.mark.asyncio
    async def test_mutation_with_mock_llm(self):
        """Test mutation with mocked LLM."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(content="Mutated value"))

        genome = PromptGenome(genes={"role": "Original", "constraints": "Original"})

        # Force mutation by setting rate to 1.0
        await genome.mutate(mock_llm, mutation_rate=1.0)

        assert genome.genes["role"] == "Mutated value"
        assert genome.genes["constraints"] == "Mutated value"

    @pytest.mark.asyncio
    async def test_mutation_with_llm_error(self):
        """Test mutation handles LLM errors gracefully."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(side_effect=Exception("LLM error"))

        genome = PromptGenome(genes={"role": "Original"})

        # Should not raise, just log warning
        await genome.mutate(mock_llm, mutation_rate=1.0)

        # Gene should remain unchanged
        assert genome.genes["role"] == "Original"


class TestEvolutionaryEngineRigorous:
    """Rigorous tests for EvolutionaryEngine."""

    def test_create_population_size(self):
        """Test population size is correct."""
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=50,
        )
        population = engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )
        assert len(population) == 50

    def test_create_population_preserves_seed(self):
        """Test that first genome is the seed."""
        seed = {"role": "You are helpful.", "constraints": "Be concise."}
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=10,
        )
        population = engine.create_population(seed)

        assert population[0].genes == seed

    def test_create_population_diversity(self):
        """Test that population has diversity."""
        seed = {"role": "You are a coding assistant", "constraints": "Be concise and clear"}
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=20,
        )
        population = engine.create_population(seed)

        # At least some genomes should differ from seed
        differs = 0
        for genome in population[1:]:
            for key in genome.genes:
                if genome.genes[key] != seed[key]:
                    differs += 1
                    break
        assert differs > 0

    @pytest.mark.asyncio
    async def test_evaluate_population_with_errors(self):
        """Test evaluation handles errors gracefully."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=5,
        )
        population = engine.create_population({"role": "Test"})

        call_count = 0
        async def failing_fitness(genome):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise Exception("Fitness evaluation failed")
            return 0.5

        await engine.evaluate_population(population, failing_fitness)

        # All genomes should have fitness (errors set to 0.0)
        for genome in population:
            assert genome.fitness >= 0.0

    def test_select_parents_tournament_size(self):
        """Test tournament selection respects tournament size."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=10,
            tournament_size=5,
        )
        population = engine.create_population({"role": "Test"})
        for i, genome in enumerate(population):
            genome.fitness = i * 0.1

        parents = engine.select_parents(population, n=3)
        assert len(parents) == 3

    def test_elitism_preserves_best(self):
        """Test that elitism preserves best genomes."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=10,
            elite_count=3,
        )
        population = engine.create_population({"role": "Test"})
        for i, genome in enumerate(population):
            genome.fitness = i * 0.1

        new_pop = engine.evolve_generation(population)

        # Top 3 should be preserved (use pytest.approx for float comparison)
        assert new_pop[0].fitness == pytest.approx(0.9)
        assert new_pop[1].fitness == pytest.approx(0.8)
        assert new_pop[2].fitness == pytest.approx(0.7)

    def test_evolve_generation_size(self):
        """Test evolved generation has correct size."""
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=15,
        )
        population = engine.create_population({"role": "Test", "constraints": "Test"})
        for i, genome in enumerate(population):
            genome.fitness = i * 0.1

        new_pop = engine.evolve_generation(population)
        assert len(new_pop) == 15

    @pytest.mark.asyncio
    async def test_run_evolution_convergence(self):
        """Test evolution detects convergence."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=10,
        )

        # Fitness function that always returns same value
        async def constant_fitness(genome):
            return 0.5

        result = await engine.run_evolution(
            seed_genes={"role": "Test"},
            fitness_fn=constant_fitness,
            generations=20,
        )

        # Should converge early
        assert result["generations_run"] < 20

    @pytest.mark.asyncio
    async def test_run_evolution_improvement(self):
        """Test evolution improves fitness over generations."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=20,
            mutation_rate=0.0,  # No mutation for deterministic test
        )

        # Fitness function based on gene length (longer = better)
        async def length_fitness(genome):
            return len(genome.genes.get("role", "")) / 100.0

        result = await engine.run_evolution(
            seed_genes={"role": "Short"},
            fitness_fn=length_fitness,
            generations=5,
        )

        # Fitness should improve or stay same
        history = result["history"]
        for i in range(1, len(history)):
            assert history[i]["best_fitness"] >= history[i-1]["best_fitness"]

    @pytest.mark.asyncio
    async def test_run_evolution_with_llm(self):
        """Test evolution with LLM mutations."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(content="Improved text"))

        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=5,
            mutation_rate=1.0,  # Force mutation
        )

        async def simple_fitness(genome):
            return 0.5

        result = await engine.run_evolution(
            seed_genes={"role": "Original"},
            fitness_fn=simple_fitness,
            llm=mock_llm,
            generations=3,
        )

        assert result["generations_run"] == 3
        # LLM should have been called for mutations
        assert mock_llm.call.call_count > 0

    def test_get_best_from_empty_population(self):
        """Test get_best with empty population."""
        engine = EvolutionaryEngine(
            gene_keys=["role"],
            population_size=5,
        )
        with pytest.raises(ValueError):
            engine.get_best([])
