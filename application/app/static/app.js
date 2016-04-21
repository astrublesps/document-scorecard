angular.module("myApp", ['webui-core', 'webui-feedback', 'ui.bootstrap', 'ui.router']);

angular.module("myApp").config(config);

    config.$inject = ['$stateProvider', '$urlRouterProvider'];
    function config ($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/scenarios/');
$stateProvider
    .state('scenarios', {
        url:'/scenarios/',
        templateUrl: 'views/app.html',
        controller: 'scenariosCtrl',
        controllerAs: 'scenario'
    })
    .state('index', {
        url:'/',
        templateUrl: 'views/app.html',
        controller: 'testCtrl'
    });
}

//allows Jinja (templates in Flask) and AngularJS to work together by changing tags for Angular to {[ ]}
angular.module("myApp").config(['$interpolateProvider', function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
}]);
//------------------------------------------------------------------------------------------------------------end config
