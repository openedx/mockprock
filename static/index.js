console.log('hello from MockProck!');

class MockProctoringEventHandler {
  onStartExam() {
    return new Promise(function(resolve, reject) {
      console.log("MockProctoringEventHandler - onStartExam() called");
      setTimeout(resolve, 1000);
    });
  }
  onEndExam() {
    return new Promise((resolve, reject) => {
      console.log("MockProctoringEventHandler - onEndExam() called");
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
