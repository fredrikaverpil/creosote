package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/fredrikaverpil/pocket/pk"
	"github.com/fredrikaverpil/pocket/pk/run"
	"github.com/fredrikaverpil/pocket/tasks/github"
	"github.com/fredrikaverpil/pocket/tasks/python"
	"github.com/fredrikaverpil/pocket/tools/uv"
)

// Config is the Pocket configuration for this project.
var Config = &pk.Config{
	Auto: pk.Serial(

		// Format, lint, typecheck, and test with Python 3.10 (minimum supported version)
		pk.WithOptions(
			python.Tasks(),
			pk.WithNameSuffix("3.10"),
			pk.WithFlags(python.FormatFlags{Python: "3.10"}),
			pk.WithFlags(python.LintFlags{Python: "3.10"}),
			pk.WithFlags(python.TypecheckFlags{Python: "3.10"}),
			pk.WithFlags(python.TestFlags{Python: "3.10", Coverage: true}),
			pk.WithDetect(python.Detect()),
		),

		// Test against remaining supported Python versions
		pk.WithOptions(
			pk.Parallel(
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.11"), pk.WithFlags(python.TestFlags{Python: "3.11"})),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.12"), pk.WithFlags(python.TestFlags{Python: "3.12"})),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.13"), pk.WithFlags(python.TestFlags{Python: "3.13"})),
				pk.WithOptions(python.Test, pk.WithNameSuffix("3.14"), pk.WithFlags(python.TestFlags{Python: "3.14"})),
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
				pk.WithFlags(github.WorkflowFlags{
					PerPocketTaskJob: new(true),
					Platforms:        []github.Platform{github.Ubuntu},
					PerPocketTaskJobOptions: map[string]github.PerPocketTaskJobOption{
						"py-test:.*": {Platforms: github.AllPlatforms()},
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
			return run.Exec(ctx, "uv", "run", "--frozen", "creosote", "--venv", ".venv", "--include-deferred")
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
		run.Println(ctx, "All rev: entries have 'v' prefix ✓")
		return nil
	},
}
