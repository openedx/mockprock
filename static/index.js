import { handlerWrapper } from '@edx/edx-proctoring';

const makeRequest = ({url, method}) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url);
    xhr.onload = function() {
      if (this.status >= 200 && this.status < 300) {
        resolve(JSON.parse(xhr.response));
      } else {
        const { status } = this;
        const { statusText } = xhr;
        reject({ status, statusText });
      }
    };
    xhr.onerror = function() {
      const { status } = this;
      const { statusText } = xhr;
      reject({ status, statusText });
    };
    xhr.send();
  });
};

console.log('hello from MockProck!');

class MockProctoringEventHandler {
  constructor({baseUrl = 'http://localhost:11136'}) {
    this.baseUrl = baseUrl;
  }
  onStartExamAttempt() {
    console.log("MockProctoringEventHandler - onStartExamAttempt() called");
    return makeRequest({url: `${this.baseUrl}/desktop/start`, method: 'POST'})
      .then(response => response.status === "running" ? Promise.resolve() : Promise.reject());
  }
  onEndExamAttempt() {
    console.log("MockProctoringEventHandler - onEndExamAttempt() called");
    return makeRequest({url: `${this.baseUrl}/desktop/stop`, method: 'POST'})
      .then(response => response.status === "uploading" ? Promise.resolve() : Promise.reject());
  }
  onPing() {
    console.log("MockProctoringEventHandler - onPing() called");
    return makeRequest({url: `${this.baseUrl}/desktop/ping`, method: 'GET'})
      .then(response => response.status === "running" ? Promise.resolve() : Promise.reject());
  }
}

export default handlerWrapper(MockProctoringEventHandler);
