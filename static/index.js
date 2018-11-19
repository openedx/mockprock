console.log('hello from MockProck!');

class MockProctoringEventHandler {
  onStartExamAttempt() {
    return new Promise(function(resolve, reject) {
      console.log("MockProctoringEventHandler - onStartExamAttempt() called");
      setTimeout(resolve, 1000);
    });
  }
  onEndExamAttempt() {
    return new Promise((resolve, reject) => {
      console.log("MockProctoringEventHandler - onEndExamAttempt() called");
      setTimeout(resolve, 1000);
    });
  }
  onPing() {
    return new Promise((resolve) => {
      console.log("MockProctoringEventHandler - onPing() called");
      setTimeout(resolve, 100);
    });
  }
}

export default MockProctoringEventHandler;
