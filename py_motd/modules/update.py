from json import load, loads
from datetime import datetime, timezone, timedelta
from subprocess import run
from sys import argv

class Update:
    def __init__(self, module_config: dict):
        self.source_path = module_config["source_path"]
        self.inputs = module_config["inputs"]

        # load the flake lock file
        with open(f"{self.source_path}/flake.lock", "r") as file:
            self.flake_lock = load(file)

        with open(f"{self.source_path}/comin.json", "r") as file:
            self.status = self.__parse_status(load(file))

        # try:
        #     # load the status info in json from comin, and the parse it
        #     self.status = self.__parse_status(
        #         loads(run(["comin", "status", "--json"],
        #                 capture_output=True, text=True, check=True).stdout))
        # except TypeError:
        #     print("Updates:")
        #     print("  (N/A) Update status not available")
        #     exit()

        # except FileNotFoundError:
        #     print("Updates:")
        #     print("  (N/A) Comin binary not found")
        #     exit()

    def get(self):
        output = {}
        # don't show extra info if there is none
        extra_info = f' [{self.status["extra"]}]' if self.status["extra"] else ""
    
        output["Status"] = f'({self.status["status"]}) {self.status["ago"]}{extra_info}'
        output["Commit"] = f'({self.status["sha"][:7]}) "{self.status["msg"]}"'
        output["Inputs"] = []
        for i in map(self.__calculate_diff, self.inputs):
            output["Inputs"].append({ i[0]: f'{str(i[1])[:-7]} ago'})

        return output
    

    def __calculate_diff(self, input: str) -> list[str | timedelta]:
        """Calculates the time difference between now and the last modified time of
        a nix flake input (i.e. nixpkgs).

        :param input: The nix flake input name to check
        :return: A list containing the input name and the time difference
        """
        then = datetime.fromtimestamp(
            self.flake_lock["nodes"][input]["locked"]["lastModified"])
        return [input, datetime.now() - then]


    def __parse_status(self, status: dict[str, dict]) -> dict[str, str]:
        """Extracts and transforms a dictionary containing the status received from
        Comin that will be formatted and displayed to the user.

        :param status: The parsed json status from Comin
        :return: The status fields to be formatted and displayed to the user
        """
        deployment = status["deployer"]["deployment"]
        generation = deployment["generation"]
        builder = status["builder"]["generation"]

        last_deployment = (
            datetime.now(tz=timezone.utc) -
            datetime.fromisoformat(deployment["ended_at"])
        )

        extra_info = [
            "Build failed" if builder["build_status"] == "failed" else "",
            "Testing" if generation["selected_branch_is_testing"] else "",
            "Reboot Required" if status["need_to_reboot"] else "",
            "Suspended" if status["is_suspended"] else "",
        ]

        return {
        "status": deployment["status"],
        "ago": str(last_deployment)[:-7] + " ago",
        "extra": ", ".join([i for i in extra_info if i != ""]),
        "msg": generation["selected_commit_msg"].rstrip(),
        "sha": generation["selected_commit_id"],
        }
