angular.module("myApp").factory('scenariosFactory', ['$http', function ($http) {
    var scenariosFactory = [];

    return {
        getScenarioList: function () {
            return $http.get("get_scenarios")
        },
        createScenario: function (scenarioData) {
            return $http.post("create_scenario", scenarioData)
        },
        createScenarioFromFile: function (scenarioData) {
            return $http.post("upload_new_scenario", scenarioData,{ headers: {
                    'Content-Type': undefined}})
        },
        deleteScenario: function (scenarioData) {
            return $http.post("delete_scenario", scenarioData)
        },
        copyScenario: function (scenarioData) {
            return $http.post("copy_scenario", scenarioData)
        },
        editScenario: function (scenarioData) {
            return $http.post("edit_scenario", scenarioData)
        },
        downloadScenario: function (scenarioData) {
            return $http.post("download_esp_list", scenarioData)
        },
        compareAndDownload: function (scenarioData) {
            return $http.post("compare_download", scenarioData,{ headers: {
                    'Content-Type': undefined}})
        }
    };
}]);
