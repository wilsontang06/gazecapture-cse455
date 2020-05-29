"use strict";
(function() {

  window.addEventListener("load", init);

  function init() {
    turnCamOn();
    $("getPosButton").addEventListener("click", processImage);
    $("camButton").addEventListener("click", toggleCamera);
  }

  function processImage() {
    alert("say cheese!");
    // insert fetch call to backend
  }

  function toggleCamera() {
    if ($("camButton").classList.contains("camButtonOn")) {
      turnCamOn();
      $("camButton").innerText = "Turn Webcam Off";
    } else {
      $("webcam").srcObject.getTracks()[0].stop();
      $("camButton").innerText = "Turn Webcam On";
    }
    $("camButton").classList.toggle("camButtonOn");
  }

  function turnCamOn() {
    let video = $("webcam");

    if (navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
          video.srcObject = stream;
          localStream = stream;
          video.play();
        });
    }
  }

  function $(id) {
    return document.getElementById(id);
  }

})();