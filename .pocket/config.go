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

// LintWorkflow runs sync, format, lint, typecheck (no tests) against minimum Python version.
func LintWorkflow() pocket.Runnable {
	return pocket.Serial(
		pocket.WithOpts(python.Sync, python.SyncOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Format, python.FormatOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Lint, python.LintOptions{PythonVersion: minPythonVersion}),
		pocket.WithOpts(python.Typecheck, python.TypecheckOptions{PythonVersion: minPythonVersion}),
	)
}

// Config is the pocket configuration for this project.
var Config = pocket.Config{
	AutoRun: pocket.Serial(
		// Format, lint, typecheck against minimum supported version (no tests)
		pocket.RunIn(LintWorkflow(), pocket.Detect(python.Detect())),

		// Run tests across all supported Python versions in parallel
		pocket.RunIn(TestMatrix(pythonVersions), pocket.Detect(python.Detect())),

		// Generate GitHub workflow files
		github.Workflows,
	),
	Shim: &pocket.ShimConfig{
		Posix:      true,
		Windows:    true,
		PowerShell: true,
	},
}
