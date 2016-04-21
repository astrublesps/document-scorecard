angular.module("myApp").service('feedbackService', feedbackService);

    feedbackService.$inject = ['FeedbackService', 'FeedbackFactory'];
    function feedbackService(FeedbackService, FeedbackFactory) {

      this.clearAndAdd = function(message, status) {
        // clear messages from a single container
        FeedbackService.clearContainer('myMessages');
        this.addMessage(message, status);
      }

      this.addMessage = function(message, status) {
          var msg = null;
          if (status == '200') {
              msg = FeedbackFactory.success(message, {closeable: true, flash: "10000"});
          } else if (status == '400') {
              msg = FeedbackFactory.warning(message, {closeable: true, flash: "10000"});
          } else if (status == '500') {
              msg = FeedbackFactory.error(message, {closeable: true, flash: "10000"});
          } else {
              msg = FeedbackFactory.error('Something unaccounted for happened, please report error/bug.', {closeable: true});
          }

          FeedbackService.sendMsgToContainer(msg, 'myMessages');
      }
}
