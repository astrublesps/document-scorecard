angular.module("myApp").factory('schemasFactory', ['$http', function ($http) {
    var scenariosFactory = [];

    return {
        getSchemaList: function () {
            return $http.get("get_schema_list")
        },
        addSchema: function (schemaData) {
            return $http.post("add_schema", schemaData,{ headers: {
                    'Content-Type': undefined}})
        },
        deleteSchema: function (schemaData) {
            return $http.post("delete_schema", schemaData)
        },
    };
}]);
