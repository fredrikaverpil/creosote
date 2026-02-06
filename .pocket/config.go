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
			pk.WithNameSuffix("3.9"),
			pk.WithFlag(python.Format, "python", "3.9"),
			pk.WithFlag(python.Lint, "python", "3.9"),
			pk.WithFlag(python.Typecheck, "python", "3.9"),
			pk.WithFlag(python.Test, "python", "3.9"),
			pk.WithFlag(python.Test, "coverage", true),
			pk.WithDetect(python.Detect()),
		),

		// Test against remaining supported Python versions
		pk.WithOptions(
			pk.Parallel(
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.10"), pk.WithFlag(python.Test, "python", "3.10")),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.11"), pk.WithFlag(python.Test, "python", "3.11")),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.12"), pk.WithFlag(python.Test, "python", "3.12")),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.13"), pk.WithFlag(python.Test, "python", "3.13")),
			),
			pk.WithDetect(python.Detect()),
		),

		pk.Parallel(
			// Just run Creosote.
			Creosote,

			// Check so .pre-commit-config.yaml was bumped
			PreCommitCheck,

			// GitHub workflows, including matrix-based task execution
			pk.WithOptions(
				github.Tasks(),
				pk.WithFlag(github.Workflows, "skip-pocket", true),
				pk.WithFlag(github.Workflows, "include-pocket-matrix", true),
				pk.WithContextValue(github.MatrixConfigKey{}, github.MatrixConfig{
					DefaultPlatforms: []string{"ubuntu-latest"},
					TaskOverrides: map[string]github.TaskOverride{
						"py-test:3.9":  {Platforms: []string{"ubuntu-latest", "macos-latest", "windows-latest"}},
						"py-test:3.10": {Platforms: []string{"ubuntu-latest", "macos-latest", "windows-latest"}},
						"py-test:3.11": {Platforms: []string{"ubuntu-latest", "macos-latest", "windows-latest"}},
						"py-test:3.12": {Platforms: []string{"ubuntu-latest", "macos-latest", "windows-latest"}},
						"py-test:3.13": {Platforms: []string{"ubuntu-latest", "macos-latest", "windows-latest"}},
					},
				}),
			),
		),
	),

	// Plan configuration.
	Plan: &pk.PlanConfig{
		Shims: pk.AllShimsConfig(),
	},
}

// Creosote runs creosote on itself to verify no unused dependencies.
var Creosote = &pk.Task{
	Name:  "creosote",
	Usage: "run creosote self-check",
	Body: pk.Serial(
		uv.Install,
		pk.Do(func(ctx context.Context) error {
			return pk.Exec(ctx, "uv", "run", "creosote", "--venv", ".venv", "--exclude-dep", "tomli")
		}),
	),
}

// PreCommitCheck validates that .pre-commit-config.yaml uses "rev: v" format.
var PreCommitCheck = &pk.Task{
	Name:  "pre-commit-check",
	Usage: "check pre-commit rev format has v prefix",
	Do: func(ctx context.Context) error {
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
	},
}
