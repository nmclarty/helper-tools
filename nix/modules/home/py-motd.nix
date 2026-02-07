{ flake, ... }:
{
  lib,
  inputs,
  config,
  pkgs,
  osConfig,
  ...
}:
let
  inherit (lib)
    mkEnableOption
    mkOption
    types
    mkIf
    ;
  cfg = config.programs.py-motd;
  yaml = pkgs.formats.yaml { };
  update = {
    commit = osConfig.system.configurationRevision;
    flake = flake.lastModified;
    inputs = builtins.map (k: { ${k} = inputs.${k}.lastModified; }) cfg.settings.update.inputs;
    version = with osConfig.system; if pkgs.stdenv.isDarwin then nixpkgsVersion else nixos.version;
  };
in
{
  options.programs.py-motd = {
    enable = mkEnableOption "Enable Python Message of the Day";
    settings = {
      update = {
        enable = mkOption {
          type = types.bool;
          default = true;
          description = "Whether to enable the module";
        };
        inputs = mkOption {
          type = types.listOf types.str;
          default = [ "nixpkgs" ];
          description = "List of flake inputs to include in the MOTD.";
        };
        data_file = mkOption {
          type = types.str;
          default = "${pkgs.writeText "update.json" (builtins.toJSON update)}";
          description = "Path to the data file containing system version info.";
        };
      };
      backup = {
        enable = mkOption {
          type = types.bool;
          default = true;
          description = "Whether to enable the module";
        };
        status_file = mkOption {
          type = types.str;
          default = "/var/lib/resticprofile/status.json";
          description = "Path to the resticprofile status file.";
        };
      };
    };
  };
  config = mkIf cfg.enable {
    home.packages = [ flake.packages.${pkgs.stdenv.hostPlatform.system}.default ];
    xdg.configFile."py-motd/config.yaml".source = yaml.generate "py-motd-config.yaml" cfg.settings;
  };
}
