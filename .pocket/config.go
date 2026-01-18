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
	// Run all python tasks except Test (skipped everywhere), targeting minimum Python version
	pocket.RunIn(
		python.Tasks(python.WithPythonVersion(minPythonVersion)),
		pocket.Detect(python.Detect()),
		pocket.Skip(python.Test),
	),

	// Run tests across all supported Python versions in parallel
	pocket.RunIn(TestMatrix(pythonVersions), pocket.Detect(python.Detect())),

	// Generate GitHub workflow files
	github.Workflows,
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
