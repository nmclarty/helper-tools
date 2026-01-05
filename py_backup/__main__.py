from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from json import loads

from pystemd.systemd1 import Manager
from ruamel.yaml import YAML

def cleanup(ds: str, mt: Path) -> None:
    if mt.is_mount():
        run(["umount", mt], check=True)

    if run(["zfs", "list", ds], capture_output=True).returncode == 0:
        run(["zfs", "destroy", ds], check=True)

def snapshot(ds: str, mt: Path) -> None:
    run(["zfs", "snapshot", ds], check=True)
    run(["mount", "-t", "zfs", ds, mt])

def main() -> None:
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Path to the configuration file", required=True
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    config = yaml.load(Path(args.config))

    # load systemd manager
    manager = Manager(_autoload=True)

    # stop each service for snapshotting
    for service in config["services"]:
        manager.Manager.StopUnit(bytes(str(service), "utf-8"), b'replace')

    # create temporary snapshots for backups
    for dataset in config["datasets"]:
        ds = f"{config["zpool"]}/{dataset}@backup"
        mt = Path(f"{config["dir"]}/{dataset}")

        cleanup(ds, mt)
        snapshot(ds, mt)
        print(f"Created snapshot '{ds}' and mounted in '{mt}'")

    # start each service after snapshotting
    for service in config["services"]:
        manager.Manager.StartUnit(bytes(str(service), "utf-8"), b'replace')

    # # run backups
    # run(
    #     ["resticprofile" "remote.backup"],
    #     capture_output=True,
    #     text=True,
    #     check=True,
    # )

    # clean up temporary snapshots for backups
    for dataset in config["datasets"]:
        cleanup(config["dir"], config["zpool"], dataset)

if __name__ == "__main__":
    main()
