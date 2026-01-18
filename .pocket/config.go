package main

import (
	"github.com/fredrikaverpil/pocket"
	"github.com/fredrikaverpil/pocket/tasks/github"
	"github.com/fredrikaverpil/pocket/tasks/python"
)

// Supported Python versions for testing (requires-python = ">=3.9").
var pythonVersions = []string{"3.9", "3.10", "3.11", "3.12", "3.13"}

// minPythonVersion is used for linting/typechecking (target minimum supported version).
const minPythonVersion = "3.9"

// LintTasks returns lint/format/typecheck tasks with minPythonVersion baked in.
// This ensures CI matrix jobs use the correct Python version when run individually.
func LintTasks() pocket.Runnable {
	return pocket.Serial(
		pocket.WithOpts(python.Sync, python.SyncOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Format, python.FormatOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Lint, python.LintOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Typecheck, python.TypecheckOptions{PythonVersion: minPythonVersion}),
	)
}

// TestMatrix creates parallel test runs across multiple Python versions.
func TestMatrix(versions []string) pocket.Runnable {
	tasks := make([]any, len(versions))
	for i, v := range versions {
		tasks[i] = pocket.Clone(python.Test,
			pocket.Named("py-test:"+v),
			pocket.Opts(python.TestOptions{PythonVersion: v}),
		)
	}
	return pocket.Parallel(tasks...)
}

// autoRun defines the execution tree for ./pok (also used for matrix generation).
var autoRun = pocket.Serial(
	// Run lint/format/typecheck targeting minimum Python version
	pocket.RunIn(LintTasks(), pocket.Detect(python.Detect())),

	// Run tests across all supported Python versions in parallel
	pocket.RunIn(TestMatrix(pythonVersions), pocket.Detect(python.Detect())),

	// Generate GitHub workflow files
	pocket.WithOpts(github.Workflows, github.WorkflowsOptions{SkipPocket: true, SkipPocketMatrix: false}),
)

// matrixConfig excludes py-test (handled separately via TestMatrix with version-specific names).
var matrixConfig = github.MatrixConfig{
	DefaultPlatforms: []string{"ubuntu-latest"},
	ExcludeTasks:     []string{"py-test"}, // Skip generic py-test; we use py-test:3.X instead
}

// Config is the pocket configuration for this project.
var Config = pocket.Config{
	AutoRun: autoRun,
	ManualRun: []pocket.Runnable{
		// GitHub Actions matrix generation (used by CI)
		github.MatrixTask(autoRun, matrixConfig),
	},
	Shim: &pocket.ShimConfig{
		Posix:      true,
		Windows:    true,
		PowerShell: true,
	},
}
