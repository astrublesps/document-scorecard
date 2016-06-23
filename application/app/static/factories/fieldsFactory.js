angular.module("myApp").factory('espsFactory', ['$rootScope', '$http', function ($rootScope, $http) {
    var espsFactory = [];
    var headerInfo = {
        transformRequest: angular.identity,
        header: {
            'Content-Type': "application/json",
            'Accept': 'text/html.application/xhtml+xml,application/xml;q=0.9,image/wep,*/*;q=0.8'
        }
    };

    return {
        getEspList: function (espData) {
            return $http.post("get_esps", espData, headerInfo)
        },
        getEspList2: function (espData) {
            return $http.post("get_esps2", espData, headerInfo)
        },
        addEsp: function (espData) {
            return $http.post("add_esp", espData, headerInfo)
        },
        removeEsp: function (espData) {
            return $http.post("remove_esp", espData, headerInfo)
        },
        editEsp: function (espData) {
            console.log(espData);
            return $http.post("edit_esp", espData, headerInfo)
        }
    };

    return espsFactory;
}]);
