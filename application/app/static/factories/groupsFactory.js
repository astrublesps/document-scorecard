angular.module("myApp").factory('groupsFactory', ['$http', function ($http) {

    return {
        getGroupList: function () {
            return $http.get("get_groups")
        },
        addGroup: function (scenarioData) {
            return $http.post("add_group", scenarioData)
        },
        removeGroup: function (scenarioData) {
            return $http.post("remove_group", scenarioData)
        },
        copyGroup: function (scenarioData) {
            return $http.post("copy_group", scenarioData)
        },
        editGroup: function (scenarioData) {
            return $http.post("edit_group", scenarioData)
        }
    };
}]);
