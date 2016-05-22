//This controller is used for scenario and esp modals so variable 'scenario' will pass the esp to manipulate as well
angular.module('myApp').controller('modalCtrl', ['$scope', '$modalInstance', '$state', 'scenario', 'action', 'schemas',
    function ($scope, $modalInstance, $state, scenario, action, schemas) {
        $scope.newScenario = angular.copy(scenario);
        $scope.scenario = scenario;
        console.log(schemas);
        $scope.schemas = schemas;
        console.log(schemas);

        $scope.closeModal = function () {
            $modalInstance.close({scenario: $scope.newScenario, file: $scope.files, action: action});
        };

        $scope.cancelModal = function () {
            $modalInstance.dismiss();
        };

    }
]);
