angular.module("myApp").controller("testCtrl",  testCtrl);

    testCtrl.$inject = ["$scope", "scenariosFactory", "feedbackService", "$uibModal"];
    function testCtrl($scope, scenariosFactory, feedbackService, $uibModal) {
        //initiate local variables for tableCtrl
        $scope.scenarios = [];
        $scope.selectedScenario = [];
        $scope.scenariosTestList = [];
        $scope.scenarioFilter = {filter: ''};
        $scope.fileUploaded = false;
        $scope.reverse = true;
        $scope.fd = new FormData();

        console.log($scope.scenariosTestList);
        console.log($scope.fileUploaded);

        //hide buttons and columns for this view
        $scope.hideRemove = true;
        $scope.hideCopy = true;
        $scope.hideEdit = true;
        $scope.hideAddESP = true;
        $scope.hideRightSearch = true;
        $scope.hideCreate = true;
        $scope.hideESPS = true;
        $scope.hideCheckBox = true;

        //Initially loads the table of scenarios
        scenariosFactory.getScenarioList().success(function (data) {
            $scope.scenarios = data;
        });

        $scope.openModal = function() {
            var modalInstance = $uibModal.open({
                templateUrl: "views/modals/fileuploadModal.tpl.html?bust=" + Math.random().toString(36).slice(2),
                controller: 'modalCtrl',
                resolve: {
                    scenario: function() {
                        return '';
                    }, action: function() {
                        return '';
                    }
                }
            })
            .result.then(function(result) { //this happens when the modal is closed, not dismissed
                angular.forEach(result.file,function(file){
                $scope.fd.append('file',file);
                $scope.fileUploaded = true;
                });
            });
        }

        $scope.compareAndDownload = function () {
            //add list of scenarios in the testList for the db call
            console.log($scope.scenariosTestList);
            var jsonData = (JSON.stringify({
                testList: $scope.testList
            }));
            $scope.fd.append("data", jsonData);

            scenariosFactory.compareAndDownload($scope.fd).success(function (data) {
                console.log(data);
                var blob = new Blob([data], {type: "attachment;charset=utf-8"});
                var fileDownload = angular.element('<a></a>');
                var fileName = data.fileName;
                fileDownload.attr('href', window.URL.createObjectURL(blob));
                fileDownload.attr('download', $scope.selectedScenario.name + '-esp_list.txt');
                fileDownload[0].click();
                console.log(data);
            });
        };

        $scope.downloadScenario = function(scenario) {
            var scenarioName = (JSON.stringify({
                name: scenario.name
            }));
            scenariosFactory.downloadScenario(scenarioName).success(function (data) {
                var blob = new Blob([data], {type: "attachment;charset=utf-8"});
                var fileDownload = angular.element('<a></a>');
                var fileName = data.fileName;
                fileDownload.attr('href', window.URL.createObjectURL(blob));
                fileDownload.attr('download', scenario.name + '-esp_list.txt');
                fileDownload[0].click();
            });
        };

        //sets column filters for the scenario table
        $scope.checkSort = function(column) {
            if (column == $scope.sortColumn) {
                $scope.reverse = !$scope.reverse;
            } else if (column != $scope.sortColumn) {
                $scope.sortColumn = column;
                $scope.reverse = true;
            }
        }

        //track selected scenario row and get list of ESPs to build esp table from
        $scope.setSelectedScenario = function(scen) {
            if ($scope.selectedScenario.name != scen.name) {
                $scope.selectedScenario.isChecked = false; //remove old checkbox
                $scope.selectedScenario = scen;
                $scope.selectedScenario.isChecked = true; //add new checkbox
            } else {//row is unselected so empty selectedScenario and remove checkbox check
                $scope.selectedScenario = [];
                scen.isChecked = false;
            };
        };

        $scope.addToList = function (scenario) {
            console.log(scenario);
            //make sure a scenario is selected
            if (scenario != null) {
                //check if the selected scenario is already in the test list, if not add to it. If it is then ignore
                if (!$scope.scenariosTestList.some(function (e) {
                        return e.name == scenario.name
                    })) {
                    //add the selected scenario to the scenario test list, automatically updates the table
                    $scope.scenariosTestList.push(scenario);
                }
                var stringList = '';
                $scope.testList = '';
                $scope.scenariosTestList.some(function (entry, i) {
                    if (stringList == '') {//prevent a leading comma
                        stringList = entry.name;
                    } else {//already a value in stringList
                        stringList = stringList + "," + entry.name;
                    }
                });
                $scope.testList = stringList;
            }
        };

        //removed the selected scenario in the test list by finding its position in the array and splicing it out
        $scope.removedFromList = function (scenario) {
            var position = -1;
            //find position of selected scenario in the array, if present
            $scope.scenariosTestList.some(function (entry, i) {
                if (entry.name == scenario.name) {
                    position = i;
                }
            });
            //if selected scenario is present in array, remove it
            if (position != -1) {
                $scope.scenariosTestList.splice(position, 1);
            }
        };
};
