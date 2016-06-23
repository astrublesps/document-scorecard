angular.module("myApp").factory('groupsFactory', ['$http', function ($http) {

    return {
        getGroupList: function () {
            return $http.get("get_groups")
        },
        createGroup: function (scenarioData) {
            return $http.post("create_group", scenarioData)
        },
        deleteGroup: function (scenarioData) {
            return $http.post("delete_group", scenarioData)
        },
        copyGroup: function (scenarioData) {
            return $http.post("copy_group", scenarioData)
        },
        editGroup: function (scenarioData) {
            return $http.post("edit_group", scenarioData)
        }
    };
}]);
