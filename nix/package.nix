{ pkgs, inputs, ... }:
let
  inherit (pkgs) lib;
  inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;

  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ../.; };
  # only rebuild when python sources change, not nix/CI/docs
  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../pyproject.toml
      ../uv.lock
      ../src
    ];
  };

  # lowest interpreter satisfying requires-python
  python = lib.head (
    pyproject-nix.lib.util.filterPythonInterpreters {
      inherit (workspace) requires-python;
      inherit (pkgs) pythonInterpreters;
    }
  );

  overlay = lib.composeManyExtensions [
    pyproject-build-systems.overlays.wheel
    (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
    (_: prev: { helper-tools = prev.helper-tools.overrideAttrs { inherit src; }; })
  ];
  pythonSet =
    (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope
      overlay;
in
(pkgs.callPackages pyproject-nix.build.util { }).mkApplication {
  venv = pythonSet.mkVirtualEnv "helper-tools-env" workspace.deps.default;
  package = pythonSet.helper-tools;
}
