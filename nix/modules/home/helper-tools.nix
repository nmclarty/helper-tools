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
  cfg = config.programs.helper-tools;
  yaml = pkgs.formats.yaml { };
  updateData = pkgs.writeText "update.json" (
    builtins.toJSON {
      inputs = map (k: {
        name = k;
        rev = inputs.${k}.dirtyShortRev or inputs.${k}.shortRev or "";
        modified = inputs.${k}.lastModified or 0;
      }) ([ "self" "nixpkgs" ] ++ cfg.update.inputs);
    }
  );
in
{
  options.programs.helper-tools = {
    enable = mkEnableOption "Enable helper-tools";
    motd = {
      enable = mkEnableOption "Enable motd";
      columns = mkOption {
        type = types.bool;
        default = true;
        description = "Display motd horizontally as columns";
      };
      system = {
        enable = mkOption {
          type = types.bool;
          default = true;
          description = "Whether to enable the module.";
        };
        services = mkOption {
          type = with types; listOf str;
          description = "List of services to monitor in the MOTD.";
        };
      };
      update = {
        enable = mkOption {
          type = types.bool;
          default = true;
          description = "Whether to enable the module.";
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
          description = "Whether to enable the module. Will be enabled automatically with py-backup.";
        };
        file = mkOption {
          type = types.str;
          default = "/var/lib/resticprofile/status.json";
          description = "Path to the resticprofile status file.";
        };
      };
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ flake.packages.${pkgs.stdenv.hostPlatform.system}.default ];
    xdg.configFile."helper-tools/config.yaml".source = yaml.generate "helper-tools-config.yaml" {
      motd = mkIf cfg.motd.enable {
        inherit (cfg.motd) columns;
        modules =
          (optional cfg.motd.system.enable {
            module = "system";
            inherit (cfg.motd.system) services;
          })
          ++ (optional cfg.motd.update.enable {
            module = "update";
            file = "${updateData}";
          })
          ++ (optional cfg.motd.backup.enable {
            module = "backup";
            inherit (cfg.motd.backup) file;
          });
      };
    };
  };
}
