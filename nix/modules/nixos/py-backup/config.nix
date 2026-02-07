{ flake, ... }:
{
  lib,
  config,
  pkgs,
  system,
  ...
}:
let
  inherit (lib) mkIf mkForce;
  cfg = config.services.py-backup;
  yaml = pkgs.formats.yaml { };
in
{
  config = mkIf cfg.enable {
    systemd = {
      tmpfiles.rules = [
        "d ${cfg.settings.zpool.directory}"
        "f ${cfg.restic.statusFile}"
      ];
      services = {
        # otherwise starting sanoid with systemd won't wait for completion
        sanoid.serviceConfig.Type = "oneshot";
        backup = {
          description = "Snapshot disks and backup";
          after = [
            "network-online.target"
            "zfs.target"
          ];
          requires = [
            "network-online.target"
            "zfs.target"
          ];
          path = with pkgs; [
            zfs
            util-linux
            resticprofile
          ];
          environment = {
            PYTHONUNBUFFERED = "1"; # otherwise stdout is delayed
            PY_BACKUP_CONFIG_FILE = "${yaml.generate "py-backup-config.yaml" cfg.settings}";
          };
          serviceConfig = {
            Type = "oneshot";
            ExecStart = "${flake.packages.${system}.default}/bin/py_backup";
          };
        };
      };
      timers = {
        # since we're triggering sanoid manually, disable its timer
        sanoid.enable = mkForce false;
        backup = {
          enable = true;
          wantedBy = [ "timers.target" ];
          timerConfig = {
            OnCalendar = cfg.interval;
            Persistent = true;
          };
        };
      };
    };

    sops = {
      templates."resticprofile/profiles.json" = {
        path = "/etc/resticprofile/profiles.json";
        content =
          let
            settings = {
              version = "1";

              default = {
                inherit (cfg.restic) repository;
                password-file = config.sops.secrets.${cfg.restic.secrets.password}.path;
                env = {
                  AWS_ACCESS_KEY_ID = config.sops.placeholder.${cfg.restic.secrets.accessKey};
                  AWS_SECRET_ACCESS_KEY = config.sops.placeholder.${cfg.restic.secrets.secretKey};
                };
                status-file = "/var/lib/resticprofile/status.json";
                force-inactive-lock = true;
                initialize = true;
                cache-dir = "/var/cache/restic";
                cleanup-cache = true;
                pack-size = 64;
                backup = {
                  tag = "automatic";
                  source = cfg.settings.zpool.datasets;
                  source-base = cfg.settings.zpool.directory;
                  source-relative = true;
                  extended-status = true;
                };
                retention = {
                  after-backup = true;
                  tag = true;
                  prune = true;
                  keep-daily = cfg.restic.retention.days;
                  keep-weekly = cfg.restic.retention.weeks;
                };
              };
            };
          in
          builtins.toJSON settings;
      };
    };
  };
}
