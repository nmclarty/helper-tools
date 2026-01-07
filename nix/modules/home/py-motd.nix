{ lib, inputs, config, osConfig, pkgs, perSystem, ... }:
with lib;
let
  cfg = config.programs.py-motd;
in
{
  options.programs.py-motd = {
    enable = mkEnableOption "Enable Python Message of the Day";
    settings = {
      modules = mkOption {
        type = types.listOf types.str;
        default = [ "update" "backup" ];
        description = "Which modules to enable (run), and the order that they are displayed in.";
      };
      update = {
        source_path = mkOption {
          type = types.str;
          default = "${inputs.self}";
          description = "Path to the Nix flake for the system. Used to retrieve flake.lock information.";
        };
        inputs = mkOption {
          type = types.listOf types.str;
          default = [ "nixpkgs" ];
          description = "List of flake inputs to include in the MOTD.";
        };
      };
      backup = {
        status_file = mkOption {
          type = types.str;
          default = "/var/lib/resticprofile/status.json";
          description = "Path to the resticprofile status file.";
        };
      };
    };
  };
  config = mkIf cfg.enable {
    home.packages = [ perSystem.nix-helpers.default ];
    xdg.configFile."py_motd/config.yaml".source = (pkgs.formats.yaml { }).generate "config.yaml" cfg.settings;
  };
}
