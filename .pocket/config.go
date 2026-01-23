package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/fredrikaverpil/pocket/pk"
	"github.com/fredrikaverpil/pocket/tasks/github"
	"github.com/fredrikaverpil/pocket/tasks/python"
	"github.com/fredrikaverpil/pocket/tools/uv"
)

// Config is the Pocket configuration for this project.
var Config = &pk.Config{
	Auto: pk.Serial(

		// Format, lint, typecheck, and test with Python 3.9 (minimum supported version)
		pk.WithOptions(
			python.Tasks(),
			python.WithVersion("3.9"),
			python.WithTestCoverage(),
			pk.WithDetect(python.Detect()),
		),

		// Test against remaining supported Python versions
		pk.WithOptions(
			pk.Parallel(
				pk.WithOptions(python.Test, python.WithVersion("3.10")),
				pk.WithOptions(python.Test, python.WithVersion("3.11")),
				pk.WithOptions(python.Test, python.WithVersion("3.12")),
				pk.WithOptions(python.Test, python.WithVersion("3.13")),
			),
			pk.WithDetect(python.Detect()),
		),

		// Just run Creosote.
		Creosote,

		// Check so .pre-commit-config.yaml was bumped
		PreCommitCheck,

		// GitHub workflows, including matrix-based task execution
		pk.WithOptions(
			github.Tasks(),
			pk.WithFlag(github.Workflows, "skip-pocket", true),
			pk.WithFlag(github.Workflows, "include-pocket-matrix", true),
		),
	),

	// Manual tasks - only run when explicitly invoked.
	Manual: []pk.Runnable{
		github.Matrix(matrixConfig), // ./pok gha-matrix
	},

	// Plan configuration.
	Plan: &pk.PlanConfig{
		Shims: pk.AllShimsConfig(),
	},
}

// Creosote runs creosote on itself to verify no unused dependencies.
var Creosote = pk.NewTask(
	"creosote",
	"run creosote self-check",
	nil,
	pk.Serial(
		uv.Install,
		pk.Do(func(ctx context.Context) error {
			return pk.Exec(ctx, "uv", "run", "creosote", "--venv", ".venv", "--exclude-dep", "tomli")
		}),
	),
)

// PreCommitCheck validates that .pre-commit-config.yaml uses "rev: v" format.
var PreCommitCheck = pk.NewTask(
	"pre-commit-check",
	"check pre-commit rev format has v prefix",
	nil,
	pk.Do(func(ctx context.Context) error {
		// Tasks run from .pocket/, so go up to project root
		configPath := filepath.Join("..", ".pre-commit-config.yaml")
		file, err := os.Open(configPath)
		if err != nil {
			return fmt.Errorf("open .pre-commit-config.yaml: %w", err)
		}
		defer file.Close()

		scanner := bufio.NewScanner(file)
		var badLines []string
		lineNum := 0
		for scanner.Scan() {
			lineNum++
			line := scanner.Text()
			if strings.Contains(line, "rev:") && !strings.Contains(line, "rev: v") {
				badLines = append(badLines, fmt.Sprintf("  line %d: %s", lineNum, strings.TrimSpace(line)))
			}
		}
		if err := scanner.Err(); err != nil {
			return fmt.Errorf("read .pre-commit-config.yaml: %w", err)
		}
		if len(badLines) > 0 {
			return fmt.Errorf("found rev: entries without 'v' prefix:\n%s", strings.Join(badLines, "\n"))
		}
		pk.Println(ctx, "All rev: entries have 'v' prefix ✓")
		return nil
	}),
)

// matrixConfig configures GitHub Actions matrix generation.
var matrixConfig = github.MatrixConfig{
	ExcludeTasks: []string{"github-workflows"},
}
