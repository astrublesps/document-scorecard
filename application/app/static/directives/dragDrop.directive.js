angular.module("myApp").directive('dragDrop',function(){
    return function($scope, element){
      $scope.droparea = element[0];
      $scope.dropText = 'Drop file here...'

      // init event handlers
      function dragEnterLeave(evt) {
        evt.stopPropagation()
        evt.preventDefault()
        $scope.$apply(function(){
            $scope.dropText = 'Drop file here...';
            $scope.dropClass = ''
        })
      }
      $scope.droparea.addEventListener("dragenter", dragEnterLeave, false);
      $scope.droparea.addEventListener("dragleave", dragEnterLeave, false);
      $scope.droparea.addEventListener("dragover", function(evt) {
        evt.stopPropagation();
        evt.preventDefault();
        var clazz = 'not-available';
        var ok = evt.dataTransfer && evt.dataTransfer.types && evt.dataTransfer.types.indexOf('Files') >= 0;
        $scope.$apply(function(){
            $scope.dropText = ok ? 'Drop file here...' : 'Only files are allowed!';
            $scope.dropClass = ok ? 'over' : 'not-available'
        })
      }, false)
      $scope.droparea.addEventListener("drop", function(evt) {
        console.log('drop evt:', JSON.parse(JSON.stringify(evt.dataTransfer)));
        evt.stopPropagation()
        evt.preventDefault()
        $scope.$apply(function(){
            $scope.dropText = 'Drop file here...';
            $scope.dropClass = ''
        })
        var files = evt.dataTransfer.files;
        if (files.length > 0) {
            $scope.$apply(function(){
                $scope.files = []
                for (var i = 0; i < files.length; i++) {
                    $scope.files.push(files[i])
                }
            })
        }
      }, false)
    };
    //============== DRAG & DROP =============
      $scope.setFiles = function(element) {
      $scope.$apply(function($scope) {
        console.log('files:', element.files)
        //There will only be one file at a time
          $scope.files = []
          $scope.files.push(element.files[0])
        });
      };
});
