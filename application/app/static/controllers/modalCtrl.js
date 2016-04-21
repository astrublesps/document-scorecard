//This controller is used for scenario and esp modals so variable 'scenario' will pass the esp to manipulate as well
angular.module('myApp').controller('modalCtrl', ['$scope', '$modalInstance', '$state', 'scenario', 'action',
 function ($scope, $modalInstance, $state, scenario, action) {
  $scope.newScenario = angular.copy(scenario);
  $scope.scenario = scenario;
  
 	$scope.closeModal = function() {
    $modalInstance.close({scenario: $scope.newScenario, file: $scope.files, action: action});
 	};

 	$scope.cancelModal = function () {
    $modalInstance.dismiss();
 	};

 }
]);
