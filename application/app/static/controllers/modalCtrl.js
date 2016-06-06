//This controller is used for scenario and esp modals so variable 'scenario' will pass the esp to manipulate as well
angular.module('myApp').controller('modalCtrl', ['$scope', '$modalInstance', '$state', 'scenario', 'action', 'schemas',
    function ($scope, $modalInstance, $state, scenario, action, schemas) {
        $scope.newScenario = angular.copy(scenario);
        $scope.scenario = scenario;
        $scope.schemas = schemas;
        //holds the options for the drop down menus
        $scope.docTypeOptions = ['810', '846', '850', '855', '856'];
        $scope.fulfillmentTypeOptions = ['Bulk Import', 'Drop Ship', 'Multi Store', 'Cross Dock', 'Multiple'];

        console.log(schemas);

        $scope.closeModal = function () {
            $modalInstance.close({scenario: $scope.newScenario, file: $scope.files, action: action});
        };

        $scope.cancelModal = function () {
            $modalInstance.dismiss();
        };

    }
]);
