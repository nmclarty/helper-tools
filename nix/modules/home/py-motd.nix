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
    optional
    ;
  cfg = config.programs.py-motd;
  toml = pkgs.formats.toml { };
  updateData = pkgs.writeText "update.json" (
    builtins.toJSON {
      commit = osConfig.system.configurationRevision;
      age = inputs.self.lastModified;
      inputs = map (k: {
        name = k;
        age = inputs.${k}.lastModified;
      }) cfg.update.inputs;
      version = with osConfig.system; if pkgs.stdenv.isDarwin then nixpkgsVersion else nixos.version;
    }
  );
in
{
  options.programs.py-motd = {
    enable = mkEnableOption "Enable Python Message of the Day";
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
    };
    backup = {
      enable = mkOption {
        type = types.bool;
        default = with osConfig; services ? py-backup && services.py-backup.enable;
        description = "Whether to enable the module";
      };
      file = mkOption {
        type = types.str;
        default = "/var/lib/resticprofile/status.json";
        description = "Path to the resticprofile status file.";
      };
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ flake.packages.${pkgs.stdenv.hostPlatform.system}.default ];
    xdg.configFile."py-motd/config.toml".source = toml.generate "py-motd-config.toml" {
      modules =
        (optional cfg.update.enable {
          name = "update";
          file = "${updateData}";
        })
        ++ (optional cfg.backup.enable {
          name = "backup";
          inherit (cfg.backup) file;
        });
    };
  };
}
