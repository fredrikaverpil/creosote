package main

import (
	"github.com/fredrikaverpil/pocket"
	"github.com/fredrikaverpil/pocket/tasks/github"
	"github.com/fredrikaverpil/pocket/tasks/python"
)

// Config is the pocket configuration for this project.
var Config = pocket.Config{
	AutoRun: pocket.Serial(
		// Python workflow
		pocket.Paths(python.Tasks()).DetectBy(python.Detect()).SkipTask(python.Test),
	),
	ManualRun: []pocket.Runnable{
		github.Workflows,
	},
	Shim: &pocket.ShimConfig{
		Posix:      true,
		Windows:    true,
		PowerShell: true,
	},
}
