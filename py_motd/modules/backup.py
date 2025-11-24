import json
import datetime

class Backup:
    def __init__(self, module_config: dict[str, str]):
        self.status_path = module_config["status_path"]
        self.profiles = module_config["profiles"]

    def get(self):
        output = []
        statuses = map(self.__get_status, self.profiles)
        status_labels = ["Failure", "Success"]

        for status in statuses:
            time_ago = str(self.__diff(status["time"]))[:-7]
            success = status_labels[status["success"]]
            output.append({status["profile"]: (f'({success}) {time_ago} ago')})

        return output
    
    def __get_status(self, profile):
        try:
            with open(f'{self.status_path}/{profile}.status', "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            print("  (N/A) Backup status not found")
            exit()
        status = data["profiles"][profile]["backup"]
        status["profile"] = profile
        return status
    
    def __diff(self, time):
        now = datetime.datetime.now()
        then = datetime.datetime.fromisoformat(time).replace(tzinfo=None)
        return now - then
    