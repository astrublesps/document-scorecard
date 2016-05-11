angular.module("myApp").controller("scenariosCtrl",  scenariosCtrl);

    scenariosCtrl.$inject = ["$scope", "scenariosFactory", "espsFactory", "schemasFactory", "feedbackService", "$uibModal"];
    function scenariosCtrl($scope, scenariosFactory, espsFactory, schemasFactory, feedbackService, $uibModal) {
        //initiate local variables for tableCtrl
        $scope.scenarios = [];
        $scope.esps = [];
        $scope.selectedScenario = [];
        $scope.scenarioFilter = {filter: ''};
        $scope.espFilter = {filter: ''};
        $scope.reverse = false;

        //hide buttons and columns for this view
        $scope.hideTestButton = true;
        $scope.hideUpload = true;
        $scope.hideAddTest = true;
        $scope.hideTestTable = true;

        //Initially loads the table of scenarios
        scenariosFactory.getScenarioList().success(function (data) {
            $scope.scenarios = data;
        });

        schemasFactory.getSchemaList().success(function (data) {
            $scope.schemas = data;
            console.log($scope.schemas);
        });

        //opens the scenario and ESP modal windows and performs the confirmed action when it closes
        $scope.openModal = function(action, scenario) {
            var template = "";
            if (action == 'delete') {
                template = "views/modals/deleteModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'edit') {
                template = "views/modals/editModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'copy') {
                template = "views/modals/copyModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'create') {
                template = "views/modals/createModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'addESP') {
                template = "views/modals/addESPModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'editESP') {
                template = "views/modals/editESPModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            } else if (action == 'removeESP') {
                template = "views/modals/removeESPModal.tpl.html?bust=" + Math.random().toString(36).slice(2);
            }

            if (template != "") {
                var modalInstance = $uibModal.open({
                    templateUrl: template,
                    controller: 'modalCtrl',
                    resolve: {
                        scenario: function() {
                            return scenario;
                        }, action: function() {
                            return action;
                        }, schemas: function() {
                            return $scope.schemas;
                        }
                    }
                })
                .result.then(function(result) { //this happens when the modal is closed, not dismissed
                    //some values are repetative because that is how the database was originally build..dont want to break it now
                    var jsonData = (JSON.stringify({
                        name: result.scenario.name,
                        description: result.scenario.description,
                        docType: result.scenario.docType,
                        oldName: scenario.name,
                        oldXpath: scenario.xpath,
                        oldData: scenario.data,
                        oldScore: scenario.score,
                        newName: result.scenario.name,
                        newDescription: result.scenario.description,
                        updatedName: result.scenario.name,
                        updatedDescription: result.scenario.description,
                        scenName: $scope.selectedScenario.name,
                        xpath: result.scenario.xpath,
                        score: result.scenario.score,
                        data: result.scenario.data,
                        newXpath: result.scenario.xpath,
                        newScore: result.scenario.score,
                        newData: result.scenario.data
                    }));

                    if (result.action == 'copy') {
                        scenariosFactory.copyScenario(jsonData).success(function (data) {
                            $scope.scenarios = data;
                            feedbackService.clearAndAdd('Scenario successfully copied', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    } else if (result.action == 'edit') {
                        scenariosFactory.editScenario(jsonData).success(function (data) {
                            $scope.scenarios = data;
                            feedbackService.addMessage('Scenario successfully edited', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    } else if (result.action == 'create') {
                        if (result.file == null) {
                            scenariosFactory.createScenario(jsonData).success(function (data) {
                                $scope.scenarios = data;
                                feedbackService.addMessage('A new empty scenario was created', '200');
                            })
                            .error(function(result,status) {
                                feedbackService.addMessage(result, status);
                                console.log('error code: '+status+'-'+result);
                            });
                        } else {
                            var fd = new FormData();
                            angular.forEach(result.file,function(file){
                            fd.append('file',file);
                            });
                            fd.append("data", jsonData);

                            scenariosFactory.createScenarioFromFile(fd).success(function (data) {
                                $scope.scenarios = data;
                                feedbackService.addMessage('New scenario was created from the uploaded file', '200');
                            })
                            .error(function(result,status) {
                                feedbackService.addMessage(result, status);
                                console.log('error code: '+status+'-'+result);
                            });
                        }
                    } else if (result.action == 'delete') {
                        scenariosFactory.deleteScenario(jsonData).success(function (data) {
                            $scope.scenarios = data;
                            // empty esps table so it doesn't still show the deleted scenario
                            $scope.selectedScenario = '';
                            $scope.esps = '';
                            feedbackService.addMessage('Scenario successfully deleted', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    } else if (result.action == 'addESP') {
                        espsFactory.addEsp(jsonData).success(function (data) {
                            $scope.esps = data;
                            feedbackService.addMessage('ESP sucessfully added', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    } else if (result.action == 'editESP') {
                        espsFactory.editEsp(jsonData).success(function (data) {
                            $scope.esps = data;
                            feedbackService.addMessage('ESP successfully edited', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    } else if (result.action == 'removeESP') {
                        espsFactory.removeEsp(jsonData).success(function (data) {
                            $scope.esps = data;
                            feedbackService.addMessage('ESP successfully removed', '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                            console.log('error code: '+status+'-'+result);
                        });
                    }
                });
            }
        }

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
        $scope.setSelectedScenario = function (scen) {
            if ($scope.selectedScenario.name != scen.name) {
                $scope.selectedScenario.isChecked = false; //remove old checkbox
                $scope.selectedScenario = scen;
                $scope.selectedScenario.isChecked = true; //add new checkbox
            } else {//row is unselected so empty selectedScenario and remove checkbox check
                $scope.selectedScenario = [];
                scen.isChecked = false;
            };
            //get esps to populate espsTable
            if ($scope.selectedScenario != null && $scope.selectedScenario.name != null) {
                var jsonData = (JSON.stringify({
                    name: $scope.selectedScenario.name
                }));
                espsFactory.getEspList(jsonData).success(function (data) {
                    $scope.esps = data;
                });
            } else {
                $scope.esps = []; // clears esp table if no scenario is selected
            };
        };

        //schema functionality--------------------------------------------------
        $scope.openSchemaModal = function() {
            template = "views/modals/schemaModal.tpl.html?bust=" + Math.random().toString(36).slice(2);

            if (template != "") {
                var modalInstance = $uibModal.open({
                    templateUrl: template,
                    controller: 'schemaCtrl',
                    resolve: {
                        schemas: function() {
                            return $scope.schemas;
                        }
                    }
                }).result.then(function(result) { //this happens when the modal is closed, not dismissed

                    if (result.action == 'add') {
                        var jsonData_addSchema = (JSON.stringify({
                            schema: result.schema
                        }));

                        if (result.file != null) {
                            var fd = new FormData();
                            angular.forEach(result.file,function(file){
                            fd.append('file',file);
                            });
                            fd.append("data", jsonData_addSchema);

                            schemasFactory.addSchema(fd).success(function (data) {
                                $scope.schemas = data;
                                feedbackService.addMessage('Schema '+result.schema+' was added', '200');
                            })
                            .error(function(result,status) {
                                feedbackService.addMessage(result, status);
                            });
                        } else {//no file uploaded or other unforeseen error
                                feedbackService.addMessage('Unable to add schema', '400');
                        }
                    } else if (result.action == 'delete') {
                        var jsonData_deleteSchema = (JSON.stringify({
                            delete: result.delete
                        }));
                        console.log(result.delete);

                        schemasFactory.deleteSchema(jsonData_deleteSchema).success(function (data) {
                            $scope.schemas = data;
                            feedbackService.addMessage('Schema '+result.delete+" was successfully delete", '200');
                        })
                        .error(function(result,status) {
                            feedbackService.addMessage(result, status);
                        });
                    }
                });
            }
        }
};
