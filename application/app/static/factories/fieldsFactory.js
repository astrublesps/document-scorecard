angular.module("myApp").factory('fieldsFactory', ['$rootScope', '$http', function ($rootScope, $http) {
    var headerInfo = {
        transformRequest: angular.identity,
        header: {
            'Content-Type': "application/json",
            'Accept': 'text/html.application/xhtml+xml,application/xml;q=0.9,image/wep,*/*;q=0.8'
        }
    };

    return {
        getFieldList: function (espData) {
            return $http.post("get_fields", espData, headerInfo)
        },
        getFieldList2: function (espData) {
            return $http.post("get_fields2", espData, headerInfo)
        },
        addField: function (espData) {
            return $http.post("add_field", espData, headerInfo)
        },
        removeField: function (espData) {
            return $http.post("remove_field", espData, headerInfo)
        },
        editField: function (espData) {
            console.log(espData);
            return $http.post("edit_field", espData, headerInfo)
        }
    };

}]);
